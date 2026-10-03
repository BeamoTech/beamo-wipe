#!/usr/bin/env python3
"""Authenticate USB download metadata and verify regular files; never write media."""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from beamo_wipe.release_signing import (  # noqa: E402
    _read_bytes_file, _read_json_file, _unique_json_fields,
    load_key_registry, verify_release_acceptance,
)

CHUNK = 1024 * 1024


def record(inventory, name):
    value = inventory["files"][name]
    if (type(value["bytes"]) is not int or value["bytes"] <= 0
            or not isinstance(value["sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["sha256"])):
        raise RuntimeError(f"invalid size/hash metadata for {name}")
    return value


def check_bytes(data, expected, name):
    if len(data) != expected["bytes"] or hashlib.sha256(data).hexdigest() != expected["sha256"]:
        raise RuntimeError(f"size/SHA256 mismatch: {name}")


def check_stream(stream, expected, name):
    if os.fstat(stream.fileno()).st_size != expected["bytes"]:
        raise RuntimeError(f"size mismatch: {name}")
    digest = hashlib.sha256()
    count = 0
    for chunk in iter(lambda: stream.read(CHUNK), b""):
        count += len(chunk)
        if count > expected["bytes"]:
            raise RuntimeError(f"file grew beyond authenticated size: {name}")
        digest.update(chunk)
    if count != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
        raise RuntimeError(f"size/SHA256 mismatch: {name}")


def open_regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        os.close(fd)
        raise RuntimeError(f"not a regular file: {path.name}")
    return os.fdopen(fd, "rb")


def authenticate(directory, registry_path, fingerprint, version, source):
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise RuntimeError("version must be X.Y.Z")
    if not re.fullmatch(r"[0-9a-f]{40}", source) or not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise RuntimeError("expected source commit and trusted key fingerprint must be full hex identities")
    if (os.name != "posix" or not directory.is_absolute() or directory.is_symlink()
            or not directory.is_dir() or directory.stat().st_uid != os.getuid()
            or stat.S_IMODE(directory.stat().st_mode) & 0o077):
        raise RuntimeError("use an absolute, owned, private working directory created with mktemp -d")
    if not registry_path.is_absolute():
        raise RuntimeError("trusted registry path must be absolute")
    registry = load_key_registry(_read_json_file(registry_path, what="trusted registry"))
    stem = f"beamo-wipe-{version}-amd64"
    manifest_name = stem + ".manifest.json"
    documents = {}
    payloads = {}
    for name in ("release-downloads.json", manifest_name):
        payload = _read_bytes_file(directory / name, what=name)
        signature = _read_json_file(directory / (name + ".sig"), what="detached signature")
        result = verify_release_acceptance(payload, signature, registry, min_version=version)
        if registry[result["key_id"]]["fingerprint"] != fingerprint:
            raise RuntimeError("signature key differs from independently authenticated fingerprint")
        if result["beamo_wipe_version"] != version:
            raise RuntimeError("signed document is for a different release version")
        documents[name] = json.loads(payload, object_pairs_hook=_unique_json_fields)
        payloads[name] = payload
    inventory, manifest = documents["release-downloads.json"], documents[manifest_name]
    if inventory["schema"] != "beamo-wipe-release-downloads/1" or manifest["schema_version"] != 2:
        raise RuntimeError("unsupported inventory/manifest schema")
    if (inventory["source_commit"] != source or manifest["source"]["commit"] != source
            or manifest["source"]["tag"] != "v" + version
            or manifest["source"]["dirty"] is not False
            or manifest["source"]["remote_url"] != "https://github.com/BeamoTech/beamo-wipe"):
        raise RuntimeError("signed release tag/source identity differs from the expected release")
    build = inventory["qualified_build_id"]
    if (not isinstance(build, str)
            or not re.fullmatch(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}", build)
            or manifest["build"]["release_build_id"] != build):
        raise RuntimeError("signed inventory and manifest have different/invalid build identities")
    check_bytes(payloads[manifest_name], record(inventory, manifest_name), manifest_name)
    sig_name = manifest_name + ".sig"
    check_bytes(_read_bytes_file(directory / sig_name, what=sig_name), record(inventory, sig_name), sig_name)
    meta_name = stem + ".img.json"
    meta_bytes = _read_bytes_file(directory / meta_name, what=meta_name)
    check_bytes(meta_bytes, record(inventory, meta_name), meta_name)
    meta = json.loads(meta_bytes, object_pairs_hook=_unique_json_fields)
    raw, compressed = record(inventory, stem + ".img"), record(inventory, stem + ".img.gz")
    iso = record(inventory, stem + ".iso")
    if (meta["schema_version"] != 1 or meta["image"] != stem + ".img"
            or meta["size"] != raw["bytes"] or meta["sha256"] != raw["sha256"]
            or meta["iso"] != stem + ".iso" or meta["iso_sha256"] != iso["sha256"]
            or manifest["artifact"]["iso_name"] != stem + ".iso"
            or manifest["artifact"]["iso_sha256"] != iso["sha256"]
            or manifest["artifact"]["iso_size_bytes"] != iso["bytes"]):
        raise RuntimeError("USB image metadata does not match signed USB/ISO provenance")
    print(f"AUTHENTICATED metadata: v{version}, source {source}, build {build}")
    for name, value in ((stem + ".img.gz", compressed), (stem + ".img", raw)):
        print(f"EXPECTED {name}: {value['bytes']} bytes, SHA256 {value['sha256']}")
    return stem, compressed, raw


def verify(directory, registry, fingerprint, version, source, mode):
    stem, compressed, raw = authenticate(directory, registry, fingerprint, version, source)
    if mode == "metadata":
        return
    output = directory / (stem + ".img")
    partial = directory / (stem + ".img.partial")
    if mode == "extract" and (os.path.lexists(output) or os.path.lexists(partial)):
        raise RuntimeError("stale image/partial output exists; start again in a new empty directory")
    with open_regular(directory / (stem + ".img.gz")) as packed:
        check_stream(packed, compressed, stem + ".img.gz")
        print("VERIFIED compressed USB download")
        if mode == "extract":
            packed.seek(0)
            fd = os.open(partial, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            # A failed extraction deliberately retains a clearly named partial;
            # only authenticated, complete output is published as .img.
            with os.fdopen(fd, "w+b") as target:
                with gzip.GzipFile(fileobj=packed, mode="rb") as unpacked:
                    count = 0
                    while True:
                        chunk = unpacked.read(min(CHUNK, raw["bytes"] - count + 1))
                        if not chunk:
                            break
                        count += len(chunk)
                        if count > raw["bytes"]:
                            raise RuntimeError("decompressed data exceeds authenticated raw size")
                        target.write(chunk)
                target.flush()
                os.fsync(target.fileno())
                target.seek(0)
                check_stream(target, raw, output.name)
                os.link(partial, output)  # Atomic publication, never overwrite.
            partial.unlink()
    with open_regular(output) as image:
        check_stream(image, raw, output.name)
    print(f"VERIFIED raw USB image: {output}")
    print("STOP before media writing. This verifies publisher-bound bytes, not runtime or erase safety.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("metadata", "extract", "verify"))
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--trusted-key-sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--expected-source", required=True)
    args = parser.parse_args(argv)
    try:
        verify(args.directory, args.registry, args.trusted_key_sha256,
               args.version, args.expected_source, args.mode)
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, EOFError, zlib.error) as exc:
        print(f"STOP: USB verification failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
