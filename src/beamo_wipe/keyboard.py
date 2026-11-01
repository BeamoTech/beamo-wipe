# SPDX-License-Identifier: GPL-3.0-or-later
"""Session keyboard layouts. Allowlisted argv only; never a shell string."""

from __future__ import annotations

from dataclasses import dataclass
import os
import subprocess
from typing import Mapping, Optional, Sequence, Tuple

# Shipped on the live image: x11-xserver-utils (setxkbmap) and kbd (loadkeys).
# xkb-data (/usr/share/X11/xkb/symbols/<xkb>) and console-data
# (/usr/share/keymaps/i386/<family>/<console>.kmap.gz) ship many maps; only
# the layouts below are offered. A layout id always equals its XKB name.
DEFAULT_LAYOUT = "us"

# Binaries we may exec. Names only; resolved on the clean PATH at apply time.
_SETXKBMAP = "setxkbmap"
_LOADKEYS = "loadkeys"
_ALLOWED_BINARIES = frozenset({_SETXKBMAP, _LOADKEYS})


@dataclass(frozen=True)
class KeyboardLayout:
    id: str
    title: str
    family: str
    note: str
    xkb_layout: str
    console_map: str
    dead_keys: bool
    digits_need_shift: bool

    @property
    def xkb_argv(self) -> Tuple[str, ...]:
        return (_SETXKBMAP, "-layout", self.xkb_layout, "-option", "")

    @property
    def console_argv(self) -> Tuple[str, ...]:
        return (_LOADKEYS, self.console_map)


@dataclass(frozen=True)
class ApplyResult:
    ok: bool
    message: str
    layout_id: str = ""


TITLE_US = "QWERTY (US)"
NOTE_US = (
    "Letters and digits match a US QWERTY keyboard. "
    "Numbers do not need Shift."
)
TITLE_FR = "AZERTY (French)"
NOTE_FR = (
    "Letters match a French AZERTY keyboard. Digit keys usually need Shift. "
    "Accented letters use dead keys: press the accent, then the letter."
)
TITLE_DE = "QWERTZ (German)"
NOTE_DE = (
    "Letters match a German QWERTZ keyboard. Y and Z are swapped from QWERTY. "
    "Some accents use dead keys: press the accent, then the letter."
)
TITLE_GB = "QWERTY (UK)"
NOTE_GB = (
    "Letters and digits match a UK QWERTY keyboard. Numbers do not need Shift. "
    "Some symbols, such as @ and \", are in different places than on US QWERTY."
)
TITLE_ES = "QWERTY (Spanish)"
NOTE_ES = (
    "Letters and digits match a Spanish QWERTY keyboard, including Ñ. "
    "Numbers do not need Shift. "
    "Accents use dead keys: press the accent, then the letter."
)
TITLE_LATAM = "QWERTY (Latin American)"
NOTE_LATAM = (
    "Letters and digits match a Latin American QWERTY keyboard, including Ñ. "
    "Numbers do not need Shift. "
    "Accents use dead keys: press the accent, then the letter."
)
TITLE_IT = "QWERTY (Italian)"
NOTE_IT = (
    "Letters and digits match an Italian QWERTY keyboard. "
    "Numbers do not need Shift. "
    "Accented letters such as è and à have their own keys; "
    "some other accents use dead keys with AltGr."
)


def _qwerty(layout_id: str, title: str, note: str, console_map: str, dead_keys: bool) -> KeyboardLayout:
    return KeyboardLayout(
        id=layout_id,
        title=title,
        family="qwerty",
        note=note,
        xkb_layout=layout_id,
        console_map=console_map,
        dead_keys=dead_keys,
        digits_need_shift=False,
    )


def _build_layouts() -> Mapping[str, KeyboardLayout]:
    return {
        "us": KeyboardLayout(
            id="us",
            title=TITLE_US,
            family="qwerty",
            note=NOTE_US,
            xkb_layout="us",
            console_map="us",
            dead_keys=False,
            digits_need_shift=False,
        ),
        "fr": KeyboardLayout(
            id="fr",
            title=TITLE_FR,
            family="azerty",
            note=NOTE_FR,
            xkb_layout="fr",
            console_map="fr",
            dead_keys=True,
            digits_need_shift=True,
        ),
        "de": KeyboardLayout(
            id="de",
            title=TITLE_DE,
            family="qwertz",
            note=NOTE_DE,
            xkb_layout="de",
            console_map="de",
            dead_keys=True,
            digits_need_shift=False,
        ),
        # Console map names are console-data's qwerty/{uk,es,la-latin1,it}.
        "gb": _qwerty("gb", TITLE_GB, NOTE_GB, "uk", False),
        "es": _qwerty("es", TITLE_ES, NOTE_ES, "es", True),
        "latam": _qwerty("latam", TITLE_LATAM, NOTE_LATAM, "la-latin1", True),
        "it": _qwerty("it", TITLE_IT, NOTE_IT, "it", True),
    }


