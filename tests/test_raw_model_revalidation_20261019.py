# SPDX-License-Identifier: GPL-3.0-or-later
"""A display fallback must not hide changed hardware MODEL at authorization."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from beamo_wipe import nwipe_runner as runner_module
from beamo_wipe.models import MethodId, WipeRequest
from beamo_wipe.safety import (
    SafetyError,
    assert_disk_identity,
    assert_rediscovered_identity,
    disk_identity,
)
from test_discovery_observation_fallback_pass16 import (
    _disk,
    fake_machine,  # noqa: F401 - guarded fake-machine pytest fixture
)


ROUTES = ("direct", "injected", "production-metadata-stub")
SUBJECTS = ("target", "boot")
FALLBACKS = (("Owner Data", "Owner Data"), ("", "Unknown model"))


def _payload(subject, model, label):
    boot = _disk(
        "sdz", tran="usb", size=16_000_000_000,
        mountpoints=["/run/live/medium"],
    )
    target = _disk("sda")
    changed = target if subject == "target" else boot
    changed.update(model=model, label=label)
    return {"blockdevices": [boot, target]}


def _request(discovery, logfile="/tmp/beamo-wipe/fake.log"):
    target = discovery.selectable[0]
    return WipeRequest(
        device=target.path, method=MethodId.EVERYDAY,
        boot_device=discovery.boot.path, logfile=logfile,
        device_rdev=8, boot_rdev=16, device_size_bytes=target.size_bytes,
        device_identity=disk_identity(target),
        boot_identity=disk_identity(discovery.boot),
    )


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("subject", SUBJECTS)
@pytest.mark.parametrize("label,fallback", FALLBACKS)
@pytest.mark.parametrize("reverse", (False, True))
def test_model_fallback_transition_revokes_authorization(
    fake_machine, monkeypatch, route, subject, label, fallback, reverse,  # noqa: F811
):
    models = (fallback, "") if reverse else ("", fallback)
    before = fake_machine(_payload(subject, models[0], label), route)
    after = fake_machine(_payload(subject, models[1], label), route)
    old = before.selectable[0] if subject == "target" else before.boot
    fresh = after.selectable[0] if subject == "target" else after.boot
    assert old.model == fresh.model == fallback
    assert old.raw_model != fresh.raw_model
    assert old.layout_id == fresh.layout_id
    if subject == "target":
        with pytest.raises(SafetyError, match="identity changed"):
            assert_disk_identity(old, after)
    request = _request(before)
    with pytest.raises(SafetyError, match="identity changed"):
        assert_rediscovered_identity(request, after)
    monkeypatch.setattr("beamo_wipe.discover.discover", lambda: after)
    with pytest.raises(SafetyError, match="identity changed"):
        runner_module._recheck_identity_under_lock(request)


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("subject", SUBJECTS)
@pytest.mark.parametrize("model", (None, "", "Owner Data", "Actual model"))
def test_unchanged_raw_model_preserves_authorization(
    fake_machine, route, subject, model,  # noqa: F811
):
    before = fake_machine(_payload(subject, model, "Owner Data"), route)
    after = fake_machine(_payload(subject, model, "Owner Data"), route)
    assert_disk_identity(before.selectable[0], after)
    assert_rediscovered_identity(_request(before), after)


def test_legacy_disks_keep_their_reported_model_identity(fake_machine):  # noqa: F811
    discovery = fake_machine(_payload("target", "Actual model", ""), "direct")
    target = replace(discovery.selectable[0], raw_model=None)
    assert disk_identity(target)[3] == "Actual model"
    assert disk_identity(replace(target, model="Changed model")) != disk_identity(target)
    assert disk_identity(target) == disk_identity(discovery.selectable[0])
    assert disk_identity(replace(target, raw_model="Changed model")) != disk_identity(target)
    assert disk_identity(
        replace(discovery.selectable[0], model="Changed presentation")
    ) != disk_identity(discovery.selectable[0])


@pytest.mark.parametrize("subject", SUBJECTS)
@pytest.mark.parametrize("label,fallback", FALLBACKS)
@pytest.mark.parametrize("changed", (False, True))
def test_real_runner_path_checks_raw_model_before_any_process_spawn(
    fake_machine, tmp_path, monkeypatch, subject, label, fallback, changed,  # noqa: F811
):
    before = fake_machine(_payload(subject, "", label), "production-metadata-stub")
    after = fake_machine(
        _payload(subject, fallback if changed else "", label),
        "production-metadata-stub",
    )
    monkeypatch.setattr("beamo_wipe.discover.discover", lambda: after)
    monkeypatch.setattr("beamo_wipe.safety.default_log_dir", lambda: tmp_path)
    monkeypatch.setattr("beamo_wipe.safety.assert_not_boot", lambda *_a, **_k: None)
    for name in (
        "require_real_live_for_nwipe", "_verify_pinned_nwipe",
        "assert_existing_is_block_device", "assert_size_unchanged",
        "assert_local_device_transport", "assert_not_boot",
    ):
        monkeypatch.setattr(runner_module, name, lambda *_a, **_k: None)
    monkeypatch.setattr(runner_module, "pinned_nwipe_already_running", lambda **_k: False)
    monkeypatch.setattr(
        runner_module, "block_rdev", lambda path: 8 if path == "/dev/sda" else 16,
    )
    spawn = Mock(return_value=SimpleNamespace())
    monkeypatch.setattr(runner_module.subprocess, "Popen", spawn)
    runner = runner_module.NwipeRunner()
    runner._sleep_inhibit = SimpleNamespace(start=lambda: None, stop=lambda: None)
    request = _request(before, str(tmp_path / "fake.log"))
    try:
        if changed:
            with pytest.raises(SafetyError, match="identity changed"):
                runner.start(request)
            spawn.assert_not_called()
            assert runner.start_not_spawned()
        else:
            runner.start(request)
            spawn.assert_called_once()
    finally:
        runner._release_wipe_lock()
