# SPDX-License-Identifier: GPL-3.0-or-later
"""One fixed "Help & settings" menu for every screen (#175).

Every surface (Tk, GTK/Orca, curses, the web preview) shows the same items
in the same order. An item that does not apply on the current screen stays
in the list, disabled, with a short reason; it never disappears. Opening
the menu changes nothing. Items only call the wizard's existing guarded
actions, so Advanced keeps its safety limits (it opens from the method step
only) and nothing in the menu can start, confirm or stop an erase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from beamo_wipe import copy as C
from beamo_wipe.models import Screen

TEXT_SIZE = "text_size"
LANGUAGE = "language"
SOUNDS = "sounds"
HIGH_CONTRAST = "high_contrast"
REPORT_HELP = "report_help"
ADVANCED = "advanced"
SHORTCUTS = "shortcuts"

ORDER = (TEXT_SIZE, LANGUAGE, SOUNDS, HIGH_CONTRAST, REPORT_HELP, ADVANCED, SHORTCUTS)

# Items that change a setting and leave the menu open; the others open a
# screen (and close the menu) or show information inside it.
STAYS_OPEN = frozenset({TEXT_SIZE, SOUNDS, SHORTCUTS})

# Screens where the type size must not change under the person: the final
# check before Erase now (its countdown and focus must not be disturbed) and
# the short status screens while disks are checked or a stop is confirmed.
TEXT_SIZE_LOCKED = frozenset({
    Screen.LAST_CHANCE, Screen.CHECKING, Screen.STOPPING, Screen.REFRESHING,
})
_BUSY = frozenset({Screen.CHECKING, Screen.STOPPING, Screen.REFRESHING})
_ERASE_OR_AFTER = frozenset({Screen.WORKING, Screen.CHECKING, Screen.STOPPING, Screen.DONE})


@dataclass(frozen=True)
class MenuItem:
    key: str
    label: str
    enabled: bool
    reason: str = ""

    @property
    def stays_open(self) -> bool:
        return self.key in STAYS_OPEN

    @property
    def spoken(self) -> str:
        """Label plus the reason when disabled, for screen readers and text."""
        if self.enabled or not self.reason:
            return self.label
        return f"{self.label} — {self.reason}"


def text_size_label(size: str) -> str:
    return f"{C.TEXT_SIZE_UTILITY}: {C.TEXT_SIZE_LABELS.get(size, C.TEXT_SIZE_STANDARD)}"


def items(
    *,
    screen: Screen,
    text_size: str,
    sounds_label: str,
    can_open_keyboard: bool,
    can_open_report_help: bool,
    can_open_advanced: bool,
    sound_available: bool = True,
    after_erase_started: bool = False,
    text_size_supported: bool = True,
) -> tuple[MenuItem, ...]:
    """The menu for one screen. Pure: the same inputs give the same menu."""
    here = C.MENU_REASON_HERE

    if not text_size_supported:
        size = MenuItem(TEXT_SIZE, text_size_label(text_size), False, C.TEXT_SIZE_CONSOLE)
    elif screen == Screen.LAST_CHANCE:
        size = MenuItem(TEXT_SIZE, text_size_label(text_size), False, C.MENU_REASON_FINAL_CHECK)
    elif screen in TEXT_SIZE_LOCKED:
        size = MenuItem(TEXT_SIZE, text_size_label(text_size), False, C.MENU_REASON_BUSY)
    else:
        size = MenuItem(TEXT_SIZE, text_size_label(text_size), True)

    if screen == Screen.KEYBOARD:
        language = MenuItem(LANGUAGE, C.MENU_LANGUAGE, False, here)
    elif can_open_keyboard:
        language = MenuItem(LANGUAGE, C.MENU_LANGUAGE, True)
    elif screen == Screen.SPLASH:
        language = MenuItem(LANGUAGE, C.MENU_LANGUAGE, False, C.MENU_REASON_LANGUAGE_NEXT)
    elif after_erase_started or screen in _ERASE_OR_AFTER:
        language = MenuItem(LANGUAGE, C.MENU_LANGUAGE, False, C.MENU_REASON_LANGUAGE_BEFORE)
    elif screen in _BUSY:
        language = MenuItem(LANGUAGE, C.MENU_LANGUAGE, False, C.MENU_REASON_BUSY)
    else:
        language = MenuItem(LANGUAGE, C.MENU_LANGUAGE, False, C.MENU_REASON_NOT_HERE)

    sounds = (
        MenuItem(SOUNDS, sounds_label, True)
        if sound_available
        else MenuItem(SOUNDS, sounds_label, False, C.MENU_REASON_NO_SOUND)
    )
    contrast = MenuItem(HIGH_CONTRAST, C.MENU_HIGH_CONTRAST, False, C.MENU_REASON_NOT_YET)

    if screen == Screen.REPORT_HELP:
        report = MenuItem(REPORT_HELP, C.MENU_REPORT_HELP, False, here)
    elif can_open_report_help:
        report = MenuItem(REPORT_HELP, C.MENU_REPORT_HELP, True)
    else:
        report = MenuItem(REPORT_HELP, C.MENU_REPORT_HELP, False, C.MENU_REASON_REPORT_HELP)

    # Advanced keeps its existing limit: it opens from the method step only,
    # before an erase is requested.
    if screen == Screen.ADVANCED:
        advanced = MenuItem(ADVANCED, C.BTN_ADVANCED, False, here)
    elif can_open_advanced:
        advanced = MenuItem(ADVANCED, C.BTN_ADVANCED, True)
    else:
        advanced = MenuItem(ADVANCED, C.BTN_ADVANCED, False, C.MENU_REASON_ADVANCED)

    shortcuts = MenuItem(SHORTCUTS, C.MENU_SHORTCUTS, True)
    return (size, language, sounds, contrast, report, advanced, shortcuts)


def find(menu: tuple[MenuItem, ...], key: str) -> Optional[MenuItem]:
    return next((item for item in menu if item.key == key), None)