LAYOUTS: Mapping[str, KeyboardLayout] = _build_layouts()

# Digit shortcuts are 1..N in this order; N must stay a single digit.
LAYOUT_ORDER = ("us", "fr", "de", "gb", "es", "latam", "it")

UNAVAILABLE = "That keyboard layout is not available."
APPLY_FAILED = (
    "Could not change the keyboard layout. The previous layout is still in use."
)
TOOLS_MISSING = (
    "Keyboard layout tools are not available on this computer. "
    "The previous layout is still in use."
)
SESSION_ONLY = (
    "This change lasts until this USB session restarts. "
    "It does not change firmware or BIOS keyboards."
)
LIMITS_LEAD = (
    "Only US QWERTY, French AZERTY, German QWERTZ, UK QWERTY, Spanish QWERTY, "
    "Latin American QWERTY, and Italian QWERTY are offered. "
    "This USB does not include other layouts. "
)
LIMITS = LIMITS_LEAD + SESSION_ONLY
GRAPHICAL_ONLY = (
    "The graphical layout changed. The text console could not be updated. "
)


def _apply_language() -> None:
    global LAYOUTS, LIMITS
    LAYOUTS = _build_layouts()
    LIMITS = LIMITS_LEAD + SESSION_ONLY
CONSOLE_DEAD_KEYS = (
    "On the text console, dead keys may not compose. "
    "Check letters and digits here. Confirm tokens use letters and digits only."
)


def layout_for(layout_id: str) -> Optional[KeyboardLayout]:
    if not isinstance(layout_id, str):
        return None
    return LAYOUTS.get(layout_id)


def is_allowed(layout_id: str) -> bool:
    return layout_for(layout_id) is not None


def _run_allowlisted(argv: Sequence[str]) -> bool:
    if not argv or argv[0] not in _ALLOWED_BINARIES:
        return False
    spec = layout_for(argv[2] if argv[0] == _SETXKBMAP and len(argv) >= 3 else "")
    if argv[0] == _SETXKBMAP:
        if spec is None or tuple(argv) != spec.xkb_argv:
            return False
    elif argv[0] == _LOADKEYS:
        match = next((item for item in LAYOUTS.values() if tuple(argv) == item.console_argv), None)
        if match is None:
            return False
    from beamo_wipe.safety import resolve_system_binary, session_exec_env

    resolved = resolve_system_binary(argv[0])
    if not resolved:
        return False
    try:
        proc = subprocess.run(
            [resolved, *argv[1:]],
            check=False,
            timeout=3,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            env=session_exec_env(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def apply_layout(layout_id: str, *, graphical: Optional[bool] = None) -> ApplyResult:
    """Apply one allowlisted layout. Never interpolates untrusted text."""
    spec = layout_for(layout_id)
    if spec is None:
        return ApplyResult(False, UNAVAILABLE, "")
    if graphical is None:
        graphical = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    from beamo_wipe.safety import resolve_system_binary

    x_tool = resolve_system_binary(_SETXKBMAP)
    c_tool = resolve_system_binary(_LOADKEYS)
    if graphical and not x_tool:
        return ApplyResult(False, TOOLS_MISSING, spec.id)
    if not graphical and not c_tool:
        return ApplyResult(False, TOOLS_MISSING, spec.id)
    x_ok = True
    if graphical:
        x_ok = _run_allowlisted(spec.xkb_argv)
        if not x_ok:
            return ApplyResult(False, APPLY_FAILED, spec.id)
    c_ok = c_tool is not None
    if c_tool:
        c_ok = _run_allowlisted(spec.console_argv)
        if not graphical and not c_ok:
            return ApplyResult(False, APPLY_FAILED, spec.id)
    if graphical and not c_ok:
        return ApplyResult(
            True,
            GRAPHICAL_ONLY + SESSION_ONLY,
            spec.id,
        )
    return ApplyResult(True, "", spec.id)
