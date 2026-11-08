"""One boot-menu key table for every surface (#184).

desktop/bootkeys.json is the source. scripts/gen_boot_keys.py writes the
marked regions of the Boot helper pages, the launcher page and the boot card.
These tests fail when any of them drifts from the JSON, or when a brand key
list appears outside a generated region.
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TABLE = ROOT / "desktop" / "bootkeys.json"


def _gen():
    spec = importlib.util.spec_from_file_location("gen_boot_keys", ROOT / "scripts" / "gen_boot_keys.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


GEN = _gen()


def _table() -> dict:
    return json.loads(TABLE.read_text(encoding="utf-8"))


def test_no_consumer_drifted_from_the_table():
    assert GEN.drifted() == []


def test_every_consumer_has_each_region_once():
    for path, wanted in GEN.regions(_table()).items():
        text = path.read_text(encoding="utf-8")
        for region in wanted:
            assert text.count(f"<!-- boot-keys:{region} -->") == 1, (path, region)
            assert text.count(f"<!-- /boot-keys:{region} -->") == 1, (path, region)


def test_a_changed_key_is_detected_as_drift():
    table = _table()
    dell = next(b for b in table["brands"] if b["id"] == "dell")
    dell["keys"] = ["F10"]
    stale = GEN.drifted(table)
    names = {p.relative_to(ROOT).as_posix() for p in stale}
    assert {"helper/index.html", "helper/fr.html", "helper/de.html", "helper/es.html",
            "helper/it.html", "desktop/web/index.html", "docs/boot-card.md"} <= names


def test_a_hand_edit_in_a_region_is_detected(tmp_path, monkeypatch):
    page = ROOT / "helper" / "index.html"
    copy = tmp_path / "index.html"
    copy.write_text(page.read_text(encoding="utf-8").replace(
        '<tr><td>Dell</td><td class="key"><span class="kbd">F12</span></td></tr>',
        '<tr><td>Dell</td><td class="key"><span class="kbd">F2</span></td></tr>', 1), encoding="utf-8")
    regions = GEN.regions(_table())
    monkeypatch.setattr(GEN, "regions", lambda table: {copy: regions[page]})
    assert GEN.drifted() == [copy]


def test_every_brand_cites_a_source_and_the_doc_lists_it():
    doc = (ROOT / "docs" / "boot-keys.md").read_text(encoding="utf-8")
    for brand in _table()["brands"]:
        assert brand["sources"], brand["id"]
        for url in brand["sources"]:
            assert url.startswith("https://") and url in doc, (brand["id"], url)


def test_every_helper_language_has_its_words():
    table = _table()
    for lang in GEN.HELPERS:
        words = table["words"][lang]
        assert words["or"] and words["then"] and words["lead"], lang


KEY_LIST = re.compile(r"(Dell|Lenovo|Acer|ASUS|MSI|Gigabyte)[^<\n]{0,40}(F8|F9|F11|F12)\b")


@pytest.mark.parametrize("rel", ["helper/index.html", "helper/fr.html", "helper/de.html",
                                 "helper/es.html", "helper/it.html", "desktop/web/index.html"])
def test_no_hand_kept_brand_key_list_outside_the_regions(rel):
    text = (ROOT / rel).read_text(encoding="utf-8")
    stripped = re.sub(r"<!-- boot-keys:([\w-]+) -->.*?<!-- /boot-keys:\1 -->", "", text, flags=re.S)
    # Key caps are markup; compare the visible text.
    visible = re.sub(r"<[^>]+>", "", stripped)
    assert not KEY_LIST.search(visible), KEY_LIST.search(visible)


def test_launcher_shows_one_likely_key_and_never_claims_certainty():
    page = (ROOT / "desktop" / "web" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "desktop" / "web" / "app.js").read_text(encoding="utf-8")
    assert 'id="boot-key-hint"' in page and 'id="boot-key-more"' in page
    assert "<summary>Show more</summary>" in page
    assert "not a guarantee" in page
    assert "Examples only" in page
    # An unknown brand opens the table; a known brand closes it.
    assert '$("boot-key-more").open = !known;' in app
    hint = _table()["words"]["en"]["launcher_hint"]
    assert hint.startswith("Most {brand} computers: press {keys}")
