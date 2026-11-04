# SPDX-License-Identifier: GPL-3.0-or-later
"""#153: key-caps in hints look alike and no punctuation dangles after a cap.

The arrow caps (↑ ↓ ← →) used a font glyph that the UI font often lacks; the
fallback came out thin and tinted (orange with subpixel smoothing) beside the
bold ink letter caps. They are now drawn in INK in Tk and as currentColor SVG in
the web preview. "use ↑ ↓ ." came from a sentence ending on a cap with the
cap's 4 px gap before the period: hint copy no longer ends a sentence on a key
in any language, and punctuation that does follow a cap sits against it.
"""

from __future__ import annotations

import re

import pytest

from beamo_wipe import copy as C, lang

FOOTER_TEXTS = ("NO_OUTCOME_RECORDED", "SHUTDOWN_HINT", "POWER_KEEP_CONNECTED")


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _hint_names():
    return sorted(n for n in dir(C) if n.startswith("HINT_")) + list(FOOTER_TEXTS)


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_no_hint_sentence_ends_on_a_key_cap(code):
    from beamo_wipe.ui.tk_wizard import _KEY_TOKEN_RE

    lang.set_language(code)
    for name in _hint_names():
        text = getattr(C, name)
        if not isinstance(text, str):
            continue
        for match in _KEY_TOKEN_RE.finditer(text):
            after = text[match.end():match.end() + 1]
            assert not re.match(r"[.,;:!?]", after), (code, name, text)


def test_pick_and_confirm_copy():
    assert C.HINT_PICK == "Click a disk, or use Up/Down to choose one.  Enter reviews this disk.  Esc goes back."
    assert C.HINT_CONFIRM == "Type exactly what we ask for, then press Enter to continue."


# -- Tk ------------------------------------------------------------------------


@pytest.fixture
def tk_app():
    from test_tk_runtime import _needs_display
    from beamo_wipe.ui.tk_wizard import TkWizard
    from beamo_wipe.wizard import make_demo_wizard

    created = []

    def build(screen="pick", size=(1280, 820)):
        _needs_display()
        wiz = make_demo_wizard()
        wiz.preview = False
        if screen != "keyboard":
            wiz.skip_intro()
            wiz.set_owner(True)
            wiz.continue_owner()
        else:
            wiz.skip_splash()
        app = TkWizard(wiz)
        created.append(app)
        app.root.geometry(f"{size[0]}x{size[1]}+40+40")
        app._draw()
        for _ in range(6):
            app.root.update()
        return wiz, app

    yield build
    for app in created:
        app._teardown()


def _caps(widget):
    from beamo_wipe.ui.tk_wizard import _Box

    found = []

    def walk(node):
        for child in node.winfo_children():
            if isinstance(child, _Box):
                found.append(child)
            else:
                walk(child)

    walk(widget)
    return sorted(found, key=lambda w: w.winfo_rootx())


def _content(cap):
    import tkinter as tk

    (child,) = cap.inner.winfo_children()
    if isinstance(child, tk.Canvas):
        return "glyph", child
    return "label", child


def test_tk_arrow_caps_are_drawn_in_ink_like_the_letter_caps(tk_app):
    from beamo_wipe.ui.tk_wizard import INK, SURFACE

    wiz, app = tk_app()
    caps = _caps(app._hint)
    kinds = [_content(c) for c in caps]
    arrows = [w for kind, w in kinds if kind == "glyph"]
    letters = [w for kind, w in kinds if kind == "label"]
    assert [getattr(a, "_beamo_key_glyph") for a in arrows] == ["up", "down"]
    assert [str(lbl.cget("text")) for lbl in letters] == ["Enter", "Esc"]
    for arrow in arrows:
        (item,) = arrow.find_withtag("glyph")
        assert arrow.itemcget(item, "fill").lower() == INK.lower()
        assert str(arrow.cget("bg")).lower() == SURFACE.lower()
    for label in letters:
        assert str(label.cget("fg")).lower() == INK.lower()
    # No cap shows a typed arrow character any more.
    assert all(str(lbl.cget("text")) not in "↑↓←→" for lbl in letters)
    heights = {c.winfo_height() for c in caps}
    assert max(heights) - min(heights) <= 2, heights


