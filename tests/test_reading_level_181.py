"""Plain, short sentences on every owner-facing English string (#181).

The project writes for an 8th-grade reader (copy.py's docstring). This test
measures each sentence of the English text the owner reads and fails when
one is too long or too hard:

- no sentence over MAX_WORDS words;
- a sentence of GRADED_FROM words or more must have a Flesch-Kincaid grade
  below GRADE_LIMIT (9.0): a score of 8.x is the 8th grade. Shorter
  sentences are not graded: on a handful of words one long word swings
  the score by many grades, and they are short already.

The surface is every string the UI translates (lang.surface(): copy.py and
the other modules' screen, report and error text, which the screens show in
the owner's language) plus copy.py's derived English constants. The other
string literals in the code are developer, log or evidence text that the
owner never reads as a sentence, or the keyboard hints and identifiers the
glossary test (#180) also checks for words only.

Dependency-free: a simple syllable counter, the standard formula
0.39 * words + 11.8 * syllables / words - 15.59 per sentence.

Fixed names count as one short word (TERMS): the product and engine names,
the glossary's names for things (#180, one name per thing), on-screen labels
quoted in a sentence, and hardware, file-system and file names. A writer
cannot pick a shorter word for them. Whole sentences that cannot go lower
are listed in ALLOWED with the reason; each must still be needed.
"""
from __future__ import annotations

import re

import pytest

GRADE_LIMIT = 9.0  # Flesch-Kincaid 8.x is the 8th grade; 9.0 is the 9th.
MAX_WORDS = 20
GRADED_FROM = 10

# Names the owner sees exactly as written elsewhere: each counts as "it".
TERMS = (
    # Product and engine.
    "Beamo Wipe", "Beamo USB", "Beamo", "nwipe v0.42", "nwipe", "Debian", "Linux", "Windows",
    # Glossary names (docs/glossary.md) and on-screen labels quoted in copy.
    "Diagnostic report", "diagnostic report", "Diagnostics", "screen-reader view", "Help & settings",
    "Check disks again", "Erase another disk", "Save report to USB", "Erase now", "Stop erase",
    "Show more", "Need a report?", "Support code", "Boot helper", "Final check", "Shut down",
    "Text size", "High contrast", "Standard contrast", "Everyday", "Three overwrites", "Quick zero",
    "Storage limits", "Prepare",
    # File systems, hardware and standards named by docs/claims.md and the limits docs.
    "FAT32", "exFAT", "NTFS", "FAT12", "FAT16", "NVMe", "SSDs", "SSD", "HDD", "RAID",
    "HPA/DCO", "BitLocker", "OPAL", "ATA", "Intel RST", "VMD", "Secure Boot", "Apple Silicon",
    "Chromebooks", "Macs", "UEFI", "BIOS", "Intel/AMD", "64-bit",
    # Keyboard layout names (keyboard.py).
    "QWERTY", "AZERTY", "QWERTZ", "Latin American",
    # File names.
    "result.json", "RESULT.txt", "SHARE.json", "SHARE.txt", "START-HERE.html", "README.txt",
)

# (sentence start, reason). Kept as written; each must still be found and
# still exceed the limits, or the entry is removed.
ALLOWED: list[tuple[str, str]] = [
    ("Everything on it will be erased, including its operating system.",
     "copy.ERASE_EVERYTHING_SYSTEM, the disk-specific erase warning (#128): one sentence with the "
     "same shape as its Windows and data siblings, which tests count as one warning; {disk} is "
     "the disk's name, and 'operating system' has no plainer word"),
    ("It cannot guarantee coverage of inaccessible, remapped, over-provisioned (spare), or controller-managed",
     "storage_limits.REPORT_OVERWRITE_LIMITS: the storage limits as saved in every report (result.json "
     "warnings, the coverage check, RESULT.txt); persisted evidence text. The screens show "
     "OVERWRITE_LIMITS, the same limits in plain sentences"),
    ("Contradictory hidden-storage lines were present in the pinned nwipe v0.42 log.",
     "engine_checks.HIDDEN_CONTRADICTORY: a check detail saved in result.json (persisted "
     "evidence text) that describes nwipe's own log"),
    ("Error Summary listed zero pass, verification, and fdatasync errors for the target.",
     "engine_checks.IO_CLEAN_DETAIL: a check detail saved in result.json (persisted evidence "
     "text) that quotes nwipe's log section and counter names"),
]


