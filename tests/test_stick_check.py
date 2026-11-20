# SPDX-License-Identifier: GPL-3.0-or-later
"""Stick check (Ref 183): signed per-file list and a read-only folder comparison.

Regular temporary folders only; no network, device, mount or media write.
"""

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

import pytest

from beamo_wipe import release_signing as signing
from beamo_wipe.usb_media_files import (
    MediaListError,
    list_media_files,
    validate_media_files,
)

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.2.15"
SOURCE = "e986419379f512f8088f5982ee02a51dc91a9dae"
STEM = f"beamo-wipe-{VERSION}-amd64"
STICK_FILES = {
    "EFI/boot/bootx64.efi": b"MZ\x00boot fixture",
    "isolinux/ldlinux.sys": b"syslinux fixture" * 40,
    "live/filesystem.squashfs": b"live filesystem fixture" * 1000,
    ".disk/info": b"Beamo Wipe fixture\n",
    ".disk/base_installable": b"",
    "START-HERE.html": b"<p>fixture</p>\n",
    "Start Beamo Wipe.exe": b"MZ\x00launcher fixture",
}


def _symlink_or_skip(link, target, directory=False):
    try:
        link.symlink_to(target, target_is_directory=directory)
    except (OSError, NotImplementedError) as exc:
        if directory and sys.platform == "win32":
            # Unprivileged Windows can still make a junction (a reparse point).
            import _winapi

            _winapi.CreateJunction(str(target), str(link))
            return
        pytest.skip(f"symlinks unavailable here: {exc}")


