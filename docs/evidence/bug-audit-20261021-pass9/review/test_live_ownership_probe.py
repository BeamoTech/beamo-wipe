"""Independent public startup trace: fake metadata and runner only."""
from types import SimpleNamespace

import pytest

from beamo_wipe import app, discover, safety, session_recovery, wizard
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.nwipe_runner import DryRunRunner


@pytest.mark.parametrize("mode", ["transient", "live", "desktop"])
def test_public_live_startup_requires_owned_session_before_discovery(monkeypatch, tmp_path, mode):
    fake = make_demo_wizard().discovery
    events = []
    seen = []
    calls = []
    monkeypatch.delenv("BEAMO_WIPE_DRY_RUN", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_DEMO", raising=False)
    monkeypatch.delenv("BEAMO_WIPE_LIVE", raising=False)
    monkeypatch.setattr(safety.sys, "platform", "linux")
    monkeypatch.setattr(app, "running_on_live_usb", safety.running_on_live_usb)
    monkeypatch.setattr(safety, "default_log_dir", lambda: tmp_path)

    def cmdline(*args, **kwargs):
        calls.append(True)
        if mode == "desktop" or (mode == "transient" and len(calls) == 1):
            return ""
        return "boot=live quiet"

    monkeypatch.setattr(discover, "read_cmdline", cmdline)
    monkeypatch.setattr(discover, "live_medium_is_mounted", lambda **kw: True)
    monkeypatch.setattr(app.signal, "signal", lambda *a: None)

    class Store:
        def open(self): events.append("open")
        def close(self): events.append("close")

    monkeypatch.setattr(session_recovery, "SessionStore", Store)
    monkeypatch.setattr(wizard.Wizard, "enable_session_recovery", lambda self, store: setattr(self, "_session_store", store))
    monkeypatch.setattr(wizard.Wizard, "enable_report_intent_recovery", lambda *a: None)
    monkeypatch.setattr(wizard.Wizard, "set_language", lambda *a: None)

    def inventory(**kwargs):
        events.append("discover")
        return fake

    monkeypatch.setattr(app, "discover", inventory)
    monkeypatch.setattr(app, "NwipeRunner", DryRunRunner)

    def ui(w):
        seen.append(SimpleNamespace(dry=w.dry_run, store=w._session_store))
        return 0

    monkeypatch.setattr("beamo_wipe.ui.console_wizard.run_console", ui)
    monkeypatch.setattr("subprocess.run", lambda *a, **kw: pytest.fail("native process forbidden"))
    monkeypatch.setattr("subprocess.Popen", lambda *a, **kw: pytest.fail("native process forbidden"))
    code = app.main(["--console", "--demo"])
    if mode == "transient":
        assert code == 3 and not seen and "discover" not in events, (code, seen, events)
    elif mode == "live":
        assert code == 0 and len(seen) == 1 and not seen[0].dry and isinstance(seen[0].store, Store)
        assert events == ["open", "discover", "close"]
    else:
        assert code == 0 and len(seen) == 1 and seen[0].dry and seen[0].store is None
        assert events == []
