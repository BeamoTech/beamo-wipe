# SPDX-License-Identifier: GPL-3.0-or-later
"""Test helper: read the inline script of our own generated preview page.

The web preview (``gallery.gallery_html``) is HTML this project generates,
with exactly one ``<script>`` element. Tests inspect that script's source.
This is not an HTML filter or sanitizer and must never be used as one.
"""

from __future__ import annotations


def inline_script(html: str) -> str:
    """Return the single inline script of a generated preview page."""
    assert html.count("<script>") == 1 and html.count("</script>") == 1, (
        "the generated preview page must have exactly one inline script"
    )
    return html.split("<script>", 1)[1].split("</script>", 1)[0]
