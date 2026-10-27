"""Finalization must retain the QEMU artifact bytes named by its receipt."""
import hashlib
import json
import shutil
import sys

import pytest

from beamo_wipe import ci_evidence
from beamo_wipe import release_manifest as rm
from beamo_wipe.verification_evidence import REQUIRED_GATES, build_gate_receipt, canonical_digest
from test_ci_evidence_pipeline import build_provenance  # noqa: F401


def complete_evidence(root):
    evidence = root / "dist/evidence"
    evidence.mkdir()
    qemu = root / "qemu-evidence"
    qemu.mkdir()
    files = {"summary.txt": b"all fixture guest checks passed\n", "isoinfo.txt": b"fixture ISO\n"}
    for name, raw in files.items():
        (qemu / name).write_bytes(raw)
    hashes = {name: hashlib.sha256(raw).hexdigest() for name, raw in files.items()}
    digest = hashlib.sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    inventory = ci_evidence.build_package_inventory(
        packages=[dict(name="base-files", version="1", arch="amd64")],
        collected_from="squashfs var/lib/dpkg/status", source_commit="a" * 40,
        apt_sources=["https://deb.debian.org/debian"],
    )
    (evidence / "packages.json").write_text(json.dumps(inventory))
    for gate in REQUIRED_GATES:
        log = f"fixture execution of {gate}\n".encode()
        (evidence / f"{gate}.log").write_bytes(log)
        environment = {"runner": "fixture"}
        if gate == "qemu":
            environment["qemu_evidence_sha256"] = digest
        receipt = build_gate_receipt(
            gate=gate, status="pass", command=f"fixture {gate}", source_commit="a" * 40,
            build_id=rm.build_env()["release_build_id"], environment=environment,
            measured=dict(passed=1, failed=0, errors=0, skipped=0, xfailed=0, deselected=0, total=1),
            skips=[], log_sha256=hashlib.sha256(log).hexdigest(),
        )
        (evidence / f"{gate}.receipt.json").write_text(json.dumps(receipt))
    return qemu, evidence


@pytest.mark.parametrize("mutation", ["intact", "delete-summary", "change-summary", "remove-tree",
                                    "extra-file", "wrong-receipt-digest", "missing-receipt-digest"])
def test_finalization_rechecks_recorded_qemu_artifacts(build_provenance, mutation):  # noqa: F811
    root, dest, _iso = build_provenance
    qemu, evidence = complete_evidence(root)
    original_manifest = dest.read_bytes()
    if mutation == "delete-summary":
        (qemu / "summary.txt").unlink()
    elif mutation == "change-summary":
        (qemu / "summary.txt").write_bytes(b"changed fixture bytes\n")
    elif mutation == "remove-tree":
        shutil.rmtree(qemu)
    elif mutation == "extra-file":
        (qemu / "unrecorded.txt").write_bytes(b"unrecorded fixture\n")
    elif mutation in ("wrong-receipt-digest", "missing-receipt-digest"):
        path = evidence / "qemu.receipt.json"
        receipt = json.loads(path.read_text())
        if mutation == "wrong-receipt-digest":
            receipt["environment"]["qemu_evidence_sha256"] = "f" * 64
        else:
            del receipt["environment"]["qemu_evidence_sha256"]
        receipt["receipt_sha256"] = canonical_digest({
            key: value for key, value in receipt.items() if key != "receipt_sha256"
        })
        path.write_text(json.dumps(receipt))
    if mutation == "intact":
        ci_evidence.finalize(root)
        rm.verify_manifest(dest)
    else:
        with pytest.raises(RuntimeError, match="QEMU evidence"):
            ci_evidence.finalize(root)
        assert dest.read_bytes() == original_manifest
        assert not (root / "dist/SHA256SUMS").exists()


def test_successful_qemu_gate_requires_completion_summary(tmp_path, monkeypatch):
    monkeypatch.setattr(ci_evidence.subprocess, "check_output", lambda *_args, **_kwargs: "a" * 40)
    qemu = tmp_path / "qemu-evidence"
    qemu.mkdir()
    (qemu / "isoinfo.txt").write_text("incomplete fixture evidence")
    with pytest.raises(RuntimeError, match="QEMU evidence.*summary"):
        ci_evidence.run_gate("qemu", [sys.executable, "-c", "print('fixture command exited zero')"],
                             root=tmp_path, evidence_dir=tmp_path / "dist/evidence", build_id="local")
