# SPDX-License-Identifier: GPL-3.0-or-later
"""Translation consistency: placeholders, cited labels, key names, typography.

See docs/translations.md. These checks read the locale tables only; they do
not switch the active language.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from pathlib import Path

import pytest

from beamo_wipe import lang

TRANSLATED = ("fr", "de", "es")
HELPER = Path(__file__).resolve().parents[1] / "helper"

# (citing module, citing name, label module, label name): the English citing
# string names the English label (a button, screen title or section name), so
# every translation must name the translated label. Compared case-insensitively
# because console footers write labels in lower case.
CITED_LABELS = (
    ("copy", "POWER_EVENTS", "copy", "STOP_ASK"),
    ("progress", "STALE_NEXT", "copy", "STOP_ASK"),
    ("copy", "CON_WORKING_IDLE", "copy", "STOP_ASK"),
    ("copy", "CON_WORKING_STOP", "copy", "STOP_KEEP"),
    ("copy", "COUNTDOWN_READY", "copy", "BTN_ERASE"),
    ("copy", "COUNTDOWN_CAPTION", "copy", "BTN_ERASE"),
    ("copy", "HINT_LAST_CHANCE_TK", "copy", "BTN_ERASE"),
    ("copy", "REPORT_HELP_INSERT", "copy", "BTN_SAVE_REPORT"),
    ("copy", "REPORT_INSERT", "copy", "BTN_SAVE_REPORT"),
    ("copy", "ADVANCED_LOG_LEAD", "copy", "BTN_SAVE_REPORT"),
    ("copy", "EXPORT_GUIDE_RETRY", "copy", "BTN_SAVE_REPORT"),
    ("copy", "REPORT_HELP_PLUGGED", "copy", "BTN_REFRESH"),
    ("copy", "REPORT_MEDIA_WANTED", "copy", "BTN_REFRESH"),
    ("copy", "REFRESH_UTILITY_NOTE", "copy", "BTN_REFRESH"),
    ("copy", "CON_REFRESH_ENTER", "copy", "BTN_REFRESH"),
    ("recovery", "NEXT_BLOCKED_REFRESH", "copy", "BTN_REFRESH"),
    ("copy", "ADVANCED_LOG_TAIL", "copy", "REPORT_HELP_TITLE"),
    ("copy", "REPORT_MEDIA_WHAT", "copy", "REPORT_HELP_TITLE"),
    ("copy", "CON_REPORT_HELP", "copy", "REPORT_HELP_TITLE"),
    ("copy", "CON_REPORT_HINT", "copy", "REPORT_HELP_TITLE"),
    ("copy", "MEDIA_STEP_REPORT", "copy", "SHUTDOWN_KEEP"),
    ("copy", "CON_SHUTDOWN_KEEP", "copy", "SHUTDOWN_KEEP"),
    ("copy", "REPORT_HELP_CONTAINS", "copy", "BTN_SHUTDOWN"),
    ("copy", "REPORT_HELP_START", "copy", "DIAGNOSTIC_TITLE"),
    ("copy", "REPORT_HELP_START", "copy", "BTN_PREPARE"),
    ("copy", "CON_DIAGNOSTIC", "copy", "DIAGNOSTIC_TITLE"),
    ("copy", "CON_DIAG_SAVE", "copy", "SAVE_DIAGNOSTIC_REPORT"),
    ("diagnostic_report", "PREPARE", "copy", "BTN_PREPARE"),
    ("support_export", "CANNOT_VERIFY_BOOT", "copy", "BTN_PREPARE"),
    ("support_export", "DISK_CHANGED_PREPARE", "copy", "BTN_PREPARE"),
    ("copy", "DISK_HELP_TEXT", "copy", "BTN_MORE"),
    ("copy", "DISK_HELP_TEXT", "copy", "BTN_BACK"),
    ("copy", "DISK_HELP_TEXT", "copy", "DISK_HELP_STOP"),
    ("copy", "SOUND_VOLUME_LOW", "copy", "SOUND_LOUDER"),
    ("copy", "CON_WHAT_FOOTER", "copy", "BTN_UNDERSTAND"),
    ("copy", "CON_DONE_PREVIEW", "copy", "BTN_RUN_AGAIN"),
    ("copy", "CON_DONE_ANOTHER", "copy", "BTN_ERASE_ANOTHER"),
    ("copy", "CON_KEYBOARD", "copy", "KEYBOARD_UTILITY"),
    ("copy", "CON_METHOD_FOOTER", "copy", "TITLE_ADVANCED"),
    ("copy", "CON_METHOD_PROMPT", "copy", "TITLE_ADVANCED"),
    ("copy", "CON_COMPARE", "inventory", "COMPARE_TITLE"),
    ("copy", "CON_OTHER_DEVICES", "inventory", "TITLE"),
)

# Key names stay English in every language (locale docstrings).
KEY_NAMES = (
    "Enter", "Esc", "Space", "Shift", "Tab", "F2", "F5", "F8",
    "Up/Down", "Left/Right", "PgUp/PgDn", "Page Up/Page Down",
)

# Verb stems for "erase" per language. "Clear" (a selection, a preference)
# must never be rendered as "erase": in a disk-erasing tool that reads as a
# destructive instruction.
ERASE_STEMS = {
    "en": r"eras|wip",
    "fr": r"effa[cç]",
    "de": r"lösch",
    "es": r"borr",
}


def _values(value, prefix=""):
    if isinstance(value, str):
        yield prefix, value
    else:
        for index, item in enumerate(value):
            yield from _values(item, f"{prefix}[{index}]")


def _entries():
    for module, names in lang.surface().items():
        for name in names:
            english = dict(_values(lang.english(module, name)))
            for code in TRANSLATED:
                translated = dict(_values(lang.translated(code, module, name)))
                yield code, module, name, english, translated


def _fields(text: str) -> Counter:
    fields = Counter()
    for literal, field, _, _ in string.Formatter().parse(text):
        if field is not None:
            fields[field] += 1
    fields["{{"] = text.count("{{")
    fields["}}"] = text.count("}}")
    return fields


def test_placeholders_match_english_in_name_and_count_including_tuples():
    for code, module, name, english, translated in _entries():
        assert set(translated) == set(english), (code, module, name)
        for sub, text in english.items():
            assert _fields(translated[sub]) == _fields(text), (
                code, module, name + sub, text, translated[sub],
            )


@pytest.mark.parametrize("code", TRANSLATED)
@pytest.mark.parametrize("citing_module,citing,label_module,label", CITED_LABELS)
def test_cited_labels_match_the_translated_label(
    code, citing_module, citing, label_module, label
):
    english_label = lang.english(label_module, label).rstrip("?").strip()
    english_text = lang.english(citing_module, citing)
    # The pair is only meaningful while English still cites the label.
    assert english_label.casefold() in english_text.casefold(), (citing, label)
    wanted = lang.translated(code, label_module, label).rstrip("?").strip()
    text = lang.translated(code, citing_module, citing)
    assert wanted.casefold() in text.casefold(), (code, citing, wanted, text)


def test_key_names_stay_english():
    for code, module, name, english, translated in _entries():
        for sub, text in english.items():
            for key in KEY_NAMES:
                pattern = rf"(?<![\w/]){re.escape(key)}(?![\w/])"
                if re.search(pattern, text):
                    assert re.search(pattern, translated[sub]), (
                        code, module, name + sub, key,
                    )


def test_clear_is_never_translated_as_erase():
    checked = 0
    for code, module, name, english, translated in _entries():
        for sub, text in english.items():
            if not re.search(r"\bclear", text, re.IGNORECASE):
                continue
            checked += 1
            allowed = len(re.findall(ERASE_STEMS["en"], text, re.IGNORECASE))
            found = len(re.findall(ERASE_STEMS[code], translated[sub], re.IGNORECASE))
            assert found <= allowed, (code, module, name + sub, translated[sub])
    assert checked >= 15


def test_spanish_opening_marks_balance():
    for code, module, name, english, translated in _entries():
        if code != "es":
            continue
        for sub, text in translated.items():
            assert text.count("¿") == text.count("?"), (module, name + sub, text)
            assert text.count("¡") == text.count("!"), (module, name + sub, text)


def test_french_uses_typographic_apostrophes():
    apostrophe = re.compile(r"[^\W\d_]'[^\W\d_]")
    for code, module, name, english, translated in _entries():
        if code != "fr":
            continue
        for sub, text in translated.items():
            assert not apostrophe.search(text), (module, name + sub, text)


def test_french_spaces_before_high_punctuation():
    # One rule: an ordinary space before ? ; ! and before a label colon.
    for code, module, name, english, translated in _entries():
        if code != "fr":
            continue
        for sub, text in translated.items():
            plain = re.sub(r"&\w+;|https?://\S+|\{[^}]*\}|\w+=\{", "", text)
            assert not re.search(r"[^\s(][?;!]", plain), (module, name + sub, text)


@pytest.mark.parametrize("code", TRANSLATED)
def test_helper_pages_cite_the_translated_ui_labels(code):
    page = (HELPER / f"{code}.html").read_text(encoding="utf-8")
    for module, name in (
        ("copy", "TITLE_KEYBOARD"),
        ("copy", "STOP_ASK"),
        ("copy", "BTN_SAVE_REPORT"),
        ("copy", "SUPPORT_CODE_LABEL"),
        ("copy", "SUPPORT_BUILD_LABEL"),
        ("recovery", "RECOVERY_HAPPENED"),
        ("recovery", "RECOVERY_MEANING"),
        ("recovery", "RECOVERY_NEXT"),
    ):
        assert lang.translated(code, module, name) in page, (code, name)
    # The boot menu and kiosk recovery stay English; the page says so and
    # quotes the English boot-menu entry rather than a translation of it.
    assert "Beamo Wipe: speech for screen readers" in page
    assert lang.translated(code, "copy", f"LANGUAGE_NAME_{code.upper()}") in page
