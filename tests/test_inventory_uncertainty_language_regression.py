"""Uncertainty survives translated discovery and later language changes."""

from dataclasses import replace

import pytest

from beamo_wipe import discover, inventory, lang
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import ExcludedDevice
from test_excluded_inventory import node


@pytest.mark.parametrize("language", lang.LANGUAGE_ORDER)
def test_translated_unknown_capacity_retains_uncertainty_warning(language):
    lang.set_language(language)
    result = discover.parse_lsblk_json(
        {"blockdevices": [
            node("sdb", tran="usb", mountpoints=["/run/live/medium"]),
            node("sde", size=None),
        ]},
        boot_path="/dev/sdb",
    )
    assert inventory.REASON_CAPACITY_UNKNOWN in result.excluded[-1].reasons
    assert inventory.UNCERTAIN_NOTE in inventory.count_summary(result)


@pytest.mark.parametrize("language", lang.LANGUAGE_ORDER)
def test_definite_exclusion_reasons_do_not_claim_uncertain_identity(language):
    lang.set_language(language)
    result = discover.parse_lsblk_json(
        {"blockdevices": [
            node("sdb", tran="usb", mountpoints=["/run/live/medium"]),
            node("sde", size=0, ro=True, mountpoints=["/media/data"]),
        ]},
        boot_path="/dev/sdb",
    )
    assert inventory.UNCERTAIN_NOTE not in inventory.count_summary(result)


@pytest.mark.parametrize("source_language", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("display_language", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("reason_kind", ["capacity", "eligibility", "identity"])
def test_uncertain_inventory_snapshot_survives_language_switch(
    source_language, display_language, reason_kind
):
    lang.set_language(source_language)
    reason = {
        "capacity": inventory.REASON_CAPACITY_UNKNOWN,
        "eligibility": inventory.REASON_ELIGIBILITY,
        "identity": discover.IDENTITY_UNCONFIRMED,
    }[reason_kind]
    result = replace(
        discovery_for_scenario("happy"),
        excluded=(ExcludedDevice("Unknown device", (reason,)),),
    )
    lang.set_language(display_language)
    assert inventory.UNCERTAIN_NOTE in inventory.count_summary(result)
    assert inventory.UNCERTAIN_NOTE in inventory.count_summary(result, spoken=True)
