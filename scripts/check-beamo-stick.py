#!/usr/bin/env python3
"""Check a mounted Beamo Wipe USB stick against its signed release, file for file.

Read-only: reads ordinary files under the stick folder you name (for example
E:\\ or /media/usb). It never opens a raw disk device, needs no administrator
rights, and never writes, repairs or deletes anything.
"""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from beamo_wipe.release_signing import (  # noqa: E402
    _read_bytes_file,
    _read_json_file,
    _unique_json_fields,
    load_key_registry,
    verify_release_acceptance,
)
from beamo_wipe.usb_media_files import (  # noqa: E402
    CHUNK,
    is_link_like,
    media_path_key,
    validate_media_files,
)

GENUINE, MODIFIED, NOT_VERIFIABLE = 0, 1, 2
VERDICTS = {
    GENUINE: "GENUINE AND UNMODIFIED",
    MODIFIED: "MODIFIED",
    NOT_VERIFIABLE: "NOT VERIFIABLE",
}
RECEIPT_SCHEMA = "beamo-wipe-stick-check/1"
PLAIN_LIST_LIMIT = 50
# Well-known folders an operating system may add at the top of any stick.
OS_ROOT_FOLDERS = frozenset(
    {
        "system volume information",
        "$recycle.bin",
        ".spotlight-v100",
        ".fseventsd",
        ".trashes",
        ".temporaryitems",
        ".documentrevisions-v100",
    }
)
OS_FILES = frozenset({"thumbs.db", "desktop.ini", ".ds_store"})
LIMITS = (
    "This compares the files in the stick folder with the signed release. It does "
    "not check the stick's boot sectors or space outside its files, does not prove "
    "the stick hardware is genuine or new, and says nothing about any computer. "
    "An exact copy of a genuine stick also passes: copying Beamo Wipe is allowed "
    "under its GPL licence."
)


class NotVerifiable(RuntimeError):
    """The stick cannot be judged: bad inputs, signature, or an older release."""


