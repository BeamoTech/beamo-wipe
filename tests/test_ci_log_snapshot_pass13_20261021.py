"""A gate receipt binds the retained execution log to the emitted bytes."""
import hashlib
import os
from pathlib import Path
import sys

import pytest

from beamo_wipe import ci_evidence


@pytest.mark.parametrize("gate", ["lint", "preview"])
@pytest.mark.parametrize("exit_code", [0, 7])
@pytest.mark.parametrize(
    "mutation", ["normal", "rewrite", "restored-mtime", "grow", "truncate", "replace", "symlink", "mode", "link"]
)
def test_gate_cannot_publish_a_changed_execution_log(
    tmp_path, monkeypatch, gate, exit_code, mutation
):
    directory = tmp_path / "evidence"
    logfile = directory / (gate + ".log")
    real_stat = os.stat
    injected = False
    original = b"original\n"
    foreign = tmp_path / "foreign"
    foreign.write_bytes(b"unrelated bytes must survive")

    def stat_after_gate(path, *args, **kwargs):
        nonlocal injected
        if path == logfile and not injected:
            injected = True
            before = real_stat(path)
            if mutation in {"rewrite", "restored-mtime"}:
                logfile.write_bytes(b"tampered\n")
                if mutation == "restored-mtime":
                    os.utime(logfile, ns=(before.st_atime_ns, before.st_mtime_ns))
            elif mutation == "grow":
                logfile.write_bytes(original + b"extra")
            elif mutation == "truncate":
                logfile.write_bytes(b"")
            elif mutation == "replace":
                replacement = tmp_path / "replacement"
                replacement.write_bytes(original)
                os.replace(replacement, logfile)
            elif mutation == "symlink":
                logfile.unlink()
                logfile.symlink_to(foreign)
            elif mutation == "mode":
                logfile.chmod(0o644 if before.st_mode & 0o777 != 0o644 else 0o600)
            elif mutation == "link":
                os.link(logfile, tmp_path / "extra-name")
        return real_stat(path, *args, **kwargs)

    monkeypatch.setattr(os, "stat", stat_after_gate)

    def run():
        return ci_evidence.run_gate(
            gate,
            [sys.executable, "-c", f"print('original'); raise SystemExit({exit_code})"],
            root=Path(__file__).resolve().parents[1],
            evidence_dir=directory,
            build_id="local",
        )

    if mutation == "normal":
        receipt = run()
        assert receipt["status"] == ("pass" if exit_code == 0 else "fail")
        assert receipt["log_sha256"] == hashlib.sha256(original).hexdigest()
        assert logfile.read_bytes() == original
    else:
        with pytest.raises(RuntimeError, match="execution log changed"):
            run()
        assert not (directory / (gate + ".receipt.json")).exists()
    assert injected
    assert foreign.read_bytes() == b"unrelated bytes must survive"
