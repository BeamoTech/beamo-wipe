"""One name for each thing (#180).

docs/glossary.md is the source: its table names the word to use and the
synonyms that are banned. This test reads that table and fails when a
banned word appears on an English surface the owner reads: wizard copy and
the other modules' screen/report/error text, the web preview, the Boot
helper, the launchers, the USB README and the user-facing docs.

Code identifiers are never checked (only string constants, page text and
prose), and nwipe / Beamo Wipe are never renamed.
"""
from __future__ import annotations

import ast
import html
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
GLOSSARY = ROOT / "docs" / "glossary.md"

# Never checked: brand and engine names, placeholders.
BRANDS = re.compile(r"Beamo Wipe|beamo-wipe|beamo_wipe|BEAMO_WIPE|nwipe|Nwipe|\{[A-Za-z_]+\}")

SAFETY = "src/beamo_wipe/safety.py"
RUNNER = "src/beamo_wipe/nwipe_runner.py"
# safety.py and nwipe_runner.py are checked like every other module (#180
# follow-up, a safety: review). Their guard messages that reach a screen use
# the glossary names. The exceptions below are nwipe's own output, persisted
# evidence text, and SafetyError texts the owner never sees: the wizard
# replaces a refused start with PREFLIGHT_BLOCKED or STARTUP_UNCONFIRMED and
# never shows str(exc) (docs/glossary.md, "Not renamed").
_NEVER_SHOWN = "developer SafetyError text; the wizard shows PREFLIGHT_BLOCKED instead, never str(exc)"

# Exceptions: (surface prefix, exact phrase, reason). Each must still occur.
ALLOWED = [
    ("", "Help & settings menu", "the menu's own name followed by 'menu'"),
    ("", "Windows or Linux PCs", "hardware scope mirrors docs/claims.md"),
    ("", "Windows and Linux PCs", "hardware scope mirrors docs/claims.md"),
    ("", "UEFI PCs", "hardware scope mirrors docs/claims.md"),
    ("", "x64 PCs", "hardware scope mirrors docs/claims.md (release listing copy)"),
    ("src/beamo_wipe/wizard.py", "unsafe wipe log", "internal OSError text for nwipe's log file, never shown"),
    ("src/beamo_wipe/ui/accessible_wizard.py", "Refresh wake also failed", "exception note for developers"),
    (RUNNER, "--force is not set, not wiping it", "nwipe's own output text, matched by the IN USE regexes"),
    (RUNNER, "exited without wiping", "completion summary persisted as evidence failure_reason; tests pin it"),
    (RUNNER, "A wipe is already running.", _NEVER_SHOWN + " (the wizard's own is ALREADY_RUNNING)"),
    (RUNNER, "Wipe lock changed during acquisition.", _NEVER_SHOWN),
    (RUNNER, "Wipe lock is not a regular file.", _NEVER_SHOWN),
    (RUNNER, "Cannot create wipe lock", _NEVER_SHOWN + "; names the wipe.lock file"),
    (RUNNER, "Unknown wipe method.", _NEVER_SHOWN + " (argv builder/validator)"),
    (SAFETY, "Unknown wipe method.", _NEVER_SHOWN + " (assert_ready_to_wipe)"),
    (SAFETY, "No target disk selected.", _NEVER_SHOWN + " (assert_ready_to_wipe)"),
    (SAFETY, "Refusing to erase an optical drive.", _NEVER_SHOWN + "; other callers swallow it"),
    (SAFETY, "Refusing to write logs onto the target disk.",
     _NEVER_SHOWN + "; evidence writes show EVIDENCE_INVALID"),
]


def _cells(line: str) -> list[str]:
    parts = re.split(r"(?<!\\)\|", line.strip())
    return [p.strip().replace("\\|", "|") for p in parts[1:-1]]


def glossary() -> list[tuple[list[str], list[str]]]:
    """[(names to use, banned words)] from docs/glossary.md."""
    rows = []
    lines = GLOSSARY.read_text(encoding="utf-8").splitlines()
    start = lines.index("| Use | For | Not | Notes |")
    for line in lines[start + 2:]:
        if not line.startswith("|"):
            break
        use, _for, banned, _notes = _cells(line)
        names = re.findall(r"\*\*(.+?)\*\*", use)
        words = [w.strip() for w in banned.split(",") if w.strip()]
        rows.append((names, words))
    return rows