def _download_verifier():
    # Reuse the download verifier's authenticated size/hash checks unchanged.
    path = Path(__file__).with_name("verify-usb-download.py")
    spec = importlib.util.spec_from_file_location("beamo_verify_usb_download", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def authenticate(directory, registry_path, fingerprint, version, source=None):
    """Verify the signed inventory, then the stick file list it authenticates."""
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise NotVerifiable("version must be X.Y.Z, for example 0.2.15")
    if not re.fullmatch(r"[0-9a-f]{64}", fingerprint):
        raise NotVerifiable(
            "the trusted key fingerprint must be 64 lowercase hex characters"
        )
    if source is not None and not re.fullmatch(r"[0-9a-f]{40}", source):
        raise NotVerifiable(
            "the expected source commit must be 40 lowercase hex characters"
        )
    downloads = _download_verifier()
    directory = Path(os.path.abspath(directory))
    registry = load_key_registry(
        _read_json_file(Path(os.path.abspath(registry_path)), what="trusted registry")
    )
    payload = _read_bytes_file(
        directory / "release-downloads.json", what="release-downloads.json"
    )
    signature = _read_json_file(
        directory / "release-downloads.json.sig", what="detached signature"
    )
    result = verify_release_acceptance(
        payload, signature, registry, min_version=version
    )
    if registry[result["key_id"]]["fingerprint"] != fingerprint:
        raise NotVerifiable(
            "signature key differs from the independently confirmed fingerprint"
        )
    if result["beamo_wipe_version"] != version:
        raise NotVerifiable(
            "the signed release list is for a different Beamo Wipe version"
        )
    inventory = json.loads(payload, object_pairs_hook=_unique_json_fields)
    if inventory["schema"] != "beamo-wipe-release-downloads/1":
        raise NotVerifiable("unsupported signed release list")
    if source is not None and inventory["source_commit"] != source:
        raise NotVerifiable(
            "signed release source differs from the expected source commit"
        )
    stem = f"beamo-wipe-{version}-amd64"
    meta_name = stem + ".img.json"
    meta_bytes = _read_bytes_file(directory / meta_name, what=meta_name)
    downloads.check_bytes(meta_bytes, downloads.record(inventory, meta_name), meta_name)
    meta = json.loads(meta_bytes, object_pairs_hook=_unique_json_fields)
    if not isinstance(meta, dict) or meta.get("image") != stem + ".img":
        raise NotVerifiable("USB image metadata does not describe this release's image")
    schema = meta.get("schema_version")
    if type(schema) is not int:
        raise NotVerifiable("USB image metadata has no valid schema version")
    if schema < 2 or "files" not in meta:
        raise NotVerifiable(
            f"Beamo Wipe {version} predates the stick check: its signed release does "
            "not list the stick's files, so sticks from it cannot be checked this way"
        )
    return {
        "version": version,
        "key_fingerprint": fingerprint,
        "source_commit": inventory["source_commit"],
        "build": inventory["qualified_build_id"],
        "files": validate_media_files(meta["files"]),
    }


def _stick_root(stick):
    text = os.fspath(stick)
    # Device namespaces and device nodes are disks, not folders. Refuse them.
    if re.match(r"^([\\/]{2}[.?][\\/])", text) or re.match(r"^/dev(/|$)", text):
        raise NotVerifiable(
            "give the folder where the stick is opened (like E:\\), not a disk device"
        )
    if re.fullmatch(r"[A-Za-z]:", text):
        text += "\\"  # "E:" alone means the current folder on drive E.
    root = Path(os.path.abspath(text))
    try:
        metadata = os.lstat(root)
    except OSError as exc:
        raise NotVerifiable(f"stick folder cannot be opened: {root}") from exc
    if is_link_like(metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise NotVerifiable(f"stick folder is not an ordinary folder: {root}")
    return root


def _is_os_metadata(name, at_root, is_dir):
    folded = name.casefold()
    if is_dir:
        return at_root and (folded in OS_ROOT_FOLDERS or folded.startswith(".trash-"))
    return folded in OS_FILES or name.startswith("._")


def _same_file(path, expected, before):
    """Return None if the file matches, else a reason. Never follows a link."""
    if before.st_size != expected["bytes"]:
        return "size differs"
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
        | getattr(os, "O_BINARY", 0)
    )
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if not stat.S_ISREG(opened.st_mode):
            return "not a regular file"
        if opened.st_size != expected["bytes"]:
            return "size differs"
        digest = hashlib.sha256()
        count = 0
        while chunk := stream.read(CHUNK):
            count += len(chunk)
            if count > expected["bytes"]:
                return "size differs"
            digest.update(chunk)
    if count != expected["bytes"]:
        return "size differs"
    return None if digest.hexdigest() == expected["sha256"] else "contents differ"


def check_stick(root, files):
    """Compare the folder tree with the authenticated list. Read-only."""
    expected = {media_path_key(entry["path"]): entry for entry in files}
    expected_dirs = set()
    for key in expected:
        parts = key.split("/")
        expected_dirs.update("/".join(parts[:depth]) for depth in range(1, len(parts)))
    seen, to_hash = set(), []
    changed, extra, ignored = [], [], []
    pending = [(root, "")]
    while pending:
        directory, prefix = pending.pop()
        try:
            with os.scandir(directory) as scan:
                children = sorted(scan, key=lambda item: item.name)
        except OSError as exc:
            raise NotVerifiable(
                f"could not read stick folder {prefix or directory}"
            ) from exc
        for child in children:
            rel = prefix + child.name
            key = media_path_key(rel)
            try:
                metadata = child.stat(follow_symlinks=False)
            except OSError as exc:
                raise NotVerifiable(f"could not read stick entry {rel}") from exc
            link = is_link_like(metadata)
            is_dir = stat.S_ISDIR(metadata.st_mode) and not link
            if (
                key not in expected
                and key not in expected_dirs
                and _is_os_metadata(child.name, not prefix, is_dir)
            ):
                ignored.append(rel + "/" if is_dir else rel)
                continue
            if key in seen:  # Same name in another case: FAT cannot hold both.
                extra.append(rel)
                continue
            seen.add(key)
            if key in expected:
                if link or not stat.S_ISREG(metadata.st_mode):
                    changed.append(
                        {
                            "path": expected[key]["path"],
                            "reason": "not a regular file (link, folder or special file)",
                        }
                    )
                else:
                    to_hash.append((expected[key], child.path, metadata))
            elif key in expected_dirs:
                if is_dir:
                    pending.append((child.path, rel + "/"))
                else:
                    changed.append({"path": rel + "/", "reason": "expected a folder"})
            elif is_dir:
                pending.append((child.path, rel + "/"))  # Report the files inside.
            else:
                extra.append(rel)
    for entry, path, metadata in sorted(to_hash, key=lambda item: item[0]["path"]):
        try:
            reason = _same_file(path, entry, metadata)
        except OSError as exc:
            raise NotVerifiable(f"could not read stick file {entry['path']}") from exc
        if reason:
            changed.append({"path": entry["path"], "reason": reason})
    missing = [entry["path"] for key, entry in expected.items() if key not in seen]
    return {
        "files_checked": len(files),
        "missing": sorted(missing),
        "changed": sorted(changed, key=lambda item: item["path"]),
        "extra": sorted(extra),
        "ignored": sorted(ignored),
    }


def run(args):
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "stick": None,
        "release_version": args.version,
        "missing": [],
        "changed": [],
        "extra": [],
        "ignored": [],
        "limits": LIMITS,
    }
    try:
        root = _stick_root(args.stick)
        receipt["stick"] = str(root)
        release = authenticate(
            args.directory,
            args.registry,
            args.trusted_key_sha256,
            args.version,
            args.expected_source,
        )
        receipt.update(
            key_fingerprint=release["key_fingerprint"],
            source_commit=release["source_commit"],
            build=release["build"],
        )
        receipt.update(check_stick(root, release["files"]))
    except (
        NotVerifiable,
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        TypeError,
    ) as exc:
        receipt["reason"] = str(exc) or type(exc).__name__
        code = NOT_VERIFIABLE
    else:
        code = (
            MODIFIED
            if receipt["missing"] or receipt["changed"] or receipt["extra"]
            else GENUINE
        )
    receipt["verdict"] = VERDICTS[code]
    receipt["exit_code"] = code
    return code, receipt


