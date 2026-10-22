"""Prior receipt validation never authorizes retiring another writer's bytes."""

import os

import pytest

from test_desktop_output_replacement_pass2_20261019 import (
    _setup,
    builder as existing_builder_fixture,
)


HOSTS = ("posix", "nt")


@pytest.fixture
def builder():
    return existing_builder_fixture.__wrapped__()


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize(
    "prior,change",
    [
        (prior, change)
        for prior in (False, True)
        for change in ("replace", "edit", "symlink", "directory", "remove", "metadata")
        if prior or change not in {"remove", "metadata"}
    ],
)
def test_changed_prior_receipt_is_preserved_before_any_compilation(
    builder,
    tmp_path,
    monkeypatch,
    host,
    prior,
    change,
):
    output = _setup(builder, tmp_path, monkeypatch, host, prior)
    manifest = output / "desktop-build.json"
    outside = tmp_path / "foreign-receipt"
    foreign = b"foreign receipt must survive retirement"
    outside.write_bytes(foreign)
    original = builder._require_generated_prior_manifest
    compile_call = builder.subprocess.check_call
    compiled = []

    def record_compile(*args, **kwargs):
        compiled.append(args)
        return compile_call(*args, **kwargs)

    def change_after_validation(*args, **kwargs):
        expected = original(*args, **kwargs)
        if change in {"replace", "symlink", "directory", "remove"}:
            manifest.unlink(missing_ok=True)
        if change == "symlink":
            manifest.symlink_to(outside)
        elif change == "directory":
            manifest.mkdir()
            (manifest / "foreign-content").write_bytes(foreign)
        elif change == "metadata":
            info = manifest.stat()
            os.utime(manifest, ns=(info.st_atime_ns, info.st_mtime_ns + 1_000_000))
        elif change != "remove":
            manifest.write_bytes(foreign)
        return expected

    monkeypatch.setattr(
        builder, "_require_generated_prior_manifest", change_after_validation
    )
    monkeypatch.setattr(builder.subprocess, "check_call", record_compile)
    with pytest.raises(RuntimeError, match="prior manifest"):
        builder.build(output)
    assert not compiled
    if change == "remove":
        assert not manifest.exists()
    elif change == "directory":
        assert (manifest / "foreign-content").read_bytes() == foreign
    elif change == "metadata":
        assert manifest.is_file()
    else:
        assert manifest.read_bytes() == foreign
        assert manifest.is_symlink() is (change == "symlink")
    assert outside.read_bytes() == foreign
    for name in builder.LAUNCHERS:
        assert (
            (output / name).read_bytes() == b"prior compiled launcher"
            if prior
            else not (output / name).exists()
        )
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("ordinal", (1, 2, 3))
@pytest.mark.parametrize("change", (False, True))
def test_prior_receipt_metadata_spans_each_retirement_read(
    builder,
    tmp_path,
    monkeypatch,
    host,
    ordinal,
    change,
):
    output = _setup(builder, tmp_path, monkeypatch, host, True)
    manifest = output / "desktop-build.json"
    original = builder._read_output_file
    reads = 0
    foreign = b"foreign receipt edited while a captured read returned old bytes"

    def read_then_edit(*args, **kwargs):
        nonlocal reads
        data = original(*args, **kwargs)
        if args[2] == manifest.name:
            reads += 1
            if change and reads == ordinal:
                manifest.write_bytes(foreign)
        return data

    monkeypatch.setattr(builder, "_read_output_file", read_then_edit)
    if change:
        with pytest.raises(RuntimeError, match="prior manifest"):
            builder.build(output)
        assert manifest.read_bytes() == foreign
        for name in builder.LAUNCHERS:
            assert (output / name).read_bytes() == b"prior compiled launcher"
    else:
        builder.build(output)
        builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)
    assert reads >= ordinal
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("prior", (False, True))
def test_unchanged_prior_or_absent_receipt_remains_rebuildable(
    builder,
    tmp_path,
    monkeypatch,
    host,
    prior,
):
    output = _setup(builder, tmp_path, monkeypatch, host, prior)
    builder.build(output)
    builder.verify_desktop_bundle(tmp_path, output, "a" * 40, "0.2.14", False)
    builder.build(output)
    assert not (output / ".build.lock").exists()


@pytest.mark.parametrize("host", HOSTS)
@pytest.mark.parametrize("swap", ("lock", "directory"))
def test_receipt_retirement_rechecks_lock_and_directory_ownership(
    builder,
    tmp_path,
    monkeypatch,
    host,
    swap,
):
    output = _setup(builder, tmp_path, monkeypatch, host, True)
    original_bytes = (output / "desktop-build.json").read_bytes()
    archive = tmp_path / "original-output"
    foreign = b"foreign directory receipt"
    original = builder._require_generated_prior_manifest

    def change_after_validation(*args, **kwargs):
        expected = original(*args, **kwargs)
        if swap == "lock":
            (output / ".build.lock").unlink()
            (output / ".build.lock").write_bytes(b"foreign lock")
        else:
            output.rename(archive)
            output.mkdir()
            os.link(archive / ".build.lock", output / ".build.lock")
            (output / "desktop-build.json").write_bytes(foreign)
        return expected

    monkeypatch.setattr(
        builder, "_require_generated_prior_manifest", change_after_validation
    )
    with pytest.raises(RuntimeError, match="build lock changed"):
        builder.build(output)
    if swap == "lock":
        assert (output / "desktop-build.json").read_bytes() == original_bytes
        assert (output / ".build.lock").read_bytes() == b"foreign lock"
    else:
        assert (archive / "desktop-build.json").read_bytes() == original_bytes
        assert (output / "desktop-build.json").read_bytes() == foreign
