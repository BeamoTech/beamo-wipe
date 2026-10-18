"""Every inventory count uses the session language, including plural forms."""

from dataclasses import replace

import pytest

from beamo_wipe import inventory, lang
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.models import ExcludedDevice
from beamo_wipe.safety import selectable_disks


def _inventory(available, other=0):
    result = discovery_for_scenario("happy")
    targets = selectable_disks(result)[:available]
    return replace(
        result,
        disks=(result.boot, *targets),
        selectable=targets,
        excluded=tuple(
            ExcludedDevice(f"Extra {i}", (inventory.REASON_READ_ONLY,))
            for i in range(other)
        ),
    )


@pytest.mark.parametrize(
    "language,phrases",
    [
        ("en", ("No disks available to erase", "1 disk available to erase", "3 disks available to erase")),
        ("fr", ("Aucun disque disponible à effacer", "1 disque disponible à effacer", "3 disques disponibles à effacer")),
        ("de", ("Keine Datenträger zum Löschen verfügbar", "1 Datenträger zum Löschen verfügbar", "3 Datenträger zum Löschen verfügbar")),
    ],
)
@pytest.mark.parametrize("available,index", [(0, 0), (1, 1), (3, 2)])
def test_available_count_is_in_session_language(language, phrases, available, index):
    lang.set_language(language)
    result = _inventory(available)
    assert inventory.count_summary(result).startswith(phrases[index])
    assert inventory.count_summary(result, spoken=True).startswith(phrases[index])


@pytest.mark.parametrize(
    "language,phrases",
    [
        ("en", ("1 other device not available", "2 other devices not available")),
        ("fr", ("1 autre appareil non disponible", "2 autres appareils non disponibles")),
        ("de", ("1 weiteres Gerät nicht verfügbar", "2 weitere Geräte nicht verfügbar")),
    ],
)
@pytest.mark.parametrize("other", [1, 2])
def test_other_device_count_is_in_session_language(language, phrases, other):
    lang.set_language(language)
    result = _inventory(1, other)
    assert phrases[other - 1] in inventory.count_summary(result)
    assert phrases[other - 1] in inventory.count_summary(result, spoken=True)
