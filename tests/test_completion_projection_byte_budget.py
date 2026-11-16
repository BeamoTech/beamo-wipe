"""The final sample and collision witness remain inside the projection budget."""

import pytest

from beamo_wipe import nwipe_runner as module


@pytest.mark.parametrize("malformed", [False, True])
@pytest.mark.parametrize("short_by", [0, 1])
def test_last_progress_insertion_obeys_budget(tmp_path, monkeypatch, malformed, short_by):
    first = "/dev/sda: 010.00%, round 1 of 1, pass 1 of 1, eta 00:00:01, [writing]\n"
    last = ("/dev/sda: 010.00%, round 1 of 1, pass 1 of\n" if malformed else
            "/dev/sda: 100.00%, round 1 of 1, pass 1 of 1, eta 00:00:00, [verifying]\n")
    budget = len((first+last).encode()) - short_by
    monkeypatch.setattr(module, "NWIPE_COMPLETION_EVIDENCE_BYTES", budget)
    logfile = tmp_path / "engine.log"
    logfile.write_text(first+"ordinary diagnostic message\n"+last)
    projected = module.NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", module._log_signature(logfile.stat()),
    )
    if short_by:
        assert projected is None
    else:
        assert projected == first+last
        assert len(projected.encode()) <= budget


@pytest.mark.parametrize("short_by", [0, 1])
def test_collision_witness_obeys_budget(tmp_path, monkeypatch, short_by):
    target, other = "/dev/nvme0n100", "/dev/xnvme0n100"
    assert module.nwipe_status_device_field(target) == module.nwipe_status_device_field(other)
    witness = f"observed {other}\n"
    budget = len(witness.encode()) - short_by
    monkeypatch.setattr(module, "NWIPE_COMPLETION_EVIDENCE_BYTES", budget)
    logfile = tmp_path / "engine.log"
    logfile.write_text(witness)
    projected = module.NwipeRunner()._scan_completion_log(
        str(logfile), target, module._log_signature(logfile.stat()),
    )
    assert projected == (None if short_by else witness)


@pytest.mark.parametrize("deferred", [False, True])
@pytest.mark.parametrize("fill", [b"x", b"\xff", "é".encode()])
@pytest.mark.parametrize("short_by", [0, 1])
def test_normalized_projection_obeys_budget(tmp_path, monkeypatch, deferred, fill, short_by):
    if deferred:
        first = b"/dev/sda: 010.00%, round 1 of 1, eta 00:00:01, [writing]\n"
        last = b"/dev/sda: 100.00%, round 1 of 1, pass 1 of " + fill * 31 + b"\n"
        data = first + b"ordinary diagnostic\n" + last
        expected = (first + last).decode("utf-8", errors="replace")
    else:
        data = b"***" + fill * 31 + b"\n***" + fill * 23 + b"\n"
        expected = data.decode("utf-8", errors="replace")
    budget = len(expected.encode("utf-8")) - short_by
    monkeypatch.setattr(module, "NWIPE_COMPLETION_EVIDENCE_BYTES", budget)
    logfile = tmp_path / "engine.log"
    logfile.write_bytes(data)
    projected = module.NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", module._log_signature(logfile.stat()),
    )
    assert projected == (None if short_by else expected)
    if projected is not None:
        assert len(projected.encode("utf-8")) <= budget


@pytest.mark.parametrize("fill", [b"x", b"\xff"])
def test_replacement_expansion_cannot_exceed_default_budget(tmp_path, fill):
    data = (b"***" + fill * 65532 + b"\n") * 16
    assert len(data) == module.NWIPE_COMPLETION_EVIDENCE_BYTES
    logfile = tmp_path / "engine.log"
    logfile.write_bytes(data + b"diagnostic\n")
    projected = module.NwipeRunner()._scan_completion_log(
        str(logfile), "/dev/sda", module._log_signature(logfile.stat()),
    )
    if fill == b"\xff":
        assert projected is None
    else:
        assert projected == data.decode("utf-8")