@pytest.fixture
def checker():
    spec = importlib.util.spec_from_file_location(
        "check_beamo_stick", ROOT / "scripts/check-beamo-stick.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_tree(root, files):
    for name, data in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


@pytest.fixture
def release(tmp_path):
    private, public = signing.generate_keypair()  # Test key only, never written.
    registry = tmp_path / "trusted-keys.json"
    fingerprint = signing.fingerprint(public)
    registry.write_text(
        json.dumps(
            {
                "schema": signing.KEYS_SCHEMA,
                "keys": {
                    signing.key_id(public): {
                        "fingerprint": fingerprint,
                        "public_key": base64.b64encode(public).decode(),
                        "status": "active",
                    }
                },
            }
        )
    )
    stick = tmp_path / "stick"
    _write_tree(stick, STICK_FILES)
    downloads = tmp_path / "downloads"
    downloads.mkdir()
    meta = {
        "schema_version": 2,
        "image": STEM + ".img",
        "size": 4096,
        "sha256": "a" * 64,
        "iso": STEM + ".iso",
        "iso_sha256": "b" * 64,
        "layout": "MBR, one active FAT32 partition at sector 2048",
        "files": list_media_files(stick),
    }
    inventory = {
        "schema": "beamo-wipe-release-downloads/1",
        "beamo_wipe_version": VERSION,
        "source_commit": SOURCE,
        "qualified_build_id": "12345678-1234-1234-1234-123456789abc",
        "files": {STEM + ".img": {"bytes": 4096, "sha256": "a" * 64}},
    }

    def resign(signed_meta=None):
        data = json.dumps(meta, indent=2, sort_keys=True).encode()
        (downloads / (STEM + ".img.json")).write_bytes(data)
        signed_data = data if signed_meta is None else signed_meta
        inventory["files"][STEM + ".img.json"] = {
            "bytes": len(signed_data),
            "sha256": hashlib.sha256(signed_data).hexdigest(),
        }
        payload = json.dumps(inventory).encode()
        (downloads / "release-downloads.json").write_bytes(payload)
        (downloads / "release-downloads.json.sig").write_text(
            json.dumps(signing.sign_manifest_bytes(payload, private))
        )

    resign()
    args = [
        "--directory",
        str(downloads),
        "--registry",
        str(registry),
        "--trusted-key-sha256",
        fingerprint,
        "--version",
        VERSION,
    ]
    return stick, downloads, meta, resign, args


# --- usb_media_files helper -------------------------------------------------


def test_listing_is_deterministic_sorted_and_hashes_bytes(tmp_path):
    first, second = tmp_path / "a", tmp_path / "b"
    _write_tree(first, STICK_FILES)
    _write_tree(second, dict(reversed(list(STICK_FILES.items()))))
    listed = list_media_files(first)
    assert listed == list_media_files(second) == list_media_files(first)
    assert [entry["path"] for entry in listed] == sorted(STICK_FILES)
    for entry in listed:
        data = STICK_FILES[entry["path"]]
        assert entry == {
            "path": entry["path"],
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    # Directories are implied by their files and never listed themselves.
    (first / "empty-folder").mkdir()
    assert list_media_files(first) == listed


@pytest.mark.parametrize("directory", [False, True])
def test_listing_refuses_symlinked_file_and_folder(tmp_path, directory):
    tree = tmp_path / "tree"
    _write_tree(tree, STICK_FILES)
    outside = tmp_path / "outside"
    if directory:
        outside.mkdir()
        (outside / "payload.bin").write_bytes(b"not on the stick")
    else:
        outside.write_bytes(b"not on the stick")
    _symlink_or_skip(tree / "live/linked", outside, directory=directory)
    with pytest.raises(
        MediaListError, match="linked media entry is not allowed: live/linked"
    ):
        list_media_files(tree)


@pytest.mark.skipif(not hasattr(os, "mkfifo"), reason="FIFOs are POSIX-only")
def test_listing_refuses_special_files(tmp_path):
    tree = tmp_path / "tree"
    _write_tree(tree, STICK_FILES)
    os.mkfifo(tree / "pipe")
    with pytest.raises(MediaListError, match="special"):
        list_media_files(tree)


def test_listing_refuses_linked_or_missing_root(tmp_path):
    with pytest.raises(MediaListError):
        list_media_files(tmp_path / "missing")
    (tmp_path / "real").mkdir()
    (tmp_path / "real/file").write_bytes(b"x")
    _symlink_or_skip(tmp_path / "root-link", tmp_path / "real", directory=True)
    with pytest.raises(MediaListError, match="not a real directory"):
        list_media_files(tmp_path / "root-link")


@pytest.mark.parametrize(
    "files",
    [
        [],
        [
            {"path": "b", "bytes": 1, "sha256": "0" * 64},
            {"path": "a", "bytes": 1, "sha256": "0" * 64},
        ],
        [
            {"path": "A", "bytes": 1, "sha256": "0" * 64},
            {"path": "a", "bytes": 1, "sha256": "0" * 64},
        ],
        [
            {"path": "a", "bytes": 1, "sha256": "0" * 64},
            {"path": "a/b", "bytes": 1, "sha256": "0" * 64},
        ],
        [{"path": "../escape", "bytes": 1, "sha256": "0" * 64}],
        [{"path": "/absolute", "bytes": 1, "sha256": "0" * 64}],
        [{"path": "dir\\file", "bytes": 1, "sha256": "0" * 64}],
        [{"path": "C:/file", "bytes": 1, "sha256": "0" * 64}],
        [{"path": "a", "bytes": -1, "sha256": "0" * 64}],
        [{"path": "a", "bytes": True, "sha256": "0" * 64}],
        [{"path": "a", "bytes": 1, "sha256": "0" * 63}],
        [{"path": "a", "bytes": 1, "sha256": "0" * 64, "mode": 1}],
    ],
)
def test_file_list_validation_fails_closed(files):
    with pytest.raises(MediaListError):
        validate_media_files(files)


# --- build-usb-image.sh wiring (source level; the real build needs Linux) ----


def test_builder_records_readback_file_list_in_schema_2_metadata():
    source = (ROOT / "scripts/build-usb-image.sh").read_text()
    block = source.split("<<'PYVERIFY'\n", 1)[1].split("\nPYVERIFY\n", 1)[0]
    assert 'PYTHONPATH="$ROOT/src" python3 - "$TREE" "$STAGED_OUT"' in source
    assert (
        "from beamo_wipe.usb_media_files import list_media_files,validate_media_files"
        in block
    )
    # Links/special files are refused before rglob's is_file() can follow them.
    assert block.index("listed=list_media_files(root)") < block.index(
        "for source in sorted(root.rglob('*')):"
    )
    # The recorded list is the final image's readback, plus the installer's loader.
    assert "if {entry['path'] for entry in listed}!=set(readback_hashes):" in block
    assert (
        "final['isolinux/ldlinux.sys']={'path':'isolinux/ldlinux.sys','bytes':loader_size,'sha256':loader_hash}"
        in block
    )
    write = next(
        line
        for line in block.splitlines()
        if ".img.json" in line and "write_text" in line
    )
    assert "'schema_version':2" in write and "'files':media_files" in write
    for field in (
        "'image':",
        "'sha256':sha",
        "'iso':",
        "'iso_sha256':",
        "'layout':",
        "'size':",
    ):
        assert field in write
    assert block.index("media_files=validate_media_files(") < block.index(write)


# --- check-beamo-stick.py ---------------------------------------------------


def _run(checker, capsys, stick, args, *extra):
    code = checker.main([str(stick), *args, "--json", *extra])
    return code, json.loads(capsys.readouterr().out)


def test_genuine_stick_passes_with_plain_language(checker, release, capsys):
    stick, _downloads, _meta, _resign, args = release
    assert checker.main([str(stick), *args]) == 0
    out = capsys.readouterr().out
    assert "RESULT: GENUINE AND UNMODIFIED" in out
    assert f"matches the signed Beamo Wipe {VERSION} release file for file" in out
    assert "does not prove the stick hardware is genuine" in out
    code, receipt = _run(checker, capsys, stick, args, "--expected-source", SOURCE)
    assert code == 0 and receipt["verdict"] == "GENUINE AND UNMODIFIED"
    assert receipt["files_checked"] == len(STICK_FILES)
    assert receipt["missing"] == receipt["changed"] == receipt["extra"] == []


def test_case_differences_on_fat_are_not_changes(checker, release, capsys):
    stick, *_rest, args = release
    (stick / "EFI").rename(stick / "efi-tmp")
    (stick / "efi-tmp").rename(stick / "efi")
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 0, receipt


@pytest.mark.parametrize(
    "damage, field, expected",
    [
        (
            "same-size",
            "changed",
            [{"path": "live/filesystem.squashfs", "reason": "contents differ"}],
        ),
        ("size", "changed", [{"path": "START-HERE.html", "reason": "size differs"}]),
        (
            "empty-file",
            "changed",
            [{"path": ".disk/base_installable", "reason": "size differs"}],
        ),
        ("missing", "missing", ["EFI/boot/bootx64.efi"]),
        ("missing-folder", "missing", [".disk/base_installable", ".disk/info"]),
        ("extra", "extra", ["autorun.inf"]),
        ("extra-nested", "extra", ["new/folder/payload.sh"]),
        (
            "folder-for-file",
            "changed",
            [
                {
                    "path": "Start Beamo Wipe.exe",
                    "reason": "not a regular file (link, folder or special file)",
                }
            ],
        ),
        ("hidden-in-os-folder-name", "extra", ["live/Thumbs.db.exe"]),
    ],
)
def test_modified_stick_reports_each_difference(
    checker, release, capsys, damage, field, expected
):
    stick, *_rest, args = release
    if damage == "same-size":
        path = stick / "live/filesystem.squashfs"
        path.write_bytes(b"X" + path.read_bytes()[1:])
    elif damage == "size":
        (stick / "START-HERE.html").write_bytes(b"<p>changed</p>\n<script></script>")
    elif damage == "empty-file":
        (stick / ".disk/base_installable").write_bytes(b"x")
    elif damage == "missing":
        (stick / "EFI/boot/bootx64.efi").unlink()
    elif damage == "missing-folder":
        shutil.rmtree(stick / ".disk")
    elif damage == "extra":
        (stick / "autorun.inf").write_bytes(b"[autorun]\n")
    elif damage == "extra-nested":
        (stick / "new/folder").mkdir(parents=True)
        (stick / "new/folder/payload.sh").write_bytes(b"#!/bin/sh\n")
    elif damage == "folder-for-file":
        (stick / "Start Beamo Wipe.exe").unlink()
        (stick / "Start Beamo Wipe.exe").mkdir()
    elif damage == "hidden-in-os-folder-name":
        (stick / "live/Thumbs.db.exe").write_bytes(b"MZ")
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1 and receipt["verdict"] == "MODIFIED"
    assert receipt[field] == expected
    assert checker.main([str(stick), *args]) == 1
    out = capsys.readouterr().out
    assert "RESULT: MODIFIED" in out and "does NOT match" in out


def test_os_metadata_is_ignored_but_listed(checker, release, capsys):
    stick, *_rest, args = release
    (stick / "System Volume Information").mkdir()
    (stick / "System Volume Information/IndexerVolumeGuid").write_bytes(b"x")
    (stick / "$RECYCLE.BIN").mkdir()
    (stick / ".Spotlight-V100").mkdir()
    (stick / ".fseventsd").mkdir()
    (stick / ".Trashes").mkdir()
    (stick / ".Trash-1000").mkdir()
    (stick / "._START-HERE.html").write_bytes(b"\0\5\26\7")
    (stick / "live/Thumbs.db").write_bytes(b"thumbs")
    (stick / "desktop.ini").write_bytes(b"[.ShellClassInfo]\n")
    (stick / ".DS_Store").write_bytes(b"\0\0\0\1Bud1")
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 0, receipt
    assert receipt["ignored"] == sorted(
        [
            "$RECYCLE.BIN/",
            "._START-HERE.html",
            ".DS_Store",
            ".Spotlight-V100/",
            ".Trash-1000/",
            ".Trashes/",
            ".fseventsd/",
            "System Volume Information/",
            "desktop.ini",
            "live/Thumbs.db",
        ]
    )
    assert checker.main([str(stick), *args]) == 0
    assert "Ignored operating-system files" in capsys.readouterr().out


def test_os_folder_names_below_the_root_are_not_ignored(checker, release, capsys):
    stick, *_rest, args = release
    (stick / "live/System Volume Information").mkdir()
    (stick / "live/System Volume Information/payload").write_bytes(b"x")
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1 and receipt["extra"] == ["live/System Volume Information/payload"]


def test_an_added_empty_folder_is_reported(checker, release, capsys):
    # An empty added folder can still change what the system loads, for
    # example a live-boot layer that hides a file.
    stick, *_rest, args = release
    (stick / "live/zz.dir/usr/bin/nwipe").mkdir(parents=True)
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1 and receipt["verdict"] == "MODIFIED"
    assert receipt["extra"] == ["live/zz.dir/usr/bin/nwipe/"]
    assert receipt["missing"] == receipt["changed"] == []


def test_an_added_folder_holding_only_os_file_names_is_reported(checker, release, capsys):
    stick, *_rest, args = release
    (stick / "live/zz.dir/etc").mkdir(parents=True)
    (stick / "live/zz.dir/etc/desktop.ini").write_bytes(b"payload")
    (stick / "live/zz.dir/etc/._payload.conf").write_bytes(b"payload")
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1 and receipt["verdict"] == "MODIFIED"
    assert receipt["extra"] == ["live/zz.dir/etc/"]
    assert receipt["ignored"] == [
        "live/zz.dir/etc/._payload.conf",
        "live/zz.dir/etc/desktop.ini",
    ]


def test_an_added_folder_is_named_once_beside_its_other_entries(checker, release, capsys):
    stick, *_rest, args = release
    (stick / "new/empty").mkdir(parents=True)
    (stick / "new/payload.sh").write_bytes(b"#!/bin/sh\n")
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1
    # The file names "new/" already; only the empty folder needs its own line.
    assert receipt["extra"] == ["new/empty/", "new/payload.sh"]


def test_symlink_where_a_file_is_expected_is_changed(
    checker, release, capsys, tmp_path
):
    stick, *_rest, args = release
    target = stick / "START-HERE.html"
    copy = tmp_path / "same-bytes.html"
    copy.write_bytes(target.read_bytes())
    target.unlink()
    _symlink_or_skip(target, copy)
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1
    assert receipt["changed"] == [
        {
            "path": "START-HERE.html",
            "reason": "not a regular file (link, folder or special file)",
        }
    ]


def test_symlinked_folder_is_not_followed(checker, release, capsys, tmp_path):
    stick, *_rest, args = release
    moved = tmp_path / "moved-live"
    (stick / "live").rename(moved)
    _symlink_or_skip(stick / "live", moved, directory=True)
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 1
    assert receipt["changed"] == [{"path": "live/", "reason": "expected a folder"}]
    assert receipt["missing"] == ["live/filesystem.squashfs"]


def test_old_schema_release_is_not_verifiable(checker, release, capsys):
    stick, _downloads, meta, resign, args = release
    meta["schema_version"] = 1
    del meta["files"]
    resign()
    code, receipt = _run(checker, capsys, stick, args)
    assert code == 2 and receipt["verdict"] == "NOT VERIFIABLE"
    assert "predates the stick check" in receipt["reason"]
    assert checker.main([str(stick), *args]) == 2
    assert "RESULT: NOT VERIFIABLE" in capsys.readouterr().out


@pytest.mark.parametrize(
    "damage",
    [
        "meta-bytes",
        "signature",
        "inventory",
        "wrong-key",
        "wrong-version",
        "revoked",
        "missing-meta",
        "bad-files",
        "wrong-source",
        "device-path",
        "not-a-folder",
        "missing-signature",
        "replay-older",
    ],
)
def test_untrusted_or_bad_inputs_are_not_verifiable(checker, release, capsys, damage):
    stick, downloads, meta, resign, args = release
    extra = []
    if damage == "meta-bytes":
        # img.json differs from the bytes recorded in the signed release list.
        signed = (downloads / (STEM + ".img.json")).read_bytes()
        meta["files"] = meta["files"][1:]
        resign(signed_meta=signed)
    elif damage == "signature":
        path = downloads / "release-downloads.json.sig"
        data = json.loads(path.read_text())
        data["signature"] = base64.b64encode(b"x" * 64).decode()
        path.write_text(json.dumps(data))
    elif damage == "inventory":
        path = downloads / "release-downloads.json"
        path.write_bytes(path.read_bytes() + b" ")
    elif damage == "wrong-key":
        args[args.index("--trusted-key-sha256") + 1] = "a" * 64
    elif damage == "wrong-version":
        args[args.index("--version") + 1] = "0.2.16"
    elif damage == "revoked":
        registry = Path(args[args.index("--registry") + 1])
        data = json.loads(registry.read_text())
        next(iter(data["keys"].values()))["status"] = "revoked"
        registry.write_text(json.dumps(data))
    elif damage == "missing-meta":
        (downloads / (STEM + ".img.json")).unlink()
    elif damage == "bad-files":
        meta["files"][0]["path"] = "../outside"
        resign()
    elif damage == "wrong-source":
        extra = ["--expected-source", "a" * 40]
    elif damage == "device-path":
        stick = "\\\\.\\PhysicalDrive1" if sys.platform == "win32" else "/dev/sdz"
    elif damage == "not-a-folder":
        stick = stick / "START-HERE.html"
    elif damage == "missing-signature":
        (downloads / "release-downloads.json.sig").unlink()
    elif damage == "replay-older":
        args[args.index("--version") + 1] = "0.2.14"
    code, receipt = _run(checker, capsys, stick, args, *extra)
    assert code == 2 and receipt["verdict"] == "NOT VERIFIABLE", receipt
    assert receipt["reason"]
    assert receipt["missing"] == receipt["changed"] == receipt["extra"] == []


def test_checker_never_writes_to_stick_or_downloads(checker, release, capsys):
    stick, downloads, *_rest, args = release

    def snapshot():
        return {
            p: (p.stat().st_size, p.stat().st_mtime_ns, p.read_bytes())
            for base in (stick, downloads)
            for p in sorted(base.rglob("*"))
            if p.is_file()
        }

    (stick / "extra.txt").write_bytes(b"x")  # Exercise the MODIFIED path too.
    before = snapshot()
    checker.main([str(stick), *args])
    checker.main([str(stick), *args, "--json"])
    capsys.readouterr()
    assert snapshot() == before
    source = (ROOT / "scripts/check-beamo-stick.py").read_text()
    for forbidden in (
        "O_WRONLY",
        "O_RDWR",
        "O_CREAT",
        "write_bytes",
        "write_text",
        "unlink",
        "rmtree",
        '"wb"',
        "'wb'",
        "subprocess",
    ):
        assert forbidden not in source


def test_stick_check_docs_are_honest_and_links_resolve():
    import re

    text = (ROOT / "docs/release-verification.md").read_text(encoding="utf-8")
    section = text.split("## Check a Beamo USB stick\n", 1)[1].split("\n## ", 1)[0]
    for phrase in (
        "scripts\\check-beamo-stick.py E:\\",
        "scripts/check-beamo-stick.py /Volumes/",
        "`GENUINE AND UNMODIFIED` | 0",
        "`MODIFIED` | 1",
        "`NOT VERIFIABLE` | 2",
        "never opens a raw disk",
        "does not check the stick's boot sectors",
        "cannot tell an exact copy",
        "GPL",
        "`schema_version` 2",
    ):
        assert phrase in section, phrase
    assert not re.search(
        r"/dev/|\bsudo\b|\bdd\b|PhysicalDrive|Run as administrator", section
    )
    headings = re.findall(r"^#{1,6} (.+)$", text, re.MULTILINE)
    slugs = {re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings}
    for anchor in re.findall(
        r"\]\(#([^)]+)\)", section + text.split("## What the manifest", 1)[0]
    ):
        assert anchor in slugs, anchor


# --- downstream consumers accept schema 2 ------------------------------------


def test_publisher_accepts_schema_2_and_rejects_bad_file_lists(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "beamo_publisher_stick", ROOT / "scripts/publish_release_gcs.py"
    )
    publisher = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = publisher
    spec.loader.exec_module(publisher)
    good = [
        {"path": ".disk/info", "bytes": 1, "sha256": "0" * 64},
        {"path": "EFI/boot/bootx64.efi", "bytes": 0, "sha256": "f" * 64},
    ]
    assert publisher._usb_media_files(good) == good
    for bad in (
        [],
        None,
        list(reversed(good)),
        [{**good[0], "path": "../x"}],
        [{**good[0], "path": "/x"}],
        [{**good[0], "bytes": -1}],
        [{**good[0], "extra": 1}],
        [{**good[0], "sha256": "x"}],
    ):
        with pytest.raises(publisher.PublishError):
            publisher._usb_media_files(bad)
    assert publisher.MAX_USB_METADATA_BYTES >= 1024 * 1024


def test_signed_inputs_read_reliably_on_this_platform(tmp_path):
    # NTFS can report a different ChangeTime for a handle and its directory
    # entry; the shared reader must not turn that into "changed while read".
    for index in range(40):
        path = tmp_path / f"input-{index}.json"
        path.write_bytes(b'{"fixture": %d}' % index)
        assert (
            signing._read_bytes_file(path, what="fixture") == b'{"fixture": %d}' % index
        )
    assert ("st_ctime_ns" in signing._FILE_METADATA_FIELDS) == (os.name == "posix")


def test_download_verifier_accepts_schema_1_and_2_only():
    source = (ROOT / "scripts/verify-usb-download.py").read_text()
    assert 'meta["schema_version"] not in (1, 2)' in source
    assert 'type(meta["schema_version"]) is not int' in source
