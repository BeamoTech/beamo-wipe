"""A launcher receipt must describe the bytes present when the build completes."""

from pathlib import Path

import pytest

from test_desktop_output_replacement_pass2_20261019 import (
    _setup,
    builder as existing_builder_fixture,
)


@pytest.fixture
def builder():
    return existing_builder_fixture.__wrapped__()


class ManifestStream:
    def __init__(self, stream, phase, callback):
        self.stream = stream
        self.phase = phase
        self.callback = callback

    def __enter__(self):
        self.stream.__enter__()
        return self

    def __exit__(self, *args):
        result = self.stream.__exit__(*args)
        if self.phase == "close":
            self.callback()
        return result

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def write(self, data):
        result = self.stream.write(data)
        if self.phase == "write":
            self.stream.flush()
            self.callback()
        return result


def _during_receipt(builder, monkeypatch, host, manifest, phase, callback):
    if host == "posix":
        original = builder.os.fdopen

        def fdopen(fd, mode="r", *args, **kwargs):
            stream = original(fd, mode, *args, **kwargs)
            if mode == "w" and kwargs.get("encoding") == "utf-8":
                return ManifestStream(stream, phase, callback)
            return stream

        monkeypatch.setattr(builder.os, "fdopen", fdopen)
    else:
        original = Path.open

        def path_open(path, mode="r", *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            if path == manifest and mode == "x":
                return ManifestStream(stream, phase, callback)
            return stream

        monkeypatch.setattr(Path, "open", path_open)


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("prior", [False, True])
@pytest.mark.parametrize("target_index", [None, 0, 1])
def test_final_source_check_cannot_hide_changed_launcher(
    builder, tmp_path, monkeypatch, host, prior, target_index
):
    output = _setup(builder, tmp_path, monkeypatch, host, prior)
    original = builder.desktop_source_digest
    injected = False
    foreign = b"foreign output changed during final source hashing"

    def final_digest(root):
        nonlocal injected
        value = original(root)
        if (
            root == tmp_path
            and not injected
            and all(
                (output / name).is_file()
                and (output / name).read_bytes() == b"new compiled launcher"
                for name in builder.LAUNCHERS
            )
        ):
            injected = True
            if target_index is not None:
                (output / builder.LAUNCHERS[target_index]).write_bytes(foreign)
        return value

    monkeypatch.setattr(builder, "desktop_source_digest", final_digest)
    if target_index is None:
        builder.build(output)
        builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)
        builder.build(output)
    else:
        with pytest.raises(RuntimeError, match="launcher bytes changed"):
            builder.build(output)
        assert (output / builder.LAUNCHERS[target_index]).read_bytes() == foreign
        assert not (output / "desktop-build.json").exists()
    assert injected
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("phase", ["write", "close"])
@pytest.mark.parametrize("target_index", [0, 1])
def test_receipt_write_cannot_hide_changed_launcher(
    builder, tmp_path, monkeypatch, host, phase, target_index
):
    output = _setup(builder, tmp_path, monkeypatch, host, False)
    manifest = output / "desktop-build.json"
    target = output / builder.LAUNCHERS[target_index]
    foreign = b"foreign output changed while the receipt was written"
    _during_receipt(
        builder, monkeypatch, host, manifest, phase, lambda: target.write_bytes(foreign)
    )

    with pytest.raises(RuntimeError, match="launcher bytes changed"):
        builder.build(output)

    assert target.read_bytes() == foreign
    assert not manifest.exists()
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("phase", ["write", "close"])
@pytest.mark.parametrize("kind", ["replacement", "in-place", "symlink", "missing"])
def test_changed_receipt_is_refused_and_foreign_content_preserved(
    builder, tmp_path, monkeypatch, host, phase, kind
):
    output = _setup(builder, tmp_path, monkeypatch, host, False)
    manifest = output / "desktop-build.json"
    outside = tmp_path / "foreign receipt"
    foreign = b"foreign receipt content must survive"
    outside.write_bytes(foreign)

    def change_receipt():
        if kind != "in-place":
            manifest.unlink()
        if kind == "replacement" or kind == "in-place":
            manifest.write_bytes(foreign)
        elif kind == "symlink":
            manifest.symlink_to(outside)

    _during_receipt(builder, monkeypatch, host, manifest, phase, change_receipt)
    with pytest.raises(RuntimeError, match="manifest.*changed"):
        builder.build(output)

    assert outside.read_bytes() == foreign
    if kind == "missing":
        assert not manifest.exists()
    else:
        assert manifest.read_bytes() == foreign
        assert manifest.is_symlink() is (kind == "symlink")
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", ["posix", "nt"])
def test_failed_owned_receipt_cleanup_preserves_primary_error(
    builder, tmp_path, monkeypatch, capsys, host
):
    output = _setup(builder, tmp_path, monkeypatch, host, False)
    manifest = output / "desktop-build.json"
    target = output / builder.LAUNCHERS[0]
    mutation_reached = False

    def change_launcher():
        nonlocal mutation_reached
        target.write_bytes(b"foreign launcher")
        mutation_reached = True

    _during_receipt(
        builder,
        monkeypatch,
        host,
        manifest,
        "close",
        change_launcher,
    )
    original_unlink = builder.os.unlink

    def refuse_manifest_cleanup(path, *args, **kwargs):
        if mutation_reached and Path(path).name == manifest.name:
            raise PermissionError("controlled cleanup refusal")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(builder.os, "unlink", refuse_manifest_cleanup)
    with pytest.raises(RuntimeError, match="launcher bytes changed"):
        builder.build(output)

    assert manifest.exists()
    assert target.read_bytes() == b"foreign launcher"
    assert "manifest cleanup" in capsys.readouterr().err


