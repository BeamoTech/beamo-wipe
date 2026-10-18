"""Pass21 proof: accepted diagnostics must survive their own JSONL reader.

Prepared by a source-only delegate. Root must run this before any product fix.
Only regular pytest temporary files and captured stderr are used; no devices,
processes, display, inventory, signals, mounts or external commands are involved.
"""

from __future__ import annotations

import json
import unicodedata

import pytest

from beamo_wipe import diagnostics


@pytest.mark.parametrize("separator", ["\u2028", "\u2029"])
@pytest.mark.parametrize(
    "field",
    ["area", "code", "detail", "device", "logfile", "request_id", "extra_key", "extra_value"],
)
def test_unicode_separator_diagnostic_round_trips(tmp_path, field, separator):
    tmp_path.chmod(0o700)
    value = f"before{separator}after"
    fields = {"area": "audit", "code": "boundary", "detail": "ordinary"}
    if field in {"extra_key", "extra_value"}:
        fields["extra"] = {value: "ordinary"} if field == "extra_key" else {"key": value}
    else:
        fields[field] = value
    assert diagnostics.log_diag(**fields, log_dir=tmp_path) is True
    raw = (tmp_path / "diagnostics.log").read_text(encoding="utf-8")
    # The writer returned success and emitted valid JSON; the exact same
    # committed event must remain available through the supported reader.
    event = json.loads(raw)
    assert diagnostics.read_diagnostics(tmp_path) == [event]


@pytest.mark.parametrize("separator", ["\u2028", "\u2029"])
def test_unicode_separator_is_flattened(separator):
    value = f"before{separator}after"
    sanitized = diagnostics._sanitize_detail(value)
    assert sanitized == "before after"
    assert not any(unicodedata.category(ch) in {"Zl", "Zp"} for ch in sanitized)


@pytest.mark.parametrize("separator", ["\u2028", "\u2029"])
def test_unicode_separator_fallback_is_one_visible_message(separator, tmp_path, capsys):
    value = f"before{separator}after"
    # A missing explicit private directory takes the write-failed fallback.
    # It must still be one visible diagnostic message.
    assert diagnostics.log_diag("audit", "boundary", value, log_dir=tmp_path / "missing") is False
    stderr = capsys.readouterr().err
    assert len(stderr.splitlines()) == 1
    assert "before after" in stderr


@pytest.mark.parametrize("separator", ["\n", "\r", "\t", "\x85", "\x1c", "\x1d", "\x1e", "\x00"])
def test_existing_control_separator_round_trip(tmp_path, separator):
    tmp_path.chmod(0o700)
    assert diagnostics.log_diag("audit", "control", f"before{separator}after", log_dir=tmp_path)
    records = diagnostics.read_diagnostics(tmp_path)
    assert len(records) == 1
    assert records[0]["detail"] == "before after"


def test_normal_unicode_and_event_order_are_preserved(tmp_path):
    tmp_path.chmod(0o700)
    for code, detail in [("first", "Ordinary café text"), ("second", "Disk check complete")]:
        assert diagnostics.log_diag("audit", code, detail, log_dir=tmp_path)
    records = diagnostics.read_diagnostics(tmp_path)
    assert [record["code"] for record in records] == ["first", "second"]
    assert records[0]["detail"] == "Ordinary café text"
    assert diagnostics.read_diagnostics(tmp_path, limit=1) == [records[1]]
