#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Require the two mixed-module GTK regressions to execute in hosted pytest."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED = (
    ("test_compat_story", "test_what_screen_keeps_title_and_shows_this_usb_line"),
    ("test_separate_footer_actions", "test_assist_nav_names_do_not_rewrite_result_heading"),
)


def check(report: Path) -> None:
    cases = list(ET.parse(report).getroot().iter("testcase"))
    for module, name in REQUIRED:
        matches = [case for case in cases
                   if case.get("classname", "").rsplit(".", 1)[-1] == module
                   and case.get("name") == name]
        if len(matches) != 1 or any(
            child.tag in {"skipped", "failure", "error"}
            for case in matches for child in case
        ):
            raise RuntimeError(f"Mandatory GTK test must execute and pass exactly once: {module}::{name}")


if __name__ == "__main__":
    check(Path(sys.argv[1]))
