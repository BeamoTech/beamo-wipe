# SPDX-License-Identifier: GPL-3.0-or-later
"""Customer guidance: time expectations, interrupted erases, hidden RAID storage."""

from __future__ import annotations

import pytest

from beamo_wipe import copy as C
from beamo_wipe import inventory
from beamo_wipe.locales import de, es, fr, it


def _values(module, key):
    """Every translation of `key` across the locale's per-module sections."""
    found = [section[key] for section in module.STRINGS.values()
             if isinstance(section, dict) and key in section]
    assert found, key
    return found


def test_method_screen_sets_expectations_without_promising_a_time():
    assert "many hours" in C.METHOD_LEAD
    assert "not promised" in C.METHOD_LEAD
    for word in ("guarantee", "minutes", "fast"):
        assert word not in C.METHOD_LEAD.lower()


def test_interrupted_erase_says_to_start_again():
    assert "does not resume automatically" in C.POWER_EVENTS
    assert "start it again from the beginning" in C.POWER_EVENTS


def test_empty_list_explains_hidden_raid_storage_without_prescribing_firmware_changes():
    text = inventory.EMPTY_STEPS
    for word in ("Intel RST", "VMD", "RAID", "Ask support before changing firmware settings"):
        assert word in text
    assert "Do not bypass protection." in text


@pytest.mark.parametrize("module,hours,restart,raid", [
    (fr, "heures", "recommencez", "Intel RST, VMD ou RAID"),
    (de, "Stunden", "erneut von vorn", "Intel RST, VMD oder RAID"),
    (es, "horas", "desde el principio", "Intel RST, VMD o RAID"),
    (it, "ore", "dall’inizio", "Intel RST, VMD o RAID"),
])
def test_translations_carry_the_same_guidance(module, hours, restart, raid):
    assert all(hours in text for text in _values(module, "METHOD_LEAD"))
    assert all(restart in text for text in _values(module, "POWER_EVENTS"))
    assert all(raid in text for text in _values(module, "EMPTY_STEPS"))
