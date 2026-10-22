"""Malformed local probe JSON must retain the doctor's structured result."""

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "operation", ["local", "test-native", "preview-web", "desktop"]
)
@pytest.mark.parametrize(
    "payload_kind", ["deep-array", "deep-object", "valid", "malformed", "wrong-type"]
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
        "valid": json.dumps(
            {
                "version": [3, 12, 0],
                "modules": {"venv": True, "pip": True, "pytest": True, "qrcode": True},
            }
        ),
        "malformed": '{"version":',
        "wrong-type": '{"version":"3.12.0","modules":{}}',
    }
    calls = []

    def probe(argv, **kwargs):
        calls.append(argv)
        if argv[-1] == "version":
            return "go version go1.26.8 linux/amd64\n", None
        return payloads[payload_kind], None

    monkeypatch.setattr(dev, "doctor_probe", probe)
    result = dev.doctor(operation)
    output = capsys.readouterr()
    report = json.loads(output.out)
    assert output.err == ""
    assert len(calls) == (2 if operation == "desktop" else 1)
    assert report["operation"] == operation
    if payload_kind == "valid":
        assert result == 0 and report["status"] == "ok"
        assert report["problems"] == []
    else:
        assert result == 2 and report["status"] == "blocked"
        assert "returned invalid probe output" in " ".join(report["problems"])
        assert "Repair or recreate its environment" in " ".join(report["problems"])
