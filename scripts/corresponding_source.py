#!/usr/bin/env python3
"""Assemble the GPL corresponding source for one published Beamo Wipe release.

The USB's SOURCE.txt is a written offer. This tool turns a release's signed
manifest into the exact source set that offer covers, so it can be archived
for at least three years and given to anyone who asks:

  plan  MANIFEST.json --out SOURCES.json
        Every installed Debian binary package (from the manifest's measured
        dpkg inventory) mapped to its exact source package and version, plus
        the pinned nwipe commit and the Beamo Wipe source commit.
  fetch SOURCES.json DEST
        Download each Debian source package (.dsc, orig and debian files) from
        snapshot.debian.org, which keeps every version ever published, and
        check every file against snapshot's content hash and the .dsc's
        Checksums-Sha256. Add upstream nwipe and Beamo Wipe tarballs at their
        pinned commits. DEST must not exist. SHA256SUMS lists every file.

Verify the manifest first (scripts/verify-usb-download.py) so the inventory is
the authenticated one. This tool does not verify Debian's OpenPGP .dsc
signatures; snapshot content hashes and the .dsc checksums bind the bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from beamo_wipe.verification_evidence import verify_package_inventory  # noqa: E402

SCHEMA = "beamo-wipe-corresponding-source/1"
SNAPSHOT = "https://snapshot.debian.org"
NWIPE_TARBALL = "https://codeload.github.com/martijnvanbrummelen/nwipe/tar.gz/{commit}"
BEAMO_TARBALL = "https://codeload.github.com/BeamoTech/beamo-wipe/tar.gz/{commit}"
CHUNK = 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024 * 1024
MAX_METADATA_BYTES = 8 * 1024 * 1024
ATTEMPTS = 3

SOURCE_NAME_RE = re.compile(r"[a-z0-9][a-z0-9+.-]+")
VERSION_RE = re.compile(r"[0-9][A-Za-z0-9.+~:-]*")
SOURCE_FIELD_RE = re.compile(r"(?P<name>[a-z0-9][a-z0-9+.-]+)(?: \((?P<version>[^()\s]+)\))?")
HEX40_RE = re.compile(r"[0-9a-f]{40}")
SHA1_RE = re.compile(r"[0-9a-f]{40}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")
FILE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9+.~_-]*")


class SourceError(RuntimeError):
    pass


def _source_of(entry: Mapping[str, Any]) -> tuple[str, str]:
    """Return (source name, source version) for one dpkg inventory entry."""
    name, version = entry["name"], entry["version"]
    field = entry.get("source") or ""
    if field:
        match = SOURCE_FIELD_RE.fullmatch(field)
        if not match:
            raise SourceError(f"unparseable Source field for {name!r}: {field!r}")
        source = match.group("name")
        version = match.group("version") or version
    else:
        source = name.split(":", 1)[0]
    if not SOURCE_NAME_RE.fullmatch(source) or not VERSION_RE.fullmatch(version):
        raise SourceError(f"invalid source identity for {name!r}: {source} {version}")
    return source, version


def plan(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    """Derive the deterministic corresponding-source set from a manifest."""
    inventory = manifest.get("installed_packages")
    if not isinstance(inventory, Mapping) or inventory.get("measured") is not True:
        raise SourceError("manifest has no measured package inventory")
    inventory = verify_package_inventory(inventory)
    source = manifest.get("source") or {}
    nwipe = manifest.get("nwipe") or {}
    commit = source.get("commit", "")
    if not HEX40_RE.fullmatch(commit or "") or source.get("dirty"):
        raise SourceError("manifest source commit is missing or dirty")
    if not HEX40_RE.fullmatch(nwipe.get("commit", "") or "") or not nwipe.get("version"):
        raise SourceError("manifest has no pinned nwipe commit")
    if inventory.get("source_commit") != commit:
        raise SourceError("package inventory belongs to another source commit")
    groups: Dict[tuple[str, str], List[str]] = {}
    for entry in inventory["packages"]:
        groups.setdefault(_source_of(entry), []).append(f"{entry['name']}:{entry['arch']}")
    debian = [
        {"name": name, "version": version, "binaries": sorted(binaries)}
        for (name, version), binaries in sorted(groups.items())
    ]
    return {
        "schema": SCHEMA,
        "beamo_wipe_version": manifest.get("beamo_wipe_version", ""),
        "beamo_wipe": {"commit": commit, "repository": "https://github.com/BeamoTech/beamo-wipe"},
        "nwipe": {
            "version": nwipe["version"],
            "commit": nwipe["commit"],
            "upstream": "https://github.com/martijnvanbrummelen/nwipe",
        },
        "inventory_sha256": inventory["inventory_sha256"],
        "binary_package_count": inventory["package_count"],
        "debian_source_count": len(debian),
        "debian_sources": debian,
    }


Opener = Callable[[str], Any]


def _default_open(url: str) -> Any:
    if not url.startswith("https://"):
        raise SourceError(f"refusing non-HTTPS URL: {url}")
    request = Request(url, headers={"User-Agent": "beamo-wipe-corresponding-source/1"})
    return urlopen(request, timeout=120)  # noqa: S310 - HTTPS enforced above


def _fetch(open_url: Opener, url: str, limit: int) -> bytes:
    last: Optional[BaseException] = None
    for attempt in range(ATTEMPTS):
        try:
            with open_url(url) as response:
                data = response.read(limit + 1)
            if len(data) > limit:
                raise SourceError(f"download exceeds {limit} bytes: {url}")
            return data
        except SourceError:
            raise
        except OSError as exc:
            last = exc
            time.sleep(2 * (attempt + 1))
    raise SourceError(f"download failed after {ATTEMPTS} attempts: {url}: {last}")


def _snapshot_files(open_url: Opener, name: str, version: str) -> List[tuple[str, str]]:
    """Return [(file name, sha1)] for one source package version on snapshot."""
    url = (f"{SNAPSHOT}/mr/package/{quote(name, safe='')}/{quote(version, safe='')}"
           "/srcfiles?fileinfo=1")
    try:
        info = json.loads(_fetch(open_url, url, MAX_METADATA_BYTES))
    except ValueError as exc:
        raise SourceError(f"snapshot returned invalid JSON for {name} {version}") from exc
    files: Dict[str, str] = {}
    for item in info.get("result", []):
        digest = item.get("hash", "")
        if not SHA1_RE.fullmatch(digest):
            raise SourceError(f"snapshot returned an invalid hash for {name} {version}")
        names = {entry.get("name") for entry in info.get("fileinfo", {}).get(digest, [])}
        if len(names) != 1:
            raise SourceError(f"snapshot file name is ambiguous for {name} {version}")
        (file_name,) = names
        if not isinstance(file_name, str) or not FILE_NAME_RE.fullmatch(file_name):
            raise SourceError(f"snapshot returned an unsafe file name for {name} {version}")
        if files.get(file_name, digest) != digest:
            raise SourceError(f"snapshot lists {file_name} twice for {name} {version}")
        files[file_name] = digest
    if not any(file_name.endswith(".dsc") for file_name in files):
        raise SourceError(f"snapshot has no .dsc for {name} {version}")
    return sorted(files.items())


def _dsc_checksums(text: str) -> Dict[str, tuple[str, int]]:
    """Parse Checksums-Sha256 from a .dsc (clearsigned or not)."""
    out: Dict[str, tuple[str, int]] = {}
    in_field = False
    for line in text.splitlines():
        if line.startswith("Checksums-Sha256:"):
            in_field = True
            continue
        if in_field:
            if not line.startswith(" "):
                break
            parts = line.split()
            if len(parts) != 3 or not SHA256_RE.fullmatch(parts[0]) or not parts[1].isdigit():
                raise SourceError("malformed Checksums-Sha256 line in .dsc")
            out[parts[2]] = (parts[0], int(parts[1]))
    if not out:
        raise SourceError(".dsc has no Checksums-Sha256 field")
    return out


def _write_new(path: Path, data: bytes) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)


def _git_archive(commit: str) -> Optional[bytes]:
    """Beamo Wipe source at commit from this checkout, without evidence archives."""
    try:
        subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{commit}^{{commit}}"],
                       check=True, capture_output=True)
        result = subprocess.run(
            ["git", "-C", str(ROOT), "archive", "--format=tar.gz",
             f"--prefix=beamo-wipe-{commit}/", commit, "--", ".", ":(exclude)docs/evidence"],
            check=True, capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout


def fetch(sources: Mapping[str, Any], dest: Path, *, open_url: Opener = _default_open,
          git_archive: Callable[[str], Optional[bytes]] = _git_archive) -> Dict[str, Any]:
    """Download and verify every source file into a new directory."""
    if sources.get("schema") != SCHEMA:
        raise SourceError("not a corresponding-source plan")
    os.mkdir(dest, 0o755)  # refuses an existing path, including a symlink
    if not stat.S_ISDIR(os.lstat(dest).st_mode):
        raise SourceError("destination is not a new directory")
    records: List[Dict[str, Any]] = []

    def keep(relative: str, data: bytes, origin: str) -> None:
        path = dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_new(path, data)
        records.append({"path": relative, "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(), "origin": origin})

    for package in sources["debian_sources"]:
        name, version = package["name"], package["version"]
        if not SOURCE_NAME_RE.fullmatch(name) or not VERSION_RE.fullmatch(version):
            raise SourceError(f"invalid source identity in plan: {name} {version}")
        folder = f"debian/{name}_{version.replace(':', '%3A')}"
        downloaded: Dict[str, bytes] = {}
        for file_name, sha1 in _snapshot_files(open_url, name, version):
            data = _fetch(open_url, f"{SNAPSHOT}/file/{sha1}", MAX_FILE_BYTES)
            if hashlib.sha1(data).hexdigest() != sha1:  # noqa: S324 - snapshot's content id
                raise SourceError(f"snapshot content hash mismatch: {file_name}")
            downloaded[file_name] = data
        dscs = [file_name for file_name in downloaded if file_name.endswith(".dsc")]
        if len(dscs) != 1:
            raise SourceError(f"expected one .dsc for {name} {version}, found {len(dscs)}")
        expected = _dsc_checksums(downloaded[dscs[0]].decode("utf-8", "replace"))
        if set(expected) != set(downloaded) - {dscs[0]}:
            raise SourceError(f".dsc file list does not match snapshot for {name} {version}")
        for file_name, (digest, size) in expected.items():
            data = downloaded[file_name]
            if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
                raise SourceError(f".dsc checksum mismatch: {file_name}")
        for file_name, data in sorted(downloaded.items()):
            keep(f"{folder}/{file_name}", data, f"{SNAPSHOT} {name} {version}")

    nwipe = sources["nwipe"]
    keep(f"upstream/nwipe-{nwipe['version']}-{nwipe['commit']}.tar.gz",
         _fetch(open_url, NWIPE_TARBALL.format(commit=nwipe["commit"]), MAX_FILE_BYTES),
         f"{nwipe['upstream']} {nwipe['commit']}")
    commit = sources["beamo_wipe"]["commit"]
    archive = git_archive(commit)
    origin = f"git archive {commit} (excluding docs/evidence)"
    if archive is None:
        archive = _fetch(open_url, BEAMO_TARBALL.format(commit=commit), MAX_FILE_BYTES)
        origin = f"{BEAMO_TARBALL.format(commit=commit)}"
    keep(f"upstream/beamo-wipe-{commit}.tar.gz", archive, origin)
    keep("SOURCES.json", _canonical(sources), "corresponding-source plan")
    receipt = {"schema": SCHEMA + "/archive", "plan_sha256": hashlib.sha256(_canonical(sources)).hexdigest(),
               "files": sorted(records, key=lambda item: item["path"])}
    _write_new(dest / "ARCHIVE.json", _canonical(receipt))
    sums = "".join(f"{item['sha256']}  {item['path']}\n" for item in receipt["files"])
    _write_new(dest / "SHA256SUMS", sums.encode("ascii"))
    return receipt


def _canonical(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("ascii")


def _read_json(path: Path) -> Any:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise SourceError(f"not a regular file: {path}")
        data = handle.read(MAX_METADATA_BYTES + 1)
    if len(data) > MAX_METADATA_BYTES:
        raise SourceError(f"file too large: {path}")
    return json.loads(data)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    sub = parser.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan", help="derive the source set from a verified manifest")
    plan_cmd.add_argument("manifest", type=Path)
    plan_cmd.add_argument("--out", type=Path, required=True)
    fetch_cmd = sub.add_parser("fetch", help="download and verify every source file")
    fetch_cmd.add_argument("sources", type=Path)
    fetch_cmd.add_argument("dest", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "plan":
            result = plan(_read_json(args.manifest))
            _write_new(args.out, _canonical(result))
            print(f"{result['debian_source_count']} Debian source packages for "
                  f"{result['binary_package_count']} installed binaries, plus nwipe "
                  f"{result['nwipe']['version']} and Beamo Wipe {result['beamo_wipe']['commit'][:12]}")
        else:
            receipt = fetch(_read_json(args.sources), args.dest)
            print(f"{len(receipt['files'])} files verified into {args.dest}")
    except (SourceError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
