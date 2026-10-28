# SPDX-License-Identifier: GPL-3.0-or-later
"""Text made before a language switch is shown in the current language.

Discovery often runs before the owner picks a language, and a language change
never re-runs it, so the snapshot keeps the reasons and kind labels it was made
with. Display only: eligibility, the excluded list and the reasons as data are
unchanged. Fake disks only; nothing is erased.
"""

from __future__ import annotations

import pytest

from beamo_wipe import discover, inventory, lang, progress
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import ExcludedDevice
from beamo_wipe.wizard import format_progress_percent

TRANSLATED = tuple(code for code in lang.LANGUAGE_ORDER if code != "en")
REASONS = tuple(name for name in lang.keys("fr", "inventory") if name.startswith("REASON_"))


@pytest.fixture(autouse=True)
def _english_after():
    yield
    lang.set_language("en")


def _value(code, module, name):
    return lang.english(module, name) if code == "en" else lang.translated(code, module, name)


def _nested_partition(code, *reason_names):
    lang.set_language(code)
    kind = inventory.KIND_PART
    return ExcludedDevice(
        "Beamo Wipe | 16 GB | USB | ID: BEAMOUSB001",
        tuple(getattr(inventory, name) for name in reason_names),
        path="/dev/sdz1",
        parent_path="/dev/sdz",
        kind_label=kind,
        summary=f"{kind} · 16 GB · BEAMO_WIPE",
    )


def test_every_reason_is_covered_and_labels_are_unambiguous():
    assert {name for module, name in inventory._REASON_NAMES if module == "inventory"} == set(REASONS)
    for group in (inventory._REASON_NAMES, inventory._KIND_NAMES):
        owner: dict[str, str] = {}
        for module, name in group:
            for code in lang.LANGUAGE_ORDER:
                value = _value(code, module, name)
                # One text never names two different reasons or kinds.
                assert owner.setdefault(value, name) == name, (code, value)


@pytest.mark.parametrize("made", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("shown", lang.LANGUAGE_ORDER)
def test_nested_card_reads_in_the_current_language(made, shown):
    device = _nested_partition(made, "REASON_UNSUPPORTED", "REASON_MOUNTED")
    lang.set_language(shown)
    # The generic whole-disk reason stays silent on a nested card; others show.
    assert inventory.nested_reason_text(device) == inventory.REASON_MOUNTED
    assert inventory.nested_heading(device) == f"{inventory.KIND_PART} · 16 GB · BEAMO_WIPE"
    assert inventory.explanation(device) == (
        f"{device.identity}\n"
        + inventory.CANNOT_ERASE.format(
            reasons=f"{inventory.REASON_UNSUPPORTED}; {inventory.REASON_MOUNTED}"
        )
    )


@pytest.mark.parametrize("made", lang.LANGUAGE_ORDER)
def test_every_reason_maps_from_the_language_it_was_made_in(made):
    lang.set_language(made)
    texts = {name: getattr(inventory, name) for name in REASONS}
    texts["IDENTITY_UNCONFIRMED"] = discover.IDENTITY_UNCONFIRMED
    for shown in lang.LANGUAGE_ORDER:
        lang.set_language(shown)
        for name, text in texts.items():
            module = discover if name == "IDENTITY_UNCONFIRMED" else inventory
            assert inventory.current_reason(text) == getattr(module, name), (made, shown, name)


def test_unknown_text_passes_through_unchanged():
    lang.set_language("de")
    assert inventory.current_reason("vendor-specific note") == "vendor-specific note"
    device = ExcludedDevice("x", (), summary="Widget · 1 GB")
    assert inventory.nested_heading(device) == "Widget · 1 GB"
    assert inventory.nested_heading(ExcludedDevice("identity only", ())) == "identity only"


@pytest.mark.parametrize("code", TRANSLATED)
def test_demo_inventory_scanned_in_english_reads_in_the_chosen_language(code):
    wizard = make_demo_wizard()  # Discovery runs before any language choice.
    english_reasons = {lang.english("inventory", name) for name in REASONS}
    boot = wizard.discovery.boot
    snapshot = [r for d in wizard.discovery.excluded for r in d.reasons]
    assert set(snapshot) & english_reasons  # The snapshot really is English.
    assert wizard.set_language(code)
    current = {getattr(inventory, name) for name in REASONS}
    shown = "\n".join(
        (
            inventory.card_nesting_text(wizard.nested_components(boot)),
            inventory.full_text(wizard.other_devices),
        )
    )
    leaked = {text for text in english_reasons - current if text in shown}
    assert not leaked, (code, leaked)
    assert "Cannot erase" not in shown
    # Display only: the snapshot itself is unchanged.
    assert [r for d in wizard.discovery.excluded for r in d.reasons] == snapshot
    assert wizard.selected is None and not wizard.runner.started


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_old_percent_suffix_is_translated_in_the_preview(code):
    from beamo_wipe.gallery import _serialize_progress

    lang.set_language(code)
    view = progress.ProgressView("Writing", 42, 60, stale_for=900, percent_is_old=True)
    text = _serialize_progress(view)["percentText"]
    assert text == progress.OLD_PERCENT.format(percent=format_progress_percent(42))
    assert ("(old)" in text) == (code == "en")
