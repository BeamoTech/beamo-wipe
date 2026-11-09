#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Write every boot-menu key list from desktop/bootkeys.json (#184).

desktop/bootkeys.json is the one maintained table. The launcher embeds it to
match the computer's brand; this script regenerates the marked regions of the
Boot helper pages, the launcher page and docs/boot-card.md from it.

    python scripts/gen_boot_keys.py          # rewrite the marked regions
    python scripts/gen_boot_keys.py --check  # exit 1 if any region drifted

docs/boot-keys.md explains the fields and cites the sources.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "desktop" / "bootkeys.json"
HELPERS = {"en": "index.html", "fr": "fr.html", "de": "de.html", "es": "es.html", "it": "it.html"}


def load(path: Path = TABLE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _kbd(key: str) -> str:
    return f'<span class="kbd">{html.escape(key, quote=False)}</span>'


def key_text(brand: dict, words: dict, *, markup: str) -> str:
    """'Esc, then F9' as HTML key caps, Markdown or plain text."""
    sep = words["then" if brand["join"] == "then" else "or"]
    if markup == "html":
        keys = [_kbd(k) for k in brand["keys"]]
        sep = html.escape(sep, quote=False)
    else:
        keys = list(brand["keys"])
    return sep.join(keys)


def name(brand: dict, lang: str) -> str:
    return brand.get("localized_name", {}).get(lang, brand["name"])


def suffix(brand: dict, lang: str) -> str:
    return brand.get("suffix", {}).get(lang, "")


def helper_rows(table: dict, lang: str) -> list[str]:
    words = table["words"][lang]
    return [
        f'<tr><td>{html.escape(name(b, lang), quote=False)}</td>'
        f'<td class="key">{key_text(b, words, markup="html")}{html.escape(suffix(b, lang), quote=False)}</td></tr>'
        for b in table["brands"]
    ]


def helper_summary(table: dict, lang: str) -> str:
    words = table["words"][lang]
    parts = [
        f"{html.escape(name(b, lang), quote=False)} {key_text(b, words, markup='html')}"
        f"{html.escape(suffix(b, lang), quote=False)}"
        for b in table["brands"]
    ]
    return f"<p>{html.escape(words['lead'], quote=False)} " + "; ".join(parts) + "</p>"


def launcher_rows(table: dict) -> list[str]:
    words = table["words"]["en"]
    return [
        f'<tr><td>{html.escape(b["name"], quote=False)}</td><td class="key">{key_text(b, words, markup="html")}</td></tr>'
        for b in table["brands"]
        if b["launcher"]
    ]


def boot_card_rows(table: dict) -> list[str]:
    words = table["words"]["en"]
    return [f"| {b['name']} | {key_text(b, words, markup='text')} |" for b in table["brands"] if b["launcher"]]


def boot_card_notes(table: dict) -> list[str]:
    return [f"- **{b['name']}:** {b['note']}" for b in table["brands"] if b["launcher"] and b.get("note")]


def regions(table: dict) -> dict[Path, dict[str, list[str]]]:
    """{file: {region name: generated lines}}."""
    out: dict[Path, dict[str, list[str]]] = {}
    for lang, page in HELPERS.items():
        out[ROOT / "helper" / page] = {
            "table": helper_rows(table, lang),
            "summary": [helper_summary(table, lang)],
        }
    out[ROOT / "desktop" / "web" / "index.html"] = {"launcher-table": launcher_rows(table)}
    out[ROOT / "docs" / "boot-card.md"] = {
        "boot-card-table": boot_card_rows(table),
        "boot-card-notes": boot_card_notes(table),
    }
    return out


def _marker(region: str) -> re.Pattern[str]:
    return re.compile(
        r"(?P<indent>[ \t]*)<!-- boot-keys:" + re.escape(region) + r" -->\n"
        r"(?P<body>.*?)"
        r"(?P=indent)<!-- /boot-keys:" + re.escape(region) + r" -->",
        re.S,
    )


def render(text: str, wanted: dict[str, list[str]]) -> str:
    for region, lines in wanted.items():
        pattern = _marker(region)
        found = pattern.findall(text)
        if len(found) != 1:
            raise SystemExit(f"boot-keys: expected one {region!r} region, found {len(found)}")

        def body(match: re.Match[str], lines: list[str] = lines, region: str = region) -> str:
            indent = match.group("indent")
            inner = "".join(f"{indent}{line}\n" for line in lines)
            return (
                f"{indent}<!-- boot-keys:{region} -->\n{inner}{indent}<!-- /boot-keys:{region} -->"
            )

        text = pattern.sub(body, text, count=1)
    return text


def drifted(table: dict | None = None) -> list[Path]:
    table = table or load()
    stale = []
    for path, wanted in regions(table).items():
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if render(text, wanted) != text:
            stale.append(path)
    return stale


def main(argv: list[str]) -> int:
    table = load()
    if argv[1:] == ["--check"]:
        stale = drifted(table)
        for path in stale:
            print(f"boot-keys: {path.relative_to(ROOT).as_posix()} drifted from desktop/bootkeys.json")
        return 1 if stale else 0
    if argv[1:]:
        print(__doc__)
        return 2
    for path, wanted in regions(table).items():
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        new = render(text, wanted)
        if new != text:
            path.write_text(new, encoding="utf-8", newline="\n")
            print(f"boot-keys: wrote {path.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
