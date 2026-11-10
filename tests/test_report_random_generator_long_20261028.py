# SPDX-License-Identifier: GPL-3.0-or-later
"""The report keeps "Random data generator" after a many-hour erase.

nwipe logs its options manifest once, at the start. After hours of progress
records the exported 1 MiB tail no longer reaches it; the whole-log
projection the outcome is assessed from now keeps those exact records.
Fake log files only.
"""

from __future__ import annotations

import pytest

from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.engine_checks import check_payloads
from beamo_wipe.evidence import build_evidence
from beamo_wipe.models import MethodId, WipeResult
from beamo_wipe.nwipe_runner import (
    NWIPE_COMPLETION_LOG_BYTES,
    NWIPE_OPTIONS_HEADER_RE,
    NWIPE_PRNG_AUTO_RE,
    NWIPE_PRNG_OPTION_RE,
    NwipeRunner,
    completion_for_method,
    evaluate_nwipe_outcome,
    logged_random_generator,
)
from beamo_wipe.outcomes import VIEWS, present_evidence
from test_report_random_generator_20261027 import HEADER, STAMP, auto_line, manifest, prng_line
from test_result_presentations import ERASED, STATUS

# One unrelated engine record per line; enough of them to push the manifest
# out of the exported tail, as hours of progress records do.
FILLER = f"{STAMP}  notice: Hours of progress records go here, padding the log...\n"


def _long_run(tmp_path, head: str):
    wiz = make_demo_wizard()
    disk = wiz.selectable[0]
    repeats = NWIPE_COMPLETION_LOG_BYTES // len(FILLER) + 64
    log = head + FILLER * repeats + STATUS + ERASED.format(name=disk.name, path=disk.path) + "\n"
    logfile = tmp_path / "nwipe.log"
    logfile.write_text(log)
    runner = NwipeRunner()
    tail = runner._read_log_tail(str(logfile), NWIPE_COMPLETION_LOG_BYTES)
    assert runner._log_read_state.truncated
    projection = runner._scan_completion_log(
        str(logfile), disk.path, runner._log_read_state.identity
    )
    assert projection is not None
    return wiz, disk, log, tail, projection


def _evidence(wiz, disk, method, tail, projection):
    ok, detail, reason = evaluate_nwipe_outcome(0, projection, disk.path)
    return build_evidence(
        disk=disk,
        discovery=wiz.discovery,
        method=method,
        request=None,
        result=WipeResult(ok, 0, detail, "", reason),
        started_at_wall="",
        ended_at_wall="",
        started_mono=0,
        ended_mono=1,
        argv=[],
        log_text=tail,
        assessment_log_text=projection,
    )


@pytest.mark.parametrize("method", [MethodId.EVERYDAY, MethodId.EXTRA])
@pytest.mark.parametrize("auto", [None, "XORoshiro-256"])
def test_long_erase_keeps_the_generator_from_the_whole_log(tmp_path, method, auto):
    wiz, disk, log, tail, projection = _long_run(tmp_path, manifest("XORoshiro-256", auto=auto))
    # The exported tail lost the manifest; the projection kept it exactly.
    assert HEADER not in tail and logged_random_generator(tail) is None
    assert logged_random_generator(projection) == "XORoshiro-256"
    ev = _evidence(wiz, disk, method, tail, projection)
    assert ev["nwipe"]["prng"] == "XORoshiro-256"
    # Display only: outcome, completion and media checks are unchanged by
    # the retained generator records.
    records = (NWIPE_OPTIONS_HEADER_RE, NWIPE_PRNG_OPTION_RE, NWIPE_PRNG_AUTO_RE)
    plain = "".join(
        line + "\n" for line in projection.splitlines()
        if not any(regex.fullmatch(line) for regex in records)
    )
    assert plain != projection
    assert check_payloads(projection, disk.path) == check_payloads(plain, disk.path)
    assert completion_for_method(0, projection, disk.path, method) == completion_for_method(
        0, plain, disk.path, method
    )
    assert present_evidence(ev) == VIEWS["verified"]


def test_long_erase_with_two_manifests_stays_unknown(tmp_path):
    # A second options record anywhere in the whole log still means unknown.
    head = manifest("XORoshiro-256") + prng_line("SplitMix64") + "\n"
    wiz, disk, _, tail, projection = _long_run(tmp_path, head)
    assert logged_random_generator(projection) is None
    ev = _evidence(wiz, disk, MethodId.EVERYDAY, tail, projection)
    assert "prng" not in ev["nwipe"]


def test_long_erase_contradicting_auto_selection_stays_unknown(tmp_path):
    head = manifest("XORoshiro-256", auto="SplitMix64")
    wiz, disk, _, tail, projection = _long_run(tmp_path, head)
    assert auto_line("SplitMix64") in projection
    ev = _evidence(wiz, disk, MethodId.EVERYDAY, tail, projection)
    assert "prng" not in ev["nwipe"]


def test_zero_fill_long_erase_never_records_a_generator(tmp_path):
    wiz, disk, _, tail, projection = _long_run(tmp_path, manifest("XORoshiro-256"))
    ev = _evidence(wiz, disk, MethodId.QUICK_ZERO, tail, projection)
    assert "prng" not in ev["nwipe"]
