"""Actual signatures and disposable regular images; no media writes or network."""

import base64
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from beamo_wipe import release_signing as signing

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.12"
SOURCE = "e986419379f512f8088f5982ee02a51dc91a9dae"
STEM = f"beamo-wipe-{VERSION}-amd64"
pytestmark = pytest.mark.skipif(os.name != "posix", reason="USB file verification supports POSIX Linux/macOS")


@pytest.fixture
def verifier():
    spec = importlib.util.spec_from_file_location("usb_download", ROOT / "scripts/verify-usb-download.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def release(tmp_path):
    private, public = signing.generate_keypair()  # Test key only, never written.
    directory = tmp_path / "release with spaces"
    directory.mkdir(mode=0o700)
    registry = tmp_path / "trusted-keys.json"
    fingerprint = signing.fingerprint(public)
    registry.write_text(json.dumps({"schema": signing.KEYS_SCHEMA, "keys": {
        signing.key_id(public): {"fingerprint": fingerprint,
                                "public_key": base64.b64encode(public).decode(), "status": "active"}}}))
    raw = b"harmless regular-file image fixture\n" * 100
    packed = gzip.compress(raw, mtime=0)
    (directory / (STEM + ".img.gz")).write_bytes(packed)
    build = "12345678-1234-1234-1234-123456789abc"
    manifest = {"schema_version": 2, "beamo_wipe_version": VERSION,
                "source": {"commit": SOURCE, "tag": "v" + VERSION, "dirty": False,
                           "remote_url": "https://github.com/BeamoTech/beamo-wipe"},
                "build": {"release_build_id": build},
                "artifact": {"iso_name": STEM + ".iso", "iso_sha256": "b" * 64, "iso_size_bytes": 100}}
    def write(name, data):
        (directory / name).write_text(json.dumps(data))
    def signed(name, data):
        write(name, data)
        write(name + ".sig", signing.sign_manifest_bytes((directory / name).read_bytes(), private))
    def record(data):
        return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    signed(STEM + ".manifest.json", manifest)
    meta = {"schema_version": 1, "image": STEM + ".img", "size": len(raw),
            "sha256": record(raw)["sha256"], "iso": STEM + ".iso", "iso_sha256": "b" * 64}
    write(STEM + ".img.json", meta)
    inventory = {"schema": "beamo-wipe-release-downloads/1", "beamo_wipe_version": VERSION,
                 "source_commit": SOURCE, "qualified_build_id": build,
                 "files": {p.name: record(p.read_bytes()) for p in directory.iterdir()}}
    inventory["files"][STEM + ".img"] = record(raw)
    inventory["files"][STEM + ".iso"] = {"bytes": 100, "sha256": "b" * 64}
    def resign():
        write(STEM + ".img.json", meta)
        inventory["files"][STEM + ".img.json"] = record((directory / (STEM + ".img.json")).read_bytes())
        signed("release-downloads.json", inventory)
    resign()
    args = ["--directory", str(directory), "--registry", str(registry),
            "--trusted-key-sha256", fingerprint, "--version", VERSION, "--expected-source", SOURCE]
    return directory, registry, raw, inventory, meta, resign, args


def test_authenticate_extract_and_verify_from_unrelated_cwd(release, verifier, tmp_path, monkeypatch):
    directory, _registry, raw, *_rest, args = release
    monkeypatch.chdir(tmp_path)
    for mode in ("metadata", "extract", "verify"):
        assert verifier.main([mode, *args]) == 0
    assert (directory / (STEM + ".img")).read_bytes() == raw
    assert not (directory / (STEM + ".img.partial")).exists()


@pytest.mark.parametrize("damage", ["inventory", "signature", "compressed", "missing-raw",
    "missing-size", "wrong-build", "wrong-source", "raw-hash", "raw-size", "traversal", "revoked", "gzip",
    "deflate", "missing-inventory-signature", "missing-manifest-signature", "wrong-key"])
def test_stop_conditions_never_publish_an_image(release, verifier, damage, capsys):
    directory, registry, _raw, inventory, meta, resign, args = release
    if damage == "inventory":
        p = directory / "release-downloads.json"
        p.write_bytes(p.read_bytes() + b" ")
    elif damage == "signature":
        p = directory / "release-downloads.json.sig"
        data = json.loads(p.read_text())
        data["signature"] = base64.b64encode(b"x" * 64).decode()
        p.write_text(json.dumps(data))
    elif damage == "compressed":
        p = directory / (STEM + ".img.gz")
        p.write_bytes(b"bad" + p.read_bytes()[3:])
    elif damage == "revoked":
        data = json.loads(registry.read_text())
        next(iter(data["keys"].values()))["status"] = "revoked"
        registry.write_text(json.dumps(data))
    elif damage == "wrong-source":
        args[-1] = "a" * 40
    elif damage == "wrong-key":
        args[5] = "a" * 64
    elif damage == "missing-inventory-signature":
        (directory / "release-downloads.json.sig").unlink()
    elif damage == "missing-manifest-signature":
        (directory / (STEM + ".manifest.json.sig")).unlink()
    else:
        if damage == "missing-raw":
            del inventory["files"][STEM + ".img"]
        elif damage == "missing-size":
            del inventory["files"][STEM + ".img.gz"]["bytes"]
        elif damage == "wrong-build":
            inventory["qualified_build_id"] = "a" * 36
        elif damage == "raw-hash":
            meta["sha256"] = inventory["files"][STEM + ".img"]["sha256"] = "c" * 64
        elif damage == "raw-size":
            meta["size"] = inventory["files"][STEM + ".img"]["bytes"] = 1
        elif damage == "traversal":
            meta["image"] = "../../outside.img"
        elif damage in ("gzip", "deflate"):
            # A reserved DEFLATE block type raises zlib.error, not BadGzipFile.
            packed = b"not gzip" if damage == "gzip" else gzip.compress(b"x", mtime=0)[:10] + b"\x07" + b"\0" * 8
            (directory / (STEM + ".img.gz")).write_bytes(packed)
            inventory["files"][STEM + ".img.gz"] = {"bytes": len(packed), "sha256": hashlib.sha256(packed).hexdigest()}
        resign()
    assert verifier.main(["extract", *args]) == 1
    assert "STOP: USB verification failed" in capsys.readouterr().err
    assert not (directory / (STEM + ".img")).exists()


@pytest.mark.parametrize("name", [".img", ".img.partial"])
def test_stale_output_never_overwritten(release, verifier, name):
    directory, *_rest, args = release
    stale = directory / (STEM + name)
    stale.write_bytes(b"preserve stale file")
    assert verifier.main(["extract", *args]) == 1
    assert stale.read_bytes() == b"preserve stale file"


def test_raw_corruption_and_wrong_directory_stop(release, verifier, tmp_path):
    directory, *_rest, args = release
    assert verifier.main(["extract", *args]) == 0
    path = directory / (STEM + ".img")
    path.write_bytes(b"x" + path.read_bytes()[1:])
    assert verifier.main(["verify", *args]) == 1
    args[1] = str(tmp_path)
    assert verifier.main(["extract", *args]) == 1
    args[1] = "."
    assert verifier.main(["extract", *args]) == 1


def test_symlink_input_is_not_followed(release, verifier, tmp_path):
    directory, *_rest, args = release
    packed = directory / (STEM + ".img.gz")
    elsewhere = tmp_path / "outside.gz"
    packed.rename(elsewhere)
    packed.symlink_to(elsewhere)
    assert verifier.main(["extract", *args]) == 1
    assert not (directory / (STEM + ".img")).exists()


def test_copyable_document_block_with_fixture_downloads(release, tmp_path):
    directory, registry, raw, *_rest, args = release
    trusted = tmp_path / "trusted checkout"
    (trusted / "scripts").mkdir(parents=True)
    (trusted / "packaging/release-keys").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts/verify-usb-download.py", trusted / "scripts")
    shutil.copy2(registry, trusted / "packaging/release-keys/keys.json")
    (trusted / "src").symlink_to(ROOT / "src", target_is_directory=True)
    tools = tmp_path / "tools"
    tools.mkdir()
    curl = tools / "curl"
    curl.write_text(f"#!{sys.executable}\n" +
                   "import os,pathlib,sys\n"
                   "name=sys.argv[-1].rsplit('/',1)[-1]\n"
                   "sys.stdout.buffer.write((pathlib.Path(os.environ['FIXTURE_RELEASE'])/name).read_bytes())\n")
    curl.chmod(0o755)
    doc = (ROOT / "docs/release-verification.md").read_text()
    block = doc.split("<!-- USB-VERIFY-WALKTHROUGH-BEGIN -->", 1)[1].split("<!-- USB-VERIFY-WALKTHROUGH-END -->", 1)[0]
    block = block.split("```sh\n", 1)[1].split("```", 1)[0]
    block = block.replace("/absolute/path/to/trusted/beamo-wipe", str(trusted))
    block = block.replace("93caaf7ca93eff4d7fa1c16e360f9d6aa17ced0155a56d4cf89d8f6d429e66f7", args[5])
    result = subprocess.run(  # noqa: S603
        ["/bin/sh", "-c", block], cwd=tmp_path,
        env=dict(os.environ, TMPDIR=str(tmp_path), FIXTURE_RELEASE=str(directory),
                 PATH=str(tools) + os.pathsep + os.environ["PATH"]),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    work = Path(next(line.split(": ", 1)[1] for line in result.stdout.splitlines()
                     if line.startswith("Private verification directory:")))
    assert (work / (STEM + ".img")).read_bytes() == raw
    assert result.stdout.count("VERIFIED raw USB image") == 2
    assert "/dev/" not in block and "sudo" not in block