# --- the measure -------------------------------------------------------------

_TERM_RX = re.compile(
    "|".join(
        r"(?<![\w.\-])" + re.escape(term) + r"(?![\w\-])"
        for term in sorted(TERMS, key=len, reverse=True)
    )
)
# A placeholder that a capital letter follows ends its sentence ("{volatile} This...").
_PLACEHOLDER_END = re.compile(r"\{[A-Za-z_]*\}(?=[ \t]+[A-Z])")
_PLACEHOLDER = re.compile(r"\{[A-Za-z_]*\}")
_WORD = re.compile(r"[A-Za-z0-9][A-Za-z0-9'’\-]*")
_VOWELS = re.compile(r"[aeiouy]+")


def syllables(word: str) -> int:
    """A simple English syllable count: vowel groups, silent final e."""
    w = re.sub(r"[^a-z]", "", word.lower())
    if len(w) <= 3:
        return 1
    w = re.sub(r"(?:[^laeiouy]es|[^laeiouy]ed|[^laeiouy]e)$", "", w)
    w = re.sub(r"^y", "", w)
    return max(1, len(_VOWELS.findall(w)))


def sentences(text: str) -> list[str]:
    """Sentences of one string: lines, then '.', '!' or '?' plus a space."""
    text = _PLACEHOLDER.sub("it", _PLACEHOLDER_END.sub("it.", text))
    out = []
    for line in text.splitlines():
        for part in re.split(r"(?<=[.!?…])\s+", line):
            part = part.strip(" \t•·-–—")
            if part:
                out.append(part)
    return out


def words(sentence: str) -> list[str]:
    return _WORD.findall(_TERM_RX.sub("it", sentence))


def grade(sentence: str) -> float:
    found = words(sentence)
    if not found:
        return 0.0
    count = sum(syllables(w) for w in found)
    return 0.39 * len(found) + 11.8 * count / len(found) - 15.59


def problem(sentence: str) -> str:
    """Why a sentence is too long or too hard, or ''.

    The length counts every word as written, names included: the reader
    still reads them. The grade, and whether a sentence is long enough to
    grade, count each name as one short word.
    """
    n = len(_WORD.findall(sentence))
    if n > MAX_WORDS:
        return f"{n} words (max {MAX_WORDS})"
    if len(words(sentence)) >= GRADED_FROM and grade(sentence) >= GRADE_LIMIT:
        return f"grade {grade(sentence):.1f} (limit {GRADE_LIMIT:g})"
    return ""


# --- the surface ---------------------------------------------------------------


def _strings(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, (list, tuple)):
        return [s for item in value for s in _strings(item)]
    return []


def surfaces() -> list[tuple[str, str]]:
    from beamo_wipe import copy as C
    from beamo_wipe import lang

    lang.set_language("en")
    rows = []
    for module, names in lang.surface().items():
        for name, value in names.items():
            rows += [(f"{module}.{name}", s) for s in _strings(value)]
    for name in dir(C):
        if name.isupper():
            rows += [(f"copy.{name}", s) for s in _strings(getattr(C, name))]
    return rows


def _allowed(sentence: str) -> bool:
    return any(sentence.startswith(start) for start, _ in ALLOWED)


def offenders(rows=None) -> list[str]:
    """Each failing sentence once, under the first string that shows it."""
    hits = []
    seen = set()
    for where, text in surfaces() if rows is None else rows:
        for sentence in sentences(text):
            why = problem(sentence)
            if why and not _allowed(sentence) and sentence not in seen:
                seen.add(sentence)
                hits.append(f"{where}: {why}: {sentence}")
    return hits


# --- tests ---------------------------------------------------------------------


@pytest.mark.parametrize(
    ("word", "count"),
    [("disk", 1), ("erase", 2), ("computer", 3), ("unplugged", 2), ("removed", 2),
     ("controller", 3), ("identity", 4), ("the", 1), ("countdown", 2)],
)
def test_syllable_counter(word, count):
    assert syllables(word) == count


def test_sentence_split_and_terms():
    assert sentences("One.\nTwo two? Three {disk} three!") == ["One.", "Two two?", "Three it three!"]
    assert words("Save report to USB on the Beamo USB.") == ["it", "on", "the", "it"]
    assert words("result.json and RESULT.txt") == ["it", "and", "it"]