def _print_list(title, items):
    if not items:
        return
    print(f"{title} ({len(items)}):")
    for item in items[:PLAIN_LIST_LIMIT]:
        print(
            "  "
            + (f"{item['path']} - {item['reason']}" if isinstance(item, dict) else item)
        )
    if len(items) > PLAIN_LIST_LIMIT:
        print(
            f"  ... and {len(items) - PLAIN_LIST_LIMIT} more (use --json for the full list)"
        )


def report(code, receipt):
    version = receipt["release_version"]
    print("Beamo Wipe stick check (read-only)")
    print(f"Stick folder: {receipt['stick'] or '(not opened)'}")
    print()
    print(f"RESULT: {receipt['verdict']}")
    if code == GENUINE:
        print(
            f"Every Beamo Wipe file in this stick folder matches the signed Beamo Wipe "
            f"{version} release file for file ({receipt['files_checked']} files checked)."
        )
    elif code == MODIFIED:
        print(
            f"This stick does NOT match the signed Beamo Wipe {version} release. "
            "Do not use it. Make a new stick from the verified official download."
        )
        _print_list("CHANGED", receipt["changed"])
        _print_list("MISSING", receipt["missing"])
        _print_list("EXTRA (not part of the release)", receipt["extra"])
    else:
        print(f"The stick was not judged: {receipt['reason'].rstrip('.')}.")
        print(
            "Nothing here says the stick is good or bad. Check the inputs and try again."
        )
    if receipt["ignored"]:
        print()
        _print_list(
            "Ignored operating-system files (added by a computer, not checked)",
            receipt["ignored"],
        )
    print()
    print(LIMITS)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "stick",
        type=Path,
        help="folder where the stick is opened, e.g. E:\\ or /media/usb",
    )
    parser.add_argument(
        "--directory",
        required=True,
        type=Path,
        help="folder holding release-downloads.json, its .sig and the .img.json",
    )
    parser.add_argument(
        "--registry",
        required=True,
        type=Path,
        help="trusted keys.json from an independently trusted checkout",
    )
    parser.add_argument("--trusted-key-sha256", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument(
        "--expected-source", help="optional 40-hex source commit to require"
    )
    parser.add_argument(
        "--json", action="store_true", help="print a JSON receipt instead of text"
    )
    args = parser.parse_args(argv)
    code, receipt = run(args)
    try:
        sys.stdout.reconfigure(errors="backslashreplace")
    except (AttributeError, ValueError):
        pass
    if args.json:
        print(json.dumps(receipt, indent=2, sort_keys=True))
    else:
        report(code, receipt)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
