"""Restart to boot options in the Windows launcher (#183).

Static checks of the shipped launcher page, script and docs. Nothing here
starts the launcher or any process; this host must never restart.
"""
from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
WEB = ROOT / "desktop" / "web"


def _section() -> str:
    page = (WEB / "index.html").read_text(encoding="utf-8")
    match = re.search(r'<section id="boot-options".*?</section>', page, re.S)
    assert match, "Restart to boot options section missing"
    return match.group(0)


def test_section_is_hidden_until_a_check_offers_it_and_needs_saved_work():
    section = _section()
    assert section.startswith('<section id="boot-options" aria-labelledby="boot-options-title" hidden>')
    assert '<input id="boot-options-saved" type="checkbox">' in section
    assert '<button id="boot-options-restart" class="primary" disabled>Restart to boot options</button>' in section
    assert "Save your work and close your applications" in section


def test_section_explains_the_next_screens_and_bitlocker():
    text = re.sub(r"<[^>]+>", "", _section())
    for phrase in ("Choose an option", "Use a device", "EFI USB Device", "BitLocker recovery key",
                   "changes no startup settings and erases nothing", "boot-menu key below",
                   "You still choose and confirm the disk before anything is erased"):
        assert phrase in text, phrase


def test_page_order_puts_the_restart_before_the_key_fallback():
    page = (WEB / "index.html").read_text(encoding="utf-8")
    assert page.index('id="readiness"') < page.index('id="boot-options"') < page.index('id="boot-key"')


def test_script_sends_only_a_confirmed_reviewed_request():
    app = (WEB / "app.js").read_text(encoding="utf-8")
    calls = re.findall(r'api\("advanced-startup"[^)]*\)', app)
    assert calls == ['api("advanced-startup",true,revision)']
    assert 'if (!bootOptions || !$("boot-options-saved").checked) return;' in app
    assert 'bootOptions = v.advanced_startup === true && v.revision > 0;' in app
    # A check that is not current hides the button again.
    assert '$("boot-options").hidden = true;' in app
    assert "(bootOptions && state.advanced_startup !== true)" in app


def test_go_command_is_the_documented_one_without_force():
    src = (ROOT / "desktop" / "advanced_startup.go").read_text(encoding="utf-8")
    assert 'filepath.Join(windowsDir, "System32", "shutdown.exe"), "/r", "/o", "/t", "0"' in src
    assert '"/f"' not in src and '"/fw"' not in src
    assert "testing.Testing()" in src
    win = (ROOT / "desktop" / "platform_windows.go").read_text(encoding="utf-8")
    body = win.split("func platformAdvancedStartup(", 1)[1]
    assert body.split("\n", 2)[1].strip() == "if err := advancedStartupGuard(); err != nil {"


def test_docs_cover_elevation_bitlocker_fallback_and_not_tested():
    doc = (ROOT / "docs" / "restart-boot-options.md").read_text(encoding="utf-8")
    for phrase in ("Shut down the system", "BitLocker", "Use a device", "EFI USB Device",
                   "NOT TESTED", "learn.microsoft.com/en-us/windows-server/administration/windows-commands/shutdown"):
        assert phrase in doc, phrase
    design = (ROOT / "docs" / "desktop-entry-design.md").read_text(encoding="utf-8")
    assert "restart-boot-options.md" in design


def test_helper_pages_mention_the_option_in_every_language():
    for page, use_a_device in (("index.html", "Use a device"), ("fr.html", "Utiliser un périphérique"),
                               ("de.html", "Ein Gerät verwenden"), ("es.html", "Usar un dispositivo"),
                               ("it.html", "Usa un dispositivo")):
        text = (ROOT / "helper" / page).read_text(encoding="utf-8")
        assert "<strong>Restart to boot options</strong>" in text, page
        assert f"<strong>{use_a_device}</strong>" in text, page
        assert "<strong>EFI USB Device</strong>" in text, page