def test_the_check_flags_long_and_hard_sentences():
    long = "Keep the disk in " + "and wait " * 9 + "now."
    assert "words" in problem(long)
    hard = "It cannot guarantee coverage of inaccessible, remapped, or controller-managed flash areas."
    assert "grade" in problem(hard)
    for plain in (
        "Keep the Beamo USB in until the result screen asks you to remove it.",
        "Leave the Beamo USB and the selected disk connected.",
        "Removing it earlier ends this session immediately.",  # short: not graded
    ):
        assert problem(plain) == "", plain


def test_every_owner_facing_sentence_is_plain():
    hits = offenders()
    assert hits == [], f"{len(hits)} sentences above an 8th-grade level:\n" + "\n".join(hits)


def test_each_exception_is_still_needed():
    rows = surfaces()
    for start, reason in ALLOWED:
        found = [s for _where, text in rows for s in sentences(text) if s.startswith(start)]
        assert found, f"unused exception {start!r} ({reason}); remove it from ALLOWED"
        assert any(problem(s) for s in found), f"{start!r} now passes; remove it from ALLOWED"


# --- what changed and what did not ---------------------------------------------

# The persisted report wording of the storage limits (result.json warnings, the
# coverage check, RESULT.txt goldens). The screens say it in plainer sentences.
_REPORT_LIMITS = (
    "Overwriting reaches only storage the device exposes. It cannot guarantee "
    "coverage of inaccessible, remapped, over-provisioned (spare), or "
    "controller-managed flash areas. Additional overwrite passes do not fix these limitations."
)


def test_reports_keep_their_storage_limits_wording():
    from beamo_wipe import storage_limits as L
    from beamo_wipe.engine_checks import evaluate_engine_checks
    from beamo_wipe.models import Disk, DiskKind

    assert L.REPORT_OVERWRITE_LIMITS == _REPORT_LIMITS
    assert L.OVERWRITE_LIMITS != _REPORT_LIMITS
    for kind in DiskKind:
        assert L.report_notice(kind).endswith(_REPORT_LIMITS)
        assert L.notice(kind).endswith(L.OVERWRITE_LIMITS)
        assert L.report_notice(kind)[: -len(_REPORT_LIMITS)] == L.notice(kind)[: -len(L.OVERWRITE_LIMITS)]
    disk = Disk(path="/dev/sda", name="sda", model="Fake SSD", serial="S1", size_bytes=1,
                size_gb_label="1", kind=DiskKind.SSD, bus="SATA", label="")
    coverage = [c for c in evaluate_engine_checks("", "/dev/sda", disk) if c.id == "coverage"]
    assert coverage and coverage[0].detail == L.report_notice(DiskKind.SSD)


def test_evidence_warnings_use_the_report_wording():
    import inspect

    from beamo_wipe import evidence

    source = inspect.getsource(evidence._warnings_for)
    assert "report_notice(disk.kind)" in source


@pytest.mark.parametrize("code", ["fr", "de", "es", "it"])
def test_translations_follow_the_split(code):
    """Every rewritten English string has a draft translation; reports keep theirs."""
    import importlib

    from beamo_wipe import lang
    from beamo_wipe import storage_limits as L
    from beamo_wipe.models import DiskKind

    strings = importlib.import_module(f"beamo_wipe.locales.{code}").STRINGS
    limits = strings["storage_limits"]
    assert limits["REPORT_OVERWRITE_LIMITS"] != limits["OVERWRITE_LIMITS"]
    try:
        lang.set_language(code)
        assert L.report_notice(DiskKind.SSD).endswith(limits["REPORT_OVERWRITE_LIMITS"])
        assert L.notice(DiskKind.SSD).endswith(limits["OVERWRITE_LIMITS"])
    finally:
        lang.set_language("en")
    # No ';' left in the sentences this task split (they read as two now).
    for module, name in (("copy", "REPORT_HELP_START"),
                         ("storage_limits", "SECTION_ENCRYPTION_BODY"),
                         ("storage_limits", "SECTION_ALTERNATIVE_BODY"),
                         ("storage_limits", "SECTION_OWNERSHIP_BODY")):
        assert ";" not in strings[module][name], (code, module, name)