def _matcher(word: str) -> re.Pattern[str]:
    body = r"\s+".join(re.escape(part) for part in word.split())
    flags = 0 if word.isupper() or word in ("PCs",) else re.IGNORECASE
    # Not inside an identifier (a.b, a_b, a-b): only prose words.
    return re.compile(r"(?<![\w.\-])" + body + r"(?![\w\-])", flags)


def banned_words() -> list[tuple[str, re.Pattern[str]]]:
    return [(word, _matcher(word)) for _names, words in glossary() for word in words]


# --- surfaces -------------------------------------------------------------------


def _copy_strings() -> list[tuple[str, str]]:
    from beamo_wipe import copy as C
    from beamo_wipe import lang

    lang.set_language("en")
    out = []
    for name in dir(C):
        if not name.isupper():
            continue
        value = getattr(C, name)
        if isinstance(value, str):
            values = [value]
        elif isinstance(value, dict):
            values = list(value.values())
        elif isinstance(value, (list, tuple)):
            values = list(value)
        else:
            values = []
        out += [(f"copy.{name}", v) for v in values if isinstance(v, str)]
    return out


def _python_prose(path: pathlib.Path) -> list[tuple[str, str]]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docstrings.add(id(first.value))
    rel = path.relative_to(ROOT).as_posix()
    return [
        (f"{rel}:{node.lineno}", node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and id(node) not in docstrings and re.search(r"[A-Za-z]{2,} [a-z]{2,}", node.value)
    ]


def _page_text(path: pathlib.Path) -> list[tuple[str, str]]:
    s = path.read_text(encoding="utf-8")
    # Drop script/style blocks from our own helper pages before linting the
    # visible words; any case, and an end tag may carry spaces before ">".
    s = re.sub(r"<(script|style)\b.*?</\1\s*>", " ", s, flags=re.S | re.I)
    attrs = re.findall(r'(?:aria-label|title|alt|placeholder)="([^"]*)"', s)
    s = re.sub(r"<[^>]+>", " ", s)
    rel = path.relative_to(ROOT).as_posix()
    return [(rel, html.unescape(t)) for t in s.split("\n") + attrs if t.strip()]


def _literals(path: pathlib.Path) -> list[tuple[str, str]]:
    """Double-quoted and backquoted literals (JavaScript and Go) that read as prose."""
    s = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()
    found = re.findall(r'"((?:[^"\\\n]|\\.)*)"|`([^`]*)`', s)
    return [(rel, t) for pair in found for t in pair if t and re.search(r"[A-Za-z]{2,} [a-z]{2,}", t)]


def _doc_text(path: pathlib.Path) -> list[tuple[str, str]]:
    s = path.read_text(encoding="utf-8")
    s = re.sub(r"```.*?```", lambda m: "\n" * m.group(0).count("\n"), s, flags=re.S)
    s = re.sub(r"`[^`\n]*`", " ", s)
    s = re.sub(r"\]\([^)]*\)", "]", s)
    rel = path.relative_to(ROOT).as_posix()
    return [(f"{rel}:{i}", line) for i, line in enumerate(s.split("\n"), 1) if line.strip()]


def surfaces() -> list[tuple[str, str]]:
    rows = _copy_strings()
    for path in sorted((ROOT / "src" / "beamo_wipe").rglob("*.py")):
        if "locales" in path.parts:
            continue
        rows += _python_prose(path)
    rows += _python_prose(ROOT / "scripts" / "stage_live_assets.py")
    rows += _page_text(ROOT / "helper" / "index.html")
    rows += _page_text(ROOT / "desktop" / "web" / "index.html")
    rows += _literals(ROOT / "desktop" / "web" / "app.js")
    for path in sorted((ROOT / "desktop").glob("*.go")):
        if not path.name.endswith("_test.go"):
            rows += _literals(path)
    for doc in ("README.md", "helper/README.md", "docs/screen-reader.md"):
        rows += _doc_text(ROOT / doc)
    return rows


def _clean(where: str, text: str) -> str:
    text = BRANDS.sub(" ", text)
    for prefix, phrase, _reason in ALLOWED:
        if where.startswith(prefix):
            text = text.replace(phrase, " ")
    return text


def find_banned(rows) -> list[str]:
    words = banned_words()
    hits = []
    for where, text in rows:
        clean = _clean(where, text)
        for word, rx in words:
            for m in rx.finditer(clean):
                hits.append(f"{where}: {word!r} in …{clean[max(0, m.start() - 40): m.end() + 30]}…")
    return hits


# --- tests ----------------------------------------------------------------------


def test_glossary_table_is_complete_and_consistent():
    rows = glossary()
    names = [n for row_names, _ in rows for n in row_names]
    for expected in ("erase", "disk", "computer", "Beamo USB", "report USB", "USB stick", "Check disks again",
                     "Shut down", "boot menu", "Boot helper", "Final check", "Support code", "Text size",
                     "screen-reader view", "Help & settings", "Everyday", "Three overwrites", "Quick zero"):
        assert expected in names, expected
    banned = [w.casefold() for _, words in rows for w in words]
    assert len(banned) == len(set(banned)), "a banned word is listed twice"
    assert not {n.casefold() for n in names} & set(banned), "a word is both used and banned"
    text = GLOSSARY.read_text(encoding="utf-8")
    for keep in ("nwipe", "Beamo Wipe", "Screen.REFRESHING", "safety.py", "nwipe_runner.py"):
        assert keep in text, keep


@pytest.mark.parametrize("word", [w for _, words in glossary() for w in words])
def test_the_check_flags_each_banned_word(word):
    assert find_banned([("probe", f"Please see the {word} now.")]), word
    assert not find_banned([("probe", f"Use the selected disk.{word.replace(' ', '_')}_x")])


def test_the_check_reads_prose_only():
    quiet = [
        ("probe", "This page does not erase disks."),  # verb, not "erase disk"
        ("probe", "a machine-readable copy"),  # GPL written offer
        ("probe", "P.titles.refresh and finish_refresh"),  # identifiers
        ("probe", "Beamo Wipe uses nwipe."),
        ("probe", "Open the Help & settings menu."),
        ("probe", "For 64-bit Intel/AMD Windows or Linux PCs that start from this USB."),
    ]
    assert find_banned(quiet) == []
    assert find_banned([("probe", "Keep the boot USB connected.")])
    assert find_banned([("probe", "Do not turn the PC off.")])


def test_no_banned_synonym_on_english_surfaces():
    hits = find_banned(surfaces())
    assert hits == [], "\n".join(hits)


def test_each_exception_is_still_needed():
    rows = surfaces()
    for prefix, phrase, reason in ALLOWED:
        assert any(where.startswith(prefix) and phrase in BRANDS.sub(" ", text) for where, text in rows), (
            f"unused exception {phrase!r} ({reason}); remove it from ALLOWED"
        )


LOCALE_BANNED = {
    # docs/translations.md: the start-up stick is the Beamo USB in every language.
    "fr": ("clé USB de démarrage",),
    "de": ("Start-USB-Stick",),
    "es": ("memoria USB de arranque",),
    "it": ("chiavetta USB di avvio",),
}
LOCALE_BEAMO_USB = {
    "fr": "clé USB Beamo",
    "de": "Beamo-USB-Stick",
    "es": "memoria USB Beamo",
    "it": "chiavetta USB Beamo",
}


@pytest.mark.parametrize("code", sorted(LOCALE_BANNED))
def test_translations_use_one_name_for_the_beamo_usb(code):
    import importlib

    strings = importlib.import_module(f"beamo_wipe.locales.{code}").STRINGS
    hits = []
    for module, table in strings.items():
        for key, value in table.items():
            if not isinstance(value, str):
                continue
            hits += [f"{module}.{key}: {w}" for w in LOCALE_BANNED[code] if w in value]
    assert hits == []


def test_guard_and_engine_modules_are_checked():
    """safety.py and nwipe_runner.py are no longer skipped (#180 follow-up)."""
    where = {row[0].rsplit(":", 1)[0] for row in surfaces()}
    assert {SAFETY, RUNNER} <= where


@pytest.mark.parametrize("code", ["en", *sorted(LOCALE_BEAMO_USB)])
def test_shown_boot_guard_messages_name_the_beamo_usb(code):
    """The two boot guards reach the blocked screen as its body text."""
    from beamo_wipe import lang, safety

    try:
        lang.set_language(code)
        name = LOCALE_BEAMO_USB.get(code, "Beamo USB")
        for message in (safety.BOOT_APPEARED_SELECTABLE, safety.BOOT_APPEARED_ALIAS):
            assert name in message, (code, message)
    finally:
        lang.set_language("en")


def test_translation_glossary_points_at_the_glossary():
    text = (ROOT / "docs" / "translations.md").read_text(encoding="utf-8")
    assert "glossary.md" in text
    assert "| boot USB |" not in text
