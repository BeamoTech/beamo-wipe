"""Malformed local probe JSON must retain the doctor's structured result."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]

# A probe payload whose decoding is forced to raise RecursionError on every
# Python version, so the doctor's RecursionError handling is always covered.
FORCED_RECURSION = '{"forced":"recursion"}'


def _decode_raises_recursion(text):
    try:
        json.loads(text)
    except RecursionError:
        return True
    return False


@pytest.mark.parametrize(
    "operation", ["local", "test-native", "preview-web", "desktop"]
)
@pytest.mark.parametrize(
    "payload_kind",
    [
        "deep-array",
        "deep-object",
        "forced-recursion",
        "valid",
        "malformed",
        "wrong-type",
    ],
)
def test_doctor_probe_json_decode_depth(monkeypatch, capsys, operation, payload_kind):
    spec = importlib.util.spec_from_file_location(
        "doctor_decode_pass12", ROOT / "dev.py"
    )
    dev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(dev)
    monkeypatch.setattr(dev, "live_environment", lambda: False)
    monkeypatch.setattr(dev.sys, "platform", "linux")
    monkeypatch.setattr(dev.shutil, "which", lambda name: "/fake/" + name)
    depth = max(20_000, sys.getrecursionlimit() + 100)
    payloads = {
        "deep-array": "[" * depth + "]" * depth,
        "deep-object": '{"version":[3,12,0],"modules":'
        + '{"x":' * depth
        + "null"
        + "}" * depth
        + "}",
        "forced-recursion": FORCED_RECURSION,
        "valid": json.dumps(
            {
                "version": [3, 12, 0],
                "modules": {"venv": True, "pip": True, "pytest": True, "qrcode": True},
            }
        ),
        "malformed": '{"version":',
        "wrong-type": '{"version":"3.12.0","modules":{}}',
    }
    payload = payloads[payload_kind]

    # On Python 3.11 and earlier (CI runs Debian bookworm's 3.11) these depths
    # make json.loads raise RecursionError, and the doctor must report the
    # probe as invalid. Python 3.14.4 decodes them, so there the doctor applies
    # its normal checks to the decoded value. Which happens is taken from this
    # interpreter; 3.11 and earlier must still raise.
    deep = payload_kind in ("deep-array", "deep-object")
    deep_raises = deep and _decode_raises_recursion(payload)
    if deep and sys.version_info < (3, 12):
        assert deep_raises, "Python 3.11 and earlier must raise RecursionError here"

    if payload_kind == "forced-recursion":
        real_loads = json.loads

        def loads(text, *args, **kwargs):
            if text == FORCED_RECURSION:
                raise RecursionError("maximum recursion depth exceeded")
            return real_loads(text, *args, **kwargs)

        monkeypatch.setattr(dev.json, "loads", loads)

    calls = []

    def probe(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == "version":
            return "go version go1.26.11 linux/amd64\n", None
        return payload, None

    monkeypatch.setattr(dev, "doctor_probe", probe)
    result = dev.doctor(operation)
    output = capsys.readouterr()
    report = json.loads(output.out)
    assert output.err == ""
    assert len(calls) == (2 if operation == "desktop" else 1)
    assert report["operation"] == operation
    # Only one combination decodes to a probe result the doctor accepts: the
    # deep object (a valid version plus a modules dict) where the operation
    # checks no modules (desktop), on a Python that decodes it.
    accepted = payload_kind == "valid" or (
        payload_kind == "deep-object" and not deep_raises and operation == "desktop"
    )
    if accepted:
        assert result == 0 and report["status"] == "ok"
        assert report["problems"] == []
    else:
        assert result == 2 and report["status"] == "blocked"
        assert "returned invalid probe output" in " ".join(report["problems"])
        assert "Repair or recreate its environment" in " ".join(report["problems"])