@pytest.mark.parametrize("host", ["posix", "nt"])
@pytest.mark.parametrize("primary_error", [False, True])
@pytest.mark.parametrize("change_during_read", [False, True])
def test_receipt_edit_during_read_is_not_accepted_or_removed(
    builder, tmp_path, monkeypatch, host, primary_error, change_during_read
):
    output = _setup(builder, tmp_path, monkeypatch, host, False)
    manifest = output / "desktop-build.json"
    foreign = b"foreign receipt edited while its bytes were read"
    changed = False
    if primary_error:
        _during_receipt(
            builder,
            monkeypatch,
            host,
            manifest,
            "close",
            lambda: (output / builder.LAUNCHERS[0]).write_bytes(b"foreign launcher"),
        )

    class ReadStream:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def __getattr__(self, name):
            return getattr(self.stream, name)

        def read(self, *args):
            nonlocal changed
            data = self.stream.read(*args)
            if change_during_read and not changed:
                manifest.write_bytes(foreign)
                changed = True
            return data

    if host == "posix":
        original = builder.os.fdopen

        def fdopen(fd, mode="r", *args, **kwargs):
            receipt_read = (
                mode == "rb"
                and manifest.exists()
                and builder.os.fstat(fd).st_ino == manifest.stat().st_ino
            )
            stream = original(fd, mode, *args, **kwargs)
            return ReadStream(stream) if receipt_read else stream

        monkeypatch.setattr(builder.os, "fdopen", fdopen)
    else:
        original = Path.open

        def path_open(path, mode="r", *args, **kwargs):
            stream = original(path, mode, *args, **kwargs)
            return ReadStream(stream) if path == manifest and mode == "rb" else stream

        monkeypatch.setattr(Path, "open", path_open)

    if primary_error or change_during_read:
        message = "launcher bytes changed" if primary_error else "manifest.*changed"
        with pytest.raises(RuntimeError, match=message):
            builder.build(output)
    else:
        builder.build(output)
        builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)
    if change_during_read:
        assert changed
        assert manifest.read_bytes() == foreign
    elif primary_error:
        assert not manifest.exists()
    assert not (output / ".build.lock").exists()
