# SPDX-License-Identifier: GPL-3.0-or-later
"""Which typed confirmation characters are wrong (#156). Display only.

The gate itself is safety.token_matches and is not changed here: outer
whitespace is ignored and case does not matter; nothing else is relaxed (no
partial match, inner spaces count, another disk's characters never match).

This module only explains a wrong entry: it marks the typed characters that
do not match the token at the same position, says how many are missing or
extra, and points out spaces typed between characters. It never prints an
expected character; the card already shows them (#129). Nothing here may be
used to decide a match.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from beamo_wipe import copy as C

# Shown in place of a typed space so it can be seen and marked.
SPACE_GLYPH = "␣"


@dataclass(frozen=True)
class TokenFeedback:
    # The typed value, one character per cell, "[x]" around mismatches.
    display: str
    # "Character 3 doesn't match." plus missing/extra/space sentences.
    message: str
    # For screen readers: characters separated by commas, no brackets.
    spoken: str
    # 0-based token positions whose typed character does not match.
    wrong: tuple[int, ...]
    missing: int
    extra: int


def _same(a: str, b: str) -> bool:
    return a.casefold() == b.casefold()


def _ordinals(positions: tuple[int, ...]) -> str:
    items = [str(p + 1) for p in positions]
    if len(items) == 1:
        return items[0]
    from beamo_wipe import inventory

    return ", ".join(items[:-1]) + f" {inventory.POSITION_AND} " + items[-1]


def feedback(typed: str, token: str) -> Optional[TokenFeedback]:
    """Explain a wrong entry, or None when it matches or nothing is typed."""
    got = (typed or "").strip()
    want = (token or "").strip()
    if not got or not want:
        return None
    if len(got) == len(want) and all(_same(a, b) for a, b in zip(got, want)):
        return None
    # Spaces between characters are marked on their own; the other typed
    # characters are compared in order with the token so one stray space
    # does not make every later character look wrong. (The gate still
    # rejects any inner space.) Numbers in the message are token positions.
    spaces = tuple(i for i, ch in enumerate(got) if ch.isspace())
    kept = [i for i, ch in enumerate(got) if not ch.isspace()]
    shared = min(len(kept), len(want))
    wrong_tokens = tuple(j for j in range(shared) if not _same(got[kept[j]], want[j]))
    wrong = wrong_tokens
    extra_positions = tuple(kept[len(want):])
    missing = max(0, len(want) - len(kept))
    extra = len(extra_positions)
    marked = {kept[j] for j in wrong_tokens} | set(extra_positions) | set(spaces)
    cells = []
    for i, ch in enumerate(got):
        shown = SPACE_GLYPH if ch.isspace() else ch
        cells.append(f"[{shown}]" if i in marked else shown)
    sentences = []
    if wrong:
        template = C.TOKEN_WRONG_ONE if len(wrong) == 1 else C.TOKEN_WRONG_MANY
        sentences.append(template.format(n=wrong[0] + 1, list=_ordinals(wrong)))
    if missing:
        sentences.append(C.TOKEN_MISSING_ONE if missing == 1
                         else C.TOKEN_MISSING_MANY.format(count=missing))
    if extra:
        sentences.append(C.TOKEN_EXTRA_ONE if extra == 1
                         else C.TOKEN_EXTRA_MANY.format(count=extra))
    if spaces:
        sentences.append(C.TOKEN_SPACE_NOTE)
    message = " ".join(sentences)
    spoken_chars = ", ".join(C.TOKEN_SPACE_WORD if ch.isspace() else ch for ch in got)
    return TokenFeedback(
        display=C.TOKEN_TYPED.format(typed=" ".join(cells)),
        message=message,
        spoken=f"{C.TOKEN_TYPED.format(typed=spoken_chars)}. {message}",
        wrong=wrong,
        missing=missing,
        extra=extra,
    )
