"""CI evidence operations stay bound to one link-free directory inode."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
import sys

import pytest

from beamo_wipe import ci_evidence


ROOT = Path(__file__).resolve().parents[1]


def _swap_directory_after_validation(
    monkeypatch: pytest.MonkeyPatch,
    directory: Path,
    *,
    copy_contents: bool = False,
) -> tuple[Path, Path]:
    """Swap after the old validator or the new pinned opener returns."""
    moved = directory.with_name(directory.name + "-opened")
    replacement = directory

    if hasattr(ci_evidence, "_open_evidence_directory"):
        original = ci_evidence._open_evidence_directory

        def swapped(path, *args, **kwargs):
            descriptor = original(path, *args, **kwargs)
            if Path(path) == directory and not moved.exists():
                directory.rename(moved)
                replacement.mkdir()
                if copy_contents:
                    for child in moved.iterdir():
                        shutil.copy2(child, replacement / child.name)
            return descriptor

        monkeypatch.setattr(ci_evidence, "_open_evidence_directory", swapped)
    else:
        original = ci_evidence._require_evidence_directory

        def swapped(path, *args, **kwargs):
            result = original(path, *args, **kwargs)
            if Path(path) == directory and not moved.exists():
                directory.rename(moved)
                replacement.mkdir()
                if copy_contents:
                    for child in moved.iterdir():
                        shutil.copy2(child, replacement / child.name)
            return result

        monkeypatch.setattr(ci_evidence, "_require_evidence_directory", swapped)
    return moved, replacement


def test_json_writer_rejects_linked_parent_without_writing_outside(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="parent|safely|evidence"):
        ci_evidence._write(linked / "receipt.json", {"untrusted": True})

    assert list(outside.iterdir()) == []


def test_gate_rejects_directory_replacement_after_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "evidence"
    moved, replacement = _swap_directory_after_validation(monkeypatch, evidence)

    with pytest.raises(RuntimeError, match="evidence directory.*changed"):
        ci_evidence.run_gate(
            "preview",
            [sys.executable, "-c", "print('descriptor-bound output')"],
            root=ROOT,
            evidence_dir=evidence,
            build_id="local",
        )

    assert moved.is_dir()
    assert list(replacement.iterdir()) == []


def test_gate_child_cannot_redirect_junit_by_replacing_directory(
    tmp_path: Path,
) -> None:
    evidence = tmp_path / "evidence"
    moved = tmp_path / "opened-evidence"
    command = [
        sys.executable,
        "-c",
        (
            "import os,pathlib,sys; "
            "evidence=pathlib.Path(sys.argv[1]); "
            "evidence.rename(sys.argv[2]); evidence.mkdir(); "
            "pathlib.Path(os.environ['BEAMO_GATE_JUNIT']).write_text("
            "'<testsuite tests=\"1\"><testcase name=\"bound\"/></testsuite>')"
        ),
        str(evidence),
        str(moved),
    ]

    with pytest.raises(RuntimeError, match="evidence directory.*changed"):
        ci_evidence.run_gate(
            "tests",
            command,
            root=ROOT,
            evidence_dir=evidence,
            build_id="local",
        )

    assert (moved / "tests.xml").is_file()
    assert list(evidence.iterdir()) == []


def test_gate_rejects_hardlinked_junit_report(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    outside = tmp_path / "outside.xml"
    outside.write_text(
        '<testsuite tests="1"><testcase name="hardlinked"/></testsuite>'
    )
    command = [
        sys.executable,
        "-c",
        "import os,sys; os.link(sys.argv[1], os.environ['BEAMO_GATE_JUNIT'])",
        str(outside),
    ]

    with pytest.raises(RuntimeError, match="JUnit.*unsafe|safely read.*JUnit"):
        ci_evidence.run_gate(
            "tests",
            command,
            root=ROOT,
            evidence_dir=evidence,
            build_id="local",
        )

    assert outside.read_text().endswith("</testsuite>")


def test_gate_rejects_hardlinked_execution_log(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    outside = tmp_path / "second-log-name"
    command = [
        sys.executable,
        "-c",
        "import os,sys; os.link(sys.argv[1], sys.argv[2]); print('linked')",
        str(evidence / "preview.log"),
        str(outside),
    ]

    with pytest.raises(RuntimeError, match="execution log changed"):
        ci_evidence.run_gate(
            "preview",
            command,
            root=ROOT,
            evidence_dir=evidence,
            build_id="local",
        )

    assert outside.read_bytes() == b"linked\n"


def test_receipt_loader_rejects_directory_replacement_after_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = tmp_path / "evidence"
    ci_evidence.run_gate(
        "preview",
        [sys.executable, "-c", "print('trusted receipt')"],
        root=ROOT,
        evidence_dir=evidence,
        build_id="local",
    )
    moved, replacement = _swap_directory_after_validation(
        monkeypatch, evidence, copy_contents=True
    )

    with pytest.raises(RuntimeError, match="evidence directory.*changed"):
        ci_evidence.load_receipts(evidence)

    assert json.loads((moved / "preview.receipt.json").read_text())["gate"] == "preview"
    assert (replacement / "preview.receipt.json").is_file()


def test_receipt_loader_rejects_hardlinked_receipt(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence"
    ci_evidence.run_gate(
        "preview",
        [sys.executable, "-c", "print('trusted receipt')"],
        root=ROOT,
        evidence_dir=evidence,
        build_id="local",
    )
    outside = tmp_path / "second-receipt-name"
    os.link(evidence / "preview.receipt.json", outside)

    with pytest.raises(RuntimeError, match="CI gate receipt"):
        ci_evidence.load_receipts(evidence)

    assert json.loads(outside.read_text())["gate"] == "preview"


def test_summary_rejects_directory_replacement_after_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    evidence = tmp_path / "evidence"
    ci_evidence.run_gate(
        "preview",
        [sys.executable, "-c", "print('trusted summary')"],
        root=ROOT,
        evidence_dir=evidence,
        build_id="local",
    )
    _swap_directory_after_validation(monkeypatch, evidence, copy_contents=True)

    with pytest.raises(RuntimeError, match="evidence directory.*changed"):
        ci_evidence.print_summary(evidence)

    assert "preview: pass" not in capsys.readouterr().out


def test_inventory_rejects_linked_destination_parent(tmp_path: Path) -> None:
    image = tmp_path / "image"
    (image / "var/lib/dpkg").mkdir(parents=True)
    (image / "var/lib/dpkg/status").write_text(
        "Package: base-files\n"
        "Status: install ok installed\n"
        "Version: 1\n"
        "Architecture: amd64\n"
    )
    (image / "etc/apt").mkdir(parents=True)
    (image / "etc/apt/sources.list").write_text(
        "deb https://deb.debian.org/debian stable main\n"
    )
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="parent|safely|evidence"):
        ci_evidence.collect_inventory(image, linked / "packages.json", "a" * 40)

    assert list(outside.iterdir()) == []


@pytest.mark.parametrize("input_name", ["status", "sources"])
def test_inventory_rejects_hardlinked_host_input(
    tmp_path: Path, input_name: str
) -> None:
    image = tmp_path / "image"
    status = image / "var/lib/dpkg/status"
    sources = image / "etc/apt/sources.list"
    status.parent.mkdir(parents=True)
    sources.parent.mkdir(parents=True)
    fixtures = {
        "status": (
            "Package: base-files\n"
            "Status: install ok installed\n"
            "Version: 1\n"
            "Architecture: amd64\n"
        ),
        "sources": "deb https://deb.debian.org/debian stable main\n",
    }
    for name, path in (("status", status), ("sources", sources)):
        if name == input_name:
            outside = tmp_path / ("host-" + name)
            outside.write_text(fixtures[name])
            os.link(outside, path)
        else:
            path.write_text(fixtures[name])

    with pytest.raises(RuntimeError, match="image inventory input"):
        ci_evidence.collect_inventory(
            image, tmp_path / "packages.json", "a" * 40
        )

    assert not (tmp_path / "packages.json").exists()


def test_qemu_hashes_reject_linked_parent(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    evidence = outside / "qemu-evidence"
    evidence.mkdir(parents=True)
    (evidence / "serial.log").write_text("QEMU fixture")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(outside, target_is_directory=True)

    with pytest.raises(RuntimeError, match="QEMU evidence"):
        ci_evidence.qemu_evidence_hashes(linked_parent / "qemu-evidence")


def test_qemu_hashes_reject_hardlinked_file(tmp_path: Path) -> None:
    evidence = tmp_path / "qemu-evidence"
    evidence.mkdir()
    host_file = tmp_path / "host-log"
    host_file.write_text("host data")
    os.link(host_file, evidence / "serial.log")

    with pytest.raises(RuntimeError, match="non-regular"):
        ci_evidence.qemu_evidence_hashes(evidence)
