"""Launcher rendering must regenerate fixtures after temporary files disappear."""

from contextlib import nullcontext
from types import SimpleNamespace

import pytest

import test_launcher_readiness as readiness


def test_readiness_fixture_is_recreated_with_a_warm_go_cache(tmp_path, monkeypatch):
    if not readiness.shutil.which("go"):
        pytest.skip("The launcher fixture requires the pinned Go toolchain")
    playwright = pytest.importorskip("playwright.sync_api")
    monkeypatch.delenv("BEAMO_DESKTOP_NATIVE_INVENTORY_TEST", raising=False)
    real_which = readiness.shutil.which
    monkeypatch.setattr(
        readiness.shutil, "which",
        lambda name: "/fake/browser" if name in {"google-chrome", "chromium"} else real_which(name),
    )
    browser = SimpleNamespace(close=lambda: None)
    runtime = SimpleNamespace(chromium=SimpleNamespace(launch=lambda **_kwargs: browser))
    monkeypatch.setattr(playwright, "sync_playwright", lambda: nullcontext(runtime))
    directory = tmp_path / "readiness"
    directory.mkdir()
    # A new container can reuse a pytest temporary path while a mounted Go
    # cache survives. Reuse that path and remove its output between calls.
    factory = SimpleNamespace(mktemp=lambda _name: directory)
    for iteration in range(2):
        fixture = readiness.browser_cases.__wrapped__(factory)
        actual_browser, cases = next(fixture)
        assert actual_browser is browser
        assert {"pass", "partial", "fail", "permission", "timeout", "cancelled"} <= set(cases)
        assert next(fixture, None) is None
        path = directory / "fixtures.json"
        assert path.is_file(), iteration
        path.unlink()
