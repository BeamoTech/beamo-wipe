"""PASS22 regressions for the protected release publisher trust boundary."""

from __future__ import annotations

import io
import os
from pathlib import Path

import pytest

from test_release_publisher import PUBLISHER


class _Response:
    def __init__(self, status: int, body: bytes):
        self.status = status
        self._body = io.BytesIO(body)

    def read(self, size: int = -1) -> bytes:
        return self._body.read(size)

    def close(self) -> None:
        pass


def test_owned_release_input_rejects_hard_link(tmp_path):
    payload = tmp_path / "payload"
    payload.write_bytes(b"qualified bytes")
    os.link(payload, tmp_path / "alias")

    with pytest.raises(PUBLISHER.PublishError, match="unsafe release input"):
        PUBLISHER._regular_owned_file(payload)


@pytest.mark.parametrize("replacement", ["leaf", "parent"])
def test_open_release_input_retains_requested_name(tmp_path, replacement):
    parent = tmp_path / "dist"
    parent.mkdir()
    payload = parent / "artifact"
    payload.write_bytes(b"qualified bytes")

    with pytest.raises(PUBLISHER.PublishError, match="changed|unsafe"):
        with PUBLISHER._open_owned_file(payload) as stream:
            assert stream.read() == b"qualified bytes"
            if replacement == "leaf":
                payload.unlink()
                payload.write_bytes(b"qualified bytes")
            else:
                displaced = tmp_path / "displaced"
                parent.rename(displaced)
                parent.mkdir()
                payload.write_bytes(b"qualified bytes")


@pytest.mark.parametrize("layout", ["linked-parent", "hard-link"])
def test_signing_key_rejects_linked_storage(tmp_path, monkeypatch, layout):
    private = tmp_path / "private"
    private.mkdir()
    key = private / "release.key"
    key.write_bytes(b"k" * 32)
    key.chmod(0o600)
    if layout == "linked-parent":
        exposed = tmp_path / "exposed"
        exposed.symlink_to(private, target_is_directory=True)
        requested = exposed / key.name
    else:
        requested = tmp_path / "release.key"
        os.link(key, requested)
    monkeypatch.setenv("BEAMO_WIPE_SIGNING_KEY_FILE", str(requested))

    with pytest.raises(PUBLISHER.PublishError, match="unsafe signing material"):
        PUBLISHER._read_signing_key()


def _stub_signature_verification(monkeypatch):
    from beamo_wipe import release_signing

    monkeypatch.setattr(PUBLISHER, "_read_signing_key", lambda: b"k" * 32)
    monkeypatch.setattr(
        release_signing,
        "sign_manifest_bytes",
        lambda _manifest, _key: {"key_id": "fixture"},
    )
    monkeypatch.setattr(release_signing, "load_key_registry", lambda _raw: {})
    monkeypatch.setattr(
        release_signing,
        "verify_with_registry",
        lambda _manifest, _sidecar, _registry: {"key_id": "fixture"},
    )


@pytest.mark.parametrize("layout", ["linked-parent", "hard-link"])
def test_publisher_registry_rejects_linked_storage(tmp_path, monkeypatch, layout):
    _stub_signature_verification(monkeypatch)
    version = "0.2.13"
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / f"beamo-wipe-{version}-amd64.manifest.json").write_bytes(b"{}")
    private = tmp_path / "private-keys"
    private.mkdir()
    registry = private / "keys.json"
    registry.write_text("{}", encoding="utf-8")
    packaging = tmp_path / "packaging" / "release-keys"
    packaging.parent.mkdir()
    if layout == "linked-parent":
        packaging.symlink_to(private, target_is_directory=True)
    else:
        packaging.mkdir()
        os.link(registry, packaging / "keys.json")
    monkeypatch.setattr(PUBLISHER, "ROOT", tmp_path)

    with pytest.raises(
        PUBLISHER.PublishError, match="registry.*unsafe|unsafe.*registry"
    ):
        PUBLISHER._sign_release_manifest(dist, version, manifest_bytes=b"{}")


def test_generated_signature_rejects_same_byte_replacement(tmp_path, monkeypatch):
    _stub_signature_verification(monkeypatch)
    version = "0.2.13"
    manifest = tmp_path / f"beamo-wipe-{version}-amd64.manifest.json"
    manifest.write_bytes(b"{}")
    registry = tmp_path / "packaging" / "release-keys" / "keys.json"
    registry.parent.mkdir(parents=True)
    registry.write_text("{}", encoding="utf-8")
    signature = Path(f"{manifest}.sig")
    real_fdopen = PUBLISHER.os.fdopen

    class ReplacingStream:
        def __init__(self, fd, *args, **kwargs):
            self.stream = real_fdopen(fd, *args, **kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, payload):
            result = self.stream.write(payload)
            self.stream.flush()
            signature.unlink()
            signature.write_bytes(payload)
            return result

        def flush(self):
            return self.stream.flush()

        def fileno(self):
            return self.stream.fileno()

    monkeypatch.setattr(PUBLISHER, "ROOT", tmp_path)
    monkeypatch.setattr(PUBLISHER.os, "fdopen", ReplacingStream)

    with pytest.raises(PUBLISHER.PublishError, match="signature sidecar changed"):
        PUBLISHER._sign_release_manifest(tmp_path, version, manifest_bytes=b"{}")


