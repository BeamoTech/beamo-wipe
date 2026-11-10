# SPDX-License-Identifier: GPL-3.0-or-later
"""Physical acceptance packet #116 stays honest, consistent and linked.

Docs and regular temporary files only. Nothing here opens a disk, runs nwipe,
or fills a matrix row. The embedded cold-readback scanner is exercised only
in its --rehearsal mode on files under pytest's tmp_path; the disk seeder is
exercised only on inputs it refuses before writing anything.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
PACKET = DOCS / "acceptance" / "physical"
MATRIX_MD = PACKET / "matrix.md"
MATRIX_CSV = PACKET / "matrix.csv"
PROCEDURES = PACKET / "procedures.md"
FORMS = ("machine-intake.md", "test-run-record.md", "cold-readback.md", "sign-off.md")

HEADER = (
    "ID",
    "Area",
    "Preconditions / hardware",
    "Procedure",
    "Expected result",
    "Evidence required",
    "Status",
    "Virtual or CI evidence (does not count)",
)
STATUSES = {"NOT TESTED", "Pass", "Fail", "Excluded", "BLOCKED", "Unknown"}
NEEDS_RUN = {"Pass", "Fail", "Unknown"}
ID_RE = re.compile(r"^PHY-[A-Z0-9]+-\d{2}$")
# #111 owns these prefixes; #116 must not reuse them.
PREFIXES_111 = {"FW", "MON", "PORT", "USB", "KB", "TP", "AUD", "PWR", "DESK", "DEST"}
RUN_RE = re.compile(r"\brun: RUN-\d{8}-\d{2}\b")
FILE_RE = re.compile(
    r"\b[\w./-]+\.(?:jpg|jpeg|png|txt|log|json|md|mp4|webm|wav|ogg|m4a)\b"
)
VIRTUAL_RE = re.compile(
    r"qemu|ovmf|seabios|qcow2|virtual machine|\bvm\b|virtio|xvfb|preview|"
    r"hosted ci|github actions|blacksmith|fixture|rehearsal|simulat",
    re.IGNORECASE,
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _md_rows() -> list[list[str]]:
    lines = _read(MATRIX_MD).splitlines()
    start = lines.index("## Matrix")
    rows = []
    for line in lines[start:]:
        if not line.startswith("| "):
            continue
        cells = [
            c.strip().replace("\\|", "|")
            for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]
        ]
        rows.append(cells)
    assert rows[0] == list(HEADER)
    assert set(rows[1]) == {"---"}
    return rows[2:]


def _csv_rows() -> list[list[str]]:
    with MATRIX_CSV.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == list(HEADER)
    return rows[1:]


def _slug(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def _anchors(path: Path) -> set[str]:
    return {
        _slug(line.lstrip("#"))
        for line in _read(path).splitlines()
        if re.match(r"^#{1,6} ", line)
    }


def _embedded(sentinel: str, end: str) -> str:
    text = _read(PROCEDURES)
    after = text.split(f"<!-- {sentinel} -->", 1)[1]
    body = after.split("\n", 3)[3]  # skip the blank, ```sh and python3 lines
    return body.split(f"\n{end}\n", 1)[0] + "\n"


def test_packet_files_exist():
    for name in ("README.md", "matrix.md", "matrix.csv", "procedures.md"):
        assert (PACKET / name).is_file(), name
    for name in FORMS:
        assert (PACKET / "forms" / name).is_file(), name


def test_markdown_and_csv_matrices_match():
    md, rows = _md_rows(), _csv_rows()
    assert md == rows
    assert len(rows) >= 100


def test_ids_are_unique_well_formed_and_do_not_reuse_111_prefixes():
    ids = [row[0] for row in _csv_rows()]
    assert len(ids) == len(set(ids))
    for id_ in ids:
        assert ID_RE.match(id_), id_
        assert id_.split("-")[1] not in PREFIXES_111, id_


def test_every_row_is_complete_and_has_a_known_status():
    for row in _csv_rows():
        assert len(row) == len(HEADER), row[0]
        assert all(cell.strip() for cell in row), row[0]
        assert row[6] in STATUSES, (row[0], row[6])


def test_results_need_a_physical_run_and_evidence():
    """A row leaves NOT TESTED only with a run ID and an evidence file,
    and a Pass never cites virtual or CI evidence."""
    for row in _csv_rows():
        status, evidence = row[6], row[5]
        if status in NEEDS_RUN:
            assert RUN_RE.search(evidence), (
                f"{row[0]}: {status} needs 'run: RUN-YYYYMMDD-NN'"
            )
            assert FILE_RE.search(evidence.split("run:", 1)[1]), (
                f"{row[0]}: {status} needs an evidence file"
            )
        if status == "Pass":
            filled = evidence.split("run:", 1)[1]
            assert not VIRTUAL_RE.search(filled), (
                f"{row[0]}: Pass cites virtual evidence: {filled}"
            )


def test_every_row_names_virtual_evidence_that_does_not_count():
    for row in _csv_rows():
        assert len(row[7]) >= 10, row[0]


def test_procedure_links_resolve():
    anchors = _anchors(PROCEDURES)
    for row in _csv_rows():
        targets = re.findall(r"\]\(procedures\.md#([^)]+)\)", row[3])
        assert targets or "](../../" in row[3], row[0]
        for target in targets:
            assert target in anchors, (row[0], target)


def test_required_areas_are_covered():
    ids = {row[0] for row in _csv_rows()}
    prefixes = {id_.rsplit("-", 1)[0] for id_ in ids}
    for needed in (
        "PHY-MFG",
        "PHY-WIN",
        "PHY-LNX",
        "PHY-DISK",
        "PHY-EXCL",
        "PHY-ERASE",
        "PHY-COLD",
        "PHY-RPT",
        "PHY-INT",
        "PHY-A11Y",
        "PHY-LAY",
        "PHY-KIOSK",
    ):
        assert needed in prefixes, needed
    text = _read(MATRIX_CSV)
    for needle in (
        "FAT32",
        "exFAT",
        "VMD",
        "SmartScreen",
        "Restart to boot options",
        "Everyday",
        "Three overwrites",
        "Quick zero",
        "High contrast",
        "1024×600",
        "eMMC",
        "NVMe",
        "legacy BIOS",
        "Secure Boot enforcing",
    ):
        assert needle in text, needle


def test_every_launcher_brand_has_firmware_rows_with_its_current_key():
    """desktop/bootkeys.json is the one key table (#184). A key change there
    must be reflected in the matrix's PHY-<brand>-01 row."""
    table = json.loads(_read(ROOT / "desktop" / "bootkeys.json"))
    rows = {row[0]: row for row in _csv_rows()}
    for brand in table["brands"]:
        if not brand.get("launcher", True):
            continue
        name = brand["name"]
        brand_rows = [r for r in rows.values() if r[1] == f"Firmware: {name}"]
        assert len(brand_rows) == 4, name
        key_row = next(r for r in brand_rows if r[0].endswith("-01"))
        for key in brand["keys"]:
            assert key in key_row[2], (name, key)
        if brand.get("join") == "then":
            assert "then" in key_row[2], name


def test_readme_states_rules_tiers_order_filing_and_blockers():
    text = _read(PACKET / "README.md")
    for needle in (
        "NOT TESTED",
        "Never use a valuable disk",
        "DISPOSABLE",
        "SHA-256",
        "post-flash readback",
        "virtual never fills a physical row",
        "## Result words",
        "## Order of work",
        "## Filing results",
        "## Stays BLOCKED until a human runs it with hardware",
        "If it cannot be identified, no",
        "five-second countdown",
    ):
        assert needle in text, needle


def test_forms_ask_for_redaction_and_physical_hardware():
    intake = _read(PACKET / "forms" / "machine-intake.md")
    assert "last 4 characters" in intake
    assert "customer data" in intake
    run = _read(PACKET / "forms" / "test-run-record.md")
    assert "Physical hardware?" in run and "must be Yes" in run
    assert "SHA-256" in run
    cold = _read(PACKET / "forms" / "cold-readback.md")
    assert "warm read" in cold and "virtual disk" in cold
    sign = _read(PACKET / "forms" / "sign-off.md")
    assert "No row was filled from QEMU" in sign


def test_relative_links_in_the_packet_resolve():
    evidence_present = (DOCS / "evidence").is_dir()
    for path in PACKET.rglob("*.md"):
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", _read(path)):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not evidence_present and (DOCS / "evidence") in resolved.parents:
                continue  # sparse checkout without docs/evidence
            assert resolved.exists(), (path.name, target)


def test_existing_docs_link_to_the_packet():
    for name in (
        "desktop-hardware-acceptance.md",
        "evidence-tiers.md",
        "manufacturing.md",
        "secure-boot-acceptance.md",
        "restart-boot-options.md",
        "boot-keys.md",
        "storage-and-controller-limits.md",
        "live-session-power.md",
        "kiosk-recovery.md",
        "screen-reader.md",
        "qemu-verify.md",
        "remote-development.md",
    ):
        assert "acceptance/physical/" in _read(DOCS / name), name


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-", *args],
        input=script,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


@pytest.fixture(scope="module")
def scanner() -> str:
    return _embedded("cold-readback-scanner", "PY_SCAN")


def test_scanner_zero_mode_passes_only_all_zero(scanner, tmp_path):
    zero = tmp_path / "zero.bin"
    zero.write_bytes(bytes(3 * 1024 * 1024 + 7))
    done = _run(scanner, "zero", str(zero), "--rehearsal")
    assert done.returncode == 0, done.stderr
    assert "COLD READBACK ZERO: PASS" in done.stdout
    assert "REHEARSAL" in done.stdout and "never qualifies" in done.stdout
    dirty = tmp_path / "dirty.bin"
    data = bytearray(2 * 1024 * 1024)
    data[1024 * 1024 + 3] = 1
    dirty.write_bytes(bytes(data))
    done = _run(scanner, "zero", str(dirty), "--rehearsal")
    assert done.returncode == 1
    assert f"offset {1024 * 1024 + 3}" in done.stdout


def test_scanner_finds_a_marker_across_a_chunk_boundary(scanner, tmp_path):
    marker = "BEAMO-SEED-RUN-20270115-01"
    data = bytearray(3 * 1024 * 1024)
    at = 1024 * 1024 - 9
    data[at : at + len(marker)] = marker.encode()
    disk = tmp_path / "seeded.bin"
    disk.write_bytes(bytes(data))
    present = _run(scanner, "present", str(disk), marker, "--rehearsal")
    assert present.returncode == 0 and "Marker hits: 1" in present.stdout
    absent = _run(scanner, "absent", str(disk), marker, "--rehearsal")
    assert absent.returncode == 1 and "COLD READBACK ABSENT: FAIL" in absent.stdout


def test_scanner_refuses_without_qualifying_input(scanner, tmp_path):
    regular = tmp_path / "plain.bin"
    regular.write_bytes(bytes(4096))
    for args in (
        ("zero", str(regular)),  # regular file without --rehearsal
        ("absent", str(regular), "SHORT", "--rehearsal"),  # marker too short
        ("bogus", str(regular)),
        ("zero", str(tmp_path / "missing.bin"), "--rehearsal"),
    ):
        done = _run(scanner, *args)
        assert done.returncode == 2, args
        assert "STOP:" in done.stderr and "PASS" not in done.stdout


def test_seeder_refuses_before_writing(tmp_path):
    seeder = _embedded("seed-disposable-disk", "PY_SEED")
    busy = tmp_path / "busy"
    busy.mkdir()
    (busy / "keep.txt").write_text("x", encoding="utf-8")
    empty = tmp_path / "empty"
    empty.mkdir()
    for args in ((str(busy), "BEAMO-SEED-RUN-20270115-01"), (str(empty), "SHORT")):
        done = _run(seeder, *args)
        assert done.returncode == 2 and "STOP:" in done.stderr, args
    assert sorted(p.name for p in busy.iterdir()) == ["keep.txt"]
    assert list(empty.iterdir()) == []
