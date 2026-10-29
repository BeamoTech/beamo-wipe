# SPDX-License-Identifier: GPL-3.0-or-later
"""Every helper language is reachable from the USB's visible root folder.

The live system keeps helper/index.html and helper/<code>.html. The stick's
root names the English page START-HERE.html, so the translated pages are
copied beside it as START-HERE-<code>.html and their language links are
rewritten to those names. Regular temporary files only."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

import pytest

from test_iso_live_assets_pass20 import ASSETS, _fixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from stage_live_assets import (  # noqa: E402
    HELPER_LANGUAGES,
    README,
    link_root_helpers,
    root_helper_name,
)

ROOT_PAGES = {code: root_helper_name(code) for code in ("en", *HELPER_LANGUAGES)}
HREF = re.compile(r'href="([^"#:]+\.html)"')


def _real_page(code: str) -> str:
    name = "index.html" if code == "en" else f"{code}.html"
    return (ROOT / "helper" / name).read_text(encoding="utf-8")


def test_root_names_cover_every_shipped_helper_language():
    shipped = {"en"} | {path.stem for path in (ROOT / "helper").glob("*.html") if path.stem != "index"}
    assert set(ROOT_PAGES) == shipped
    assert ROOT_PAGES["en"] == "START-HERE.html"
    assert len(set(ROOT_PAGES.values())) == len(ROOT_PAGES)


@pytest.mark.parametrize("code", sorted(ROOT_PAGES))
def test_root_copies_link_only_to_root_pages(code):
    source = _real_page(code)
    linked = link_root_helpers(source.encode("utf-8")).decode("utf-8")
    targets = HREF.findall(linked)
    # Every other language is one click away, and nothing points at a name
    # that exists only inside the live system.
    assert set(targets) == set(ROOT_PAGES.values()) - {ROOT_PAGES[code]}
    assert not {"index.html", *(f"{c}.html" for c in HELPER_LANGUAGES)} & set(targets)
    # Only the links change.
    assert HREF.sub('href=""', linked) == HREF.sub('href=""', source)


def test_live_system_copies_keep_their_own_names():
    for code in ROOT_PAGES:
        targets = set(HREF.findall(_real_page(code)))
        expected = {"index.html", *(f"{c}.html" for c in HELPER_LANGUAGES)}
        expected.discard("index.html" if code == "en" else f"{code}.html")
        assert targets == expected


def test_readme_names_every_root_page():
    for name in ROOT_PAGES.values():
        assert name in README


def _write_linked_helpers(project: Path) -> None:
    for code in ROOT_PAGES:
        name = "index.html" if code == "en" else f"{code}.html"
        links = " ".join(
            f'<a href="{"index.html" if other == "en" else other + ".html"}">{other}</a>'
            for other in ROOT_PAGES if other != code
        )
        (project / "helper" / name).write_text(
            f"<html>{name}: not packaged; source status {links}</html>\n", encoding="utf-8"
        )


def test_staging_publishes_each_language_at_the_usb_root(tmp_path):
    project, live, _source = _fixture(tmp_path)
    _write_linked_helpers(project)
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(ASSETS), str(project), str(live)],
        cwd=project,
        env={**os.environ, "BUILD_ID": "local"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    binary = live / "config/includes.binary"
    share = live / "config/includes.chroot/usr/share/beamo-wipe/helper"
    present = set(os.listdir(binary))
    for code, root_name in ROOT_PAGES.items():
        assert root_name in present
        page = (binary / root_name).read_text(encoding="utf-8")
        assert "packaged" in page
        # Each root link resolves to a file in the same root folder.
        targets = set(HREF.findall(page))
        assert targets and targets <= present
        assert root_name not in targets
        live_name = "index.html" if code == "en" else f"{code}.html"
        inner = (share / live_name).read_text(encoding="utf-8")
        assert set(HREF.findall(inner)) <= set(os.listdir(share))


def test_license_files_named_by_source_offer_are_on_the_usb_root(tmp_path):
    from stage_live_assets import source_offer

    offer = source_offer("https://support.invalid").decode("utf-8")
    project, live, _source = _fixture(tmp_path)
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(ASSETS), str(project), str(live)],
        cwd=project,
        env={**os.environ, "BUILD_ID": "local"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    present = set(os.listdir(live / "config/includes.binary"))
    for name in ("LICENSE", "NOTICE", "THIRD_PARTY.md"):
        assert name in offer
        assert name in present


def _ignored_by_gitignore(relative: str) -> bool:
    """Plain-pattern subset of .gitignore matching (no negation needed here)."""
    from fnmatch import fnmatchcase

    for raw in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines():
        pattern = raw.strip()
        if not pattern or pattern.startswith(("#", "!")):
            continue
        pattern = pattern.lstrip("/").rstrip("/")
        if fnmatchcase(relative, pattern) or relative.startswith(pattern + "/"):
            return True
    return False


def test_every_generated_usb_root_file_is_git_ignored(tmp_path):
    # The release manifest refuses a dirty tree: a staged root file that git
    # does not ignore stopped CI run 40817302598 right after the ISO built.
    project, live, _source = _fixture(tmp_path)
    _write_linked_helpers(project)
    result = subprocess.run(  # noqa: S603
        [sys.executable, str(ASSETS), str(project), str(live)],
        cwd=project,
        env={**os.environ, "BUILD_ID": "local"},
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    staged = sorted(os.listdir(live / "config/includes.binary"))
    assert {"START-HERE-fr.html", "THIRD_PARTY.md"} <= set(staged)
    # Nothing in includes.binary is tracked: every staged file is generated.
    not_ignored = [
        name for name in staged
        if not _ignored_by_gitignore(f"packaging/live/config/includes.binary/{name}")
    ]
    assert not_ignored == []