def test_tk_keyboard_hint_draws_left_and_right(tk_app):
    wiz, app = tk_app(screen="keyboard")
    glyphs = [getattr(w, "_beamo_key_glyph") for kind, w in map(_content, _caps(app._hint)) if kind == "glyph"]
    assert glyphs[:2] == ["left", "right"]
    assert "up" in glyphs and "down" in glyphs


def test_tk_pick_hint_has_no_floating_period(tk_app):
    import tkinter as tk

    wiz, app = tk_app()
    pieces = []

    def walk(node):
        for child in node.winfo_children():
            if isinstance(child, tk.Label) and child.master is not None and child not in pieces:
                pieces.append(child)
            walk(child)

    walk(app._hint)
    texts = [str(p.cget("text")) for p in pieces if str(p.cget("text")) not in ("Enter", "Esc")]
    assert texts and not any(t.strip().startswith(".") for t in texts), texts


def test_tk_punctuation_after_a_cap_sits_against_it(tk_app):
    import tkinter as tk

    wiz, app = tk_app()
    bar = app._hint_bar(app._hint.master, "Then press Enter. Esc goes back.")
    bar.pack()
    for _ in range(4):
        app.root.update()
    caps = _caps(bar)
    enter = caps[0]
    period = next(w for w in bar.winfo_children()[0].winfo_children()
                  if isinstance(w, tk.Label) and str(w.cget("text")).startswith("."))
    assert period.winfo_rootx() - (enter.winfo_rootx() + enter.winfo_width()) <= 1
    # A cap followed by a word keeps its gap.
    esc = caps[1]
    after = next(w for w in bar.winfo_children()[0].winfo_children()
                 if isinstance(w, tk.Label) and str(w.cget("text")).startswith(" goes"))
    assert after.winfo_rootx() - (esc.winfo_rootx() + esc.winfo_width()) >= 4


# -- web preview --------------------------------------------------------------


def test_preview_draws_arrow_caps_and_hugs_punctuation():
    from beamo_wipe.gallery import gallery_html

    html = gallery_html()
    assert 'const ARROW_PATHS = {"↑":' in html
    for glyph in "↑↓←→":
        assert f'"{glyph}": "M' in html
    assert 'stroke="currentColor"' in html
    assert 'cap.setAttribute("aria-label", k);' in html
    assert "if (/^[.,;:!?]/.test(text.slice(pos))) el.lastChild.classList.add(\"kbd-hug\");" in html
    assert ".kbd.kbd-arrow svg { display: inline-block; vertical-align: -1px; color: var(--ink); }" in html


@pytest.mark.parametrize("size", [(1024, 740), (1280, 820)])
def test_preview_browser_caps_share_ink_and_no_dangling_period(tmp_path, size):
    import shutil

    from beamo_wipe.gallery import gallery_html

    api = pytest.importorskip("playwright.sync_api")
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        pytest.skip("Chrome unavailable")
    page_file = tmp_path / "index.html"
    page_file.write_text(gallery_html(), encoding="utf-8")
    with api.sync_playwright() as p:
        browser = p.chromium.launch(executable_path=chrome, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": size[0], "height": size[1]})
        page.goto(page_file.as_uri() + "#s=pick&owner=1&disk=0")
        caps = page.evaluate("""() => Array.from(document.querySelectorAll('#hint .kbd')).map(c => {
            const svg = c.querySelector('svg');
            return {svg: !!svg, label: c.getAttribute('aria-label') || c.textContent,
                    color: getComputedStyle(svg || c).color,
                    next: c.nextSibling && c.nextSibling.nodeType === 3 ? c.nextSibling.textContent : ''};
        })""")
        assert [c["label"] for c in caps] == ["↑", "↓", "Enter", "Esc"]
        assert [c["svg"] for c in caps] == [True, True, False, False]
        assert len({c["color"] for c in caps}) == 1
        assert not any(c["next"].startswith(".") for c in caps)
        browser.close()
