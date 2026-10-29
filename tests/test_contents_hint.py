# SPDX-License-Identifier: GPL-3.0-or-later
"""Pick-row contents hint: factual wording in every language, shown by the
console, curses and web views. Fake lsblk payloads only; nothing is erased."""

from __future__ import annotations

from dataclasses import replace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import (
    CONTENTS_DATA,
    CONTENTS_SYSTEM,
    CONTENTS_UNKNOWN,
    CONTENTS_WINDOWS,
    Screen,
)

CONTENTS = {
    "/dev/nvme0n1": CONTENTS_WINDOWS,
    "/dev/sda": CONTENTS_DATA,
    "/dev/sdd": CONTENTS_SYSTEM,
}
# Advice or reassurance would steer the owner toward a disk. The hint only
# reports what the partitions show.
STEERING = (
    "erase", "safe", "choose", "pick", "select", "recommend", "should",
    "main", "your ", "not this", "keep", "wipe",
)


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


def _tag(discovery, contents):
    def tag(disk):
        if disk.is_boot:
            return disk
        return replace(disk, contents=contents.get(disk.path, disk.contents))

    return replace(
        discovery,
        disks=tuple(map(tag, discovery.disks)),
        selectable=tuple(map(tag, discovery.selectable)),
    )


def _picker(contents=CONTENTS):
    wiz = make_demo_wizard()
    wiz.discovery = _tag(wiz.discovery, contents)
    wiz.skip_intro()
    wiz.accept_what()
    wiz.set_owner(True)
    wiz.continue_owner()
    assert wiz.screen == Screen.PICK and wiz.selected is None
    return wiz


def test_hint_follows_observed_contents_and_is_silent_when_unknown():
    disk = make_demo_wizard().selectable[0]
    assert C.contents_hint(replace(disk, contents=CONTENTS_WINDOWS)) == C.CONTENTS_HINT_WINDOWS
    assert C.contents_hint(replace(disk, contents=CONTENTS_SYSTEM)) == C.CONTENTS_HINT_SYSTEM
    # "data" only means no system was recognised; saying "No operating
    # system" there would mislabel a legacy-BIOS system disk.
    assert C.contents_hint(replace(disk, contents=CONTENTS_DATA)) == ""
    assert C.contents_hint(replace(disk, contents=CONTENTS_UNKNOWN)) == ""
    assert not hasattr(C, "CONTENTS_HINT_DATA")


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_hint_wording_is_factual_and_translated(code):
    lang.set_language(code)
    hints = (C.CONTENTS_HINT_WINDOWS, C.CONTENTS_HINT_SYSTEM)
    assert len(set(hints)) == 2 and all(hints)
    assert "Windows" in C.CONTENTS_HINT_WINDOWS
    for hint in hints:
        assert "\n" not in hint and len(hint) <= 60
    if code == "en":
        for hint in hints:
            assert not any(word in hint.lower() for word in STEERING), hint
    else:
        for name in ("CONTENTS_HINT_WINDOWS", "CONTENTS_HINT_SYSTEM"):
            assert getattr(C, name) == lang.translated(code, "copy", name)
            assert getattr(C, name) != lang.english("copy", name)


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_curses_pick_blocks_show_the_hint_under_each_disk(code):
    from beamo_wipe.ui.console_wizard import _pick_blocks

    wiz = _picker()
    wiz.set_language(code)
    blocks = _pick_blocks(wiz, 80)
    hints = {C.CONTENTS_HINT_WINDOWS, C.CONTENTS_HINT_SYSTEM}
    seen = set()
    for disk, block in blocks:
        lines = [line.strip() for line in block]
        if disk is None:  # protected boot USB: no contents hint
            assert not hints & set(lines)
            continue
        expected = C.contents_hint(disk)
        if expected:
            assert lines.count(expected) == 1
            seen.add(expected)
        else:
            assert not hints & set(lines)
        assert all(len(line) <= 80 for line in block)
    assert seen == hints


