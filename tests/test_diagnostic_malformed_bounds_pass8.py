"""Malformed diagnostic bytes must produce the documented safe refusal."""

import json

import pytest

from beamo_wipe import diagnostic_report as diagnostic
from beamo_wipe.models import DiscoveryResult
from beamo_wipe.safety import SafetyError


def _report():
    return json.loads(diagnostic.create_report(
        "discovery_failed", DiscoveryResult(error="fixture"),
        ui="console", session_started=0,
    ))


@pytest.mark.parametrize("elapsed", [10**400, -(10**400)], ids=["huge-positive", "huge-negative"])
def test_diagnostic_oversized_elapsed_is_a_safe_refusal(elapsed):
    report = _report()
    report["time"]["session_elapsed_seconds"] = elapsed
    with pytest.raises(SafetyError, match=diagnostic.INVALID_REPORT):
        diagnostic.validate_report(json.dumps(report).encode())


@pytest.mark.parametrize("wrapper", ["array", "object"])
def test_diagnostic_deep_json_is_a_safe_refusal(wrapper):
    if wrapper == "array":
        data = b'[' * 2000 + b'0' + b']' * 2000
    else:
        data = b'{"nested":' * 1000 + b'0' + b'}' * 1000
    assert len(data) <= diagnostic.MAX_BYTES
    with pytest.raises(SafetyError, match=diagnostic.INVALID_REPORT):
        diagnostic.validate_report(data)


def test_diagnostic_decoder_recursion_is_a_safe_refusal(monkeypatch):
    def exhausted(*_args, **_kwargs):
        raise RecursionError("fixture parser nesting limit")

    monkeypatch.setattr(diagnostic.json, "loads", exhausted)
    with pytest.raises(SafetyError, match=diagnostic.INVALID_REPORT):
        diagnostic.validate_report(b"{}")


@pytest.mark.parametrize("elapsed", [None, 0, 1, 1.25, 10**100])
def test_finite_elapsed_remains_supported(elapsed):
    report = _report()
    report["time"]["session_elapsed_seconds"] = elapsed
    encoded = json.dumps(report).encode()
    assert diagnostic.validate_report(encoded) == report
