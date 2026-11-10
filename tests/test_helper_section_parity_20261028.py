# SPDX-License-Identifier: GPL-3.0-or-later
"""Every offline helper language keeps the English page's structure.

The helper pages are hand-translated copies of ``helper/index.html``. A
translation that condenses a section (merged steps, no illustration, no
technical note with the BitLocker warning, no way back to the problem list)
silently drops guidance. Each page is split on its ``id="..."`` attributes and
compared with English section by section; only the words may differ.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

HELPER = Path(__file__).resolve().parents[1] / "helper"
ENGLISH = "index.html"
TRANSLATED = sorted(p.name for p in HELPER.glob("*.html") if p.name != ENGLISH)

_ID = re.compile(r'\sid="([^"]+)"')
_SVG = re.compile(r"<svg[\s>].*?</svg>", re.S)
_LINK = re.compile(r'href="(#[^"]*)"')
COUNTED = {
    "<p>": re.compile(r"<p[\s>]"),
    "<li>": re.compile(r"<li[\s>]"),
    "<svg>": re.compile(r"<svg[\s>]"),
    "<details>": re.compile(r"<details[\s>]"),
    "<figcaption>": re.compile(r"<figcaption[\s>]"),
    "back link": re.compile(r'class="back"'),
}

# Intentional differences, as extra elements in every translated page.
EXTRA_IN_TRANSLATIONS = {
    # The "This USB" card adds one paragraph saying the boot menu and the
    # kiosk recovery screen stay English (docs/translations.md).
    "usb-build-label": {"<p>": 1},
}


def _read(name: str) -> str:
    return (HELPER / name).read_text(encoding="utf-8")


def _sections(html: str) -> dict[str, str]:
    """Map each id to the markup from that id up to the next id."""
    marks = list(_ID.finditer(html))
    return {
        mark.group(1): html[
            mark.start() : marks[i + 1].start() if i + 1 < len(marks) else len(html)
        ]
        for i, mark in enumerate(marks)
    }


def _counts(section: str) -> dict[str, int]:
    return {name: len(pattern.findall(section)) for name, pattern in COUNTED.items()}


def _stylesheet(html: str) -> str:
    return html.split("<style>", 1)[1].split("</style>", 1)[0]


def test_every_shipped_language_is_checked():
    assert {"fr.html", "de.html", "es.html", "it.html"} <= set(TRANSLATED)


@pytest.mark.parametrize("name", TRANSLATED)
def test_translated_helper_has_the_english_section_ids_in_order(name):
    assert list(_sections(_read(name))) == list(_sections(_read(ENGLISH)))


@pytest.mark.parametrize("name", TRANSLATED)
def test_translated_helper_sections_keep_the_english_structure(name):
    english = _sections(_read(ENGLISH))
    translated = _sections(_read(name))
    mismatches = []
    for section_id, markup in english.items():
        wanted = _counts(markup)
        for element, extra in EXTRA_IN_TRANSLATIONS.get(section_id, {}).items():
            wanted[element] += extra
        found = _counts(translated.get(section_id, ""))
        if found != wanted:
            mismatches.append(f"{section_id}: English {wanted}, {name} {found}")
    assert not mismatches, "\n".join(mismatches)


@pytest.mark.parametrize("name", TRANSLATED)
def test_translated_helper_keeps_illustrations_and_in_page_links(name):
    # Illustrations are language-neutral: the same SVG bytes in each section.
    # In-page links point at the same sections in the same places.
    english = _sections(_read(ENGLISH))
    translated = _sections(_read(name))
    for section_id, markup in english.items():
        local = translated.get(section_id, "")
        assert _SVG.findall(local) == _SVG.findall(markup), section_id
        assert sorted(_LINK.findall(local)) == sorted(_LINK.findall(markup)), section_id


@pytest.mark.parametrize("name", TRANSLATED)
def test_translated_helper_shares_the_english_stylesheet(name):
    # The guide panels, illustrations, technical notes and back links are
    # styled (and the unchosen panels hidden) by the same rules as English.
    assert _stylesheet(_read(name)) == _stylesheet(_read(ENGLISH))