def test_curses_unknown_contents_add_no_line():
    from beamo_wipe.ui.console_wizard import _pick_blocks

    wiz = _picker({path: CONTENTS_UNKNOWN for path in CONTENTS})
    hints = {C.CONTENTS_HINT_WINDOWS, C.CONTENTS_HINT_SYSTEM}
    for _disk, block in _pick_blocks(wiz, 80):
        assert not hints & {line.strip() for line in block}


def test_plain_console_lists_the_hint_with_each_disk(monkeypatch, capsys):
    from beamo_wipe.ui.console_wizard import _plain_loop

    wiz = _picker()
    answers = []

    def fake_input(_prompt=""):
        answers.append(wiz.screen)
        wiz.shutdown()
        return "x"

    monkeypatch.setattr("builtins.input", fake_input)
    _plain_loop(wiz)
    out = capsys.readouterr().out
    assert answers and answers[0] == Screen.PICK
    for hint in (C.CONTENTS_HINT_WINDOWS, C.CONTENTS_HINT_SYSTEM):
        assert out.count(hint) == 1
    assert wiz.selected is None and not wiz.runner.started


def test_gallery_pick_cards_carry_and_render_the_hint(monkeypatch):
    from beamo_wipe import gallery

    original = gallery.discovery_for_scenario
    monkeypatch.setattr(
        gallery, "discovery_for_scenario",
        lambda scenario: _tag(original(scenario), CONTENTS),
    )
    disks = {item["path"]: item for item in gallery._disks_payload("happy")}
    for path, contents in CONTENTS.items():
        expected = {
            CONTENTS_WINDOWS: C.CONTENTS_HINT_WINDOWS,
            CONTENTS_SYSTEM: C.CONTENTS_HINT_SYSTEM,
            CONTENTS_DATA: "",
        }[contents]
        assert disks[path]["contentsHint"] == expected
    boot = [item for item in disks.values() if item["isBoot"]]
    assert boot and all(item["contentsHint"] == "" for item in boot)
    html = gallery.gallery_html()
    assert "d.contentsHint ?" in html and 'class="small muted contents-hint"' in html


def test_gallery_disk_card_renders_the_hint_line(monkeypatch):
    import json
    import shutil
    import subprocess

    from beamo_wipe import gallery

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable")
    original = gallery.discovery_for_scenario
    monkeypatch.setattr(
        gallery, "discovery_for_scenario",
        lambda scenario: _tag(original(scenario), CONTENTS),
    )
    disks = gallery._disks_payload("happy")
    # The generated preview page has exactly one inline script (our own HTML;
    # this extracts it for inspection, it is not an HTML filter).
    page = gallery.gallery_html()
    assert page.count("<script>") == 1 and page.count("</script>") == 1
    script = page.split("<script>", 1)[1].split("</script>", 1)[0]

    def function(name):
        start = script.index(f"function {name}(")
        depth, index = 0, script.index("{", start)
        while True:
            depth += {"{": 1, "}": -1}.get(script[index], 0)
            if depth == 0:
                return script[start:index + 1]
            index += 1

    program = "\n".join([
        "const P = {bootUsb: 'BOOT', bootDisc: 'DISC'}; let selected = null; const ICON_NO = '';",
        "function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }",
        "function metaLine(d) { return ''; }",
        function("nestedComponents"),
        function("diskCard"),
        f"const disks = {json.dumps(disks)};",
        "console.log(JSON.stringify(disks.map(d => [d.path, "
        "(diskCard(d).match(/contents-hint\">([^<]*)</) || [null, ''])[1]])));",
    ])
    done = subprocess.run([node, "-e", program], capture_output=True, text=True, timeout=30)
    assert done.returncode == 0, done.stderr
    rendered = dict(json.loads(done.stdout))
    for item in disks:
        assert rendered[item["path"]] == item["contentsHint"]
    assert {rendered[path] for path in CONTENTS} == {
        C.CONTENTS_HINT_WINDOWS, C.CONTENTS_HINT_SYSTEM, "",
    }