def test_bound_upload_rejects_same_byte_replacement(tmp_path, monkeypatch):
    payload = tmp_path / "artifact"
    payload.write_bytes(b"qualified bytes")
    snapshot = PUBLISHER._snapshot_owned_file(payload)
    payload.unlink()
    payload.write_bytes(b"qualified bytes")
    monkeypatch.setattr(
        PUBLISHER,
        "_upload_stream",
        lambda *_args: pytest.fail("a replaced input must not start an upload"),
    )

    with pytest.raises(PUBLISHER.PublishError, match="changed after verification"):
        PUBLISHER._upload_file(payload, "releases/build/artifact", snapshot)


def test_bound_upload_rejects_in_place_mutation(tmp_path, monkeypatch):
    payload = tmp_path / "artifact"
    payload.write_bytes(b"qualified bytes")

    def mutate_during_upload(_name, stream, _size):
        assert stream.read(1) == b"q"
        payload.write_bytes(b"tampered-bytes!")
        stream.read()

    monkeypatch.setattr(PUBLISHER, "_upload_stream", mutate_during_upload)

    with pytest.raises(PUBLISHER.PublishError, match="changed"):
        PUBLISHER._upload_file(payload, "releases/build/artifact")


def test_metadata_token_rejects_duplicate_access_token(monkeypatch):
    class Connection:
        def __init__(self, host, timeout):
            assert host == PUBLISHER.METADATA_HOST and timeout == 10

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            return _Response(
                200,
                b'{"access_token":"first-token-value-long",'
                b'"access_token":"second-token-value-long"}',
            )

        def close(self):
            pass

    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.setattr(PUBLISHER.http.client, "HTTPConnection", Connection)

    with pytest.raises(PUBLISHER.PublishError, match="duplicate JSON field"):
        PUBLISHER._metadata_token()


@pytest.mark.parametrize("function", ["start", "send"])
@pytest.mark.parametrize("size", [-1, True])
def test_upload_rejects_invalid_declared_size(monkeypatch, function, size):
    monkeypatch.setattr(
        PUBLISHER.http.client,
        "HTTPSConnection",
        lambda *_args, **_kwargs: pytest.fail("invalid size reached the network"),
    )
    with pytest.raises(PUBLISHER.PublishError, match="invalid upload size"):
        if function == "start":
            PUBLISHER._start_resumable_upload("releases/build/artifact", size, "token")
        else:
            PUBLISHER._send_upload("/upload/session", io.BytesIO(), size, "token")


@pytest.mark.parametrize("body", [b"ab", b"abcd"])
def test_remote_readback_requires_exact_uploaded_size(monkeypatch, body):
    class Connection:
        def __init__(self, host, timeout):
            assert host == PUBLISHER.STORAGE_HOST and timeout == 120

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            return _Response(200, body)

        def close(self):
            pass

    monkeypatch.setattr(PUBLISHER, "_metadata_token", lambda: "token")
    monkeypatch.setattr(PUBLISHER.http.client, "HTTPSConnection", Connection)

    with pytest.raises(PUBLISHER.PublishError, match="size verification failed"):
        PUBLISHER._remote_sha256("releases/build/artifact", expected_size=3)


def test_remote_readback_accepts_exact_uploaded_size(monkeypatch):
    class Connection:
        def __init__(self, host, timeout):
            assert host == PUBLISHER.STORAGE_HOST and timeout == 120

        def request(self, *_args, **_kwargs):
            pass

        def getresponse(self):
            return _Response(200, b"abc")

        def close(self):
            pass

    monkeypatch.setattr(PUBLISHER, "_metadata_token", lambda: "token")
    monkeypatch.setattr(PUBLISHER.http.client, "HTTPSConnection", Connection)

    assert (
        PUBLISHER._remote_sha256("releases/build/artifact", expected_size=3)
        == PUBLISHER.hashlib.sha256(b"abc").hexdigest()
    )


def test_bound_upload_positive_control(tmp_path, monkeypatch):
    payload = tmp_path / "artifact"
    payload.write_bytes(b"qualified bytes")
    uploaded = {}

    def upload_stream(name, stream, size):
        body = stream.read()
        assert len(body) == size
        uploaded[name] = body

    monkeypatch.setattr(PUBLISHER, "_upload_stream", upload_stream)
    PUBLISHER._upload_file(payload, "releases/build/artifact")

    assert uploaded == {"releases/build/artifact": b"qualified bytes"}
