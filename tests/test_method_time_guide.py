# SPDX-License-Identifier: GPL-3.0-or-later
"""Method-screen rough time guide: bounds, rounding, wording and hiding.

Pure functions and fake Disk records only. The guide is presentation text;
it never gates an erase, never reaches evidence, and never feeds the live
estimate on the Working screen.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from beamo_wipe import copy as C
from beamo_wipe import lang
from beamo_wipe import progress as P
from beamo_wipe.methods import METHODS
from beamo_wipe.models import Disk, DiskKind, MethodId

TB = 1_000_204_886_016  # demo WDC 1 TB hard disk
GB256 = 256_060_514_304


def _disk(size_bytes=TB, label="1000", kind=DiskKind.HDD, bus="SATA") -> Disk:
    return Disk(
        path="/dev/sdx", name="sdx", model="Fake", serial="FAKE1",
        size_bytes=size_bytes, size_gb_label=label, kind=kind, bus=bus,
        label="",
    )


@pytest.fixture(autouse=True)
def _english():
    lang.set_language("en")
    yield
    lang.set_language("en")


def _passes(method: MethodId) -> int:
    spec = METHODS[method]
    return spec.overwrite_passes + spec.verification_passes


def test_pass_counts_come_from_the_method_plan():
    # Everyday and Three overwrites verify the last pass (one extra read).
    assert _passes(MethodId.EVERYDAY) == 2
    assert _passes(MethodId.EXTRA) == 4
    assert _passes(MethodId.QUICK_ZERO) == 1


def test_bounds_use_documented_rates():
    fast, slow = P.guide_seconds(TB, DiskKind.HDD, False, 2)
    assert fast == pytest.approx(2 * TB / 200e6)
    assert slow == pytest.approx(2 * TB / 60e6)
    fast, slow = P.guide_seconds(GB256, DiskKind.NVME, False, 1)
    assert fast == pytest.approx(GB256 / 1500e6)
    assert slow == pytest.approx(GB256 / 150e6)
    fast, slow = P.guide_seconds(GB256, DiskKind.SSD, False, 1)
    assert fast == pytest.approx(GB256 / 500e6)
    assert slow == pytest.approx(GB256 / 100e6)


def test_unknown_rotation_uses_the_widest_range():
    fast, slow = P.guide_seconds(TB, DiskKind.UNKNOWN, False, 1)
    assert fast == pytest.approx(TB / 500e6)
    assert slow == pytest.approx(TB / 60e6)
    assert P.guide_seconds(TB, "something-else", False, 1) == (fast, slow)


def test_usb_halves_only_the_slow_bound():
    plain = P.guide_seconds(TB, DiskKind.HDD, False, 2)
    usb = P.guide_seconds(TB, DiskKind.HDD, True, 2)
    assert usb[0] == pytest.approx(plain[0])
    assert usb[1] == pytest.approx(plain[1] * 2)


@pytest.mark.parametrize("size", [0, -1, None, True, 1.5e12, "1000"])
def test_unknown_or_invalid_size_has_no_bounds(size):
    assert P.guide_seconds(size, DiskKind.HDD, False, 2) is None
    assert P.time_guide(size, DiskKind.HDD, False, 2) is None


@pytest.mark.parametrize("passes", [0, -1, None, True, 2.0])
def test_invalid_pass_count_has_no_bounds(passes):
    assert P.guide_seconds(TB, DiskKind.HDD, False, passes) is None


@pytest.mark.parametrize(
    "fast,slow,want",
    [
        # Minutes under 1.5 h: 1-minute steps below 10, then 5-minute steps.
        (2, 10, P.TimeGuide(1, "minutes", 2, "minutes", False)),
        (341.4, 3414.0, P.TimeGuide(5, "minutes", 60, "minutes", False)),
        (1024.0, 5121.0, P.TimeGuide(15, "minutes", 90, "minutes", False)),
        # Low rounds down, high rounds up, each in its own unit.
        (5001.0, 16670.0, P.TimeGuide(80, "minutes", 5, "hours", False)),
        (10002.0, 33340.0, P.TimeGuide(2, "hours", 10, "hours", False)),
        (20004.0, 66680.0, P.TimeGuide(5, "hours", 19, "hours", True)),
        # Hours under 48 h; days beyond.
        (160000.0, 533333.0, P.TimeGuide(44, "hours", 7, "days", True)),
        (200000.0, 600000.0, P.TimeGuide(2, "days", 7, "days", True)),
        # 1.5 h switches to hours; exactly 10 hours is not "overnight".
        (5400.0, 36000.0, P.TimeGuide(1, "hours", 10, "hours", False)),
        (3600.0, 36001.0, P.TimeGuide(60, "minutes", 11, "hours", True)),
    ],
)
def test_rounding_to_friendly_units(fast, slow, want):
    assert P.guide_range(fast, slow) == want


@pytest.mark.parametrize(
    "fast,slow",
    [(0, 10), (10, 5), (-1, 5), (1, float("inf")), (float("nan"), 5)],
)
def test_range_rejects_impossible_bounds(fast, slow):
    assert P.guide_range(fast, slow) is None


def test_one_terabyte_hard_disk_wording_per_method():
    disk = _disk()
    assert C.method_time_guide(MethodId.EVERYDAY, disk) == (
        "Rough guide for this 1 TB hard disk (not promised): 2–10 hours."
    )
    assert C.method_time_guide(MethodId.EXTRA, disk) == (
        "Rough guide for this 1 TB hard disk (not promised): 5–19 hours. "
        "Plan to leave it running overnight or longer."
    )
    assert C.method_time_guide(MethodId.QUICK_ZERO, disk) == (
        "Rough guide for this 1 TB hard disk (not promised): 80 minutes to 5 hours."
    )


def test_solid_state_wording_and_minutes():
    nvme = _disk(GB256, "256", DiskKind.NVME, "NVMe")
    sata = _disk(GB256, "256", DiskKind.SSD, "SATA")
    assert C.method_time_guide(MethodId.EVERYDAY, nvme) == (
        "Rough guide for this 256 GB SSD (not promised): 5–60 minutes."
    )
    assert C.method_time_guide(MethodId.EVERYDAY, sata) == (
        "Rough guide for this 256 GB SSD (not promised): 15–90 minutes."
    )


def test_usb_disk_gets_the_slower_bound():
    usb = _disk(bus="USB")
    assert C.method_time_guide(MethodId.EVERYDAY, usb) == (
        "Rough guide for this 1 TB hard disk (not promised): 2–19 hours. "
        "Plan to leave it running overnight or longer."
    )


def test_unknown_rotation_says_disk():
    disk = _disk(500_107_862_016, "500", DiskKind.UNKNOWN, "SATA")
    text = C.method_time_guide(MethodId.EVERYDAY, disk)
    assert text.startswith("Rough guide for this 500 GB disk (not promised): ")
    assert "hard disk" not in text and "SSD" not in text


def test_large_disk_reads_in_days_and_tenths_of_terabytes():
    disk = _disk(8_001_563_222_016, "8002", DiskKind.HDD, "SATA")
    assert C.method_time_guide(MethodId.EXTRA, disk) == (
        "Rough guide for this 8002 GB hard disk (not promised): 44 hours to 7 days. "
        "Plan to leave it running overnight or longer."
    )
    tenth = _disk(1_500_301_910_016, "1500", DiskKind.HDD, "SATA")
    assert "this 1.5 TB hard disk" in C.method_time_guide(MethodId.EVERYDAY, tenth)


@pytest.mark.parametrize(
    "changes",
    [
        {"size_gb_label": ""},
        {"size_gb_label": "unknown"},
        {"size_gb_label": "0"},
        {"size_bytes": 0},
        {"size_bytes": -5},
    ],
)
def test_hidden_when_size_is_unknown(changes):
    disk = replace(_disk(), **changes)
    for method in METHODS:
        assert C.method_time_guide(method, disk) == ""


def test_hidden_without_a_disk_or_method():
    assert C.method_time_guide(MethodId.EVERYDAY, None) == ""
    assert C.method_time_guide("not-a-method", _disk()) == ""  # type: ignore[arg-type]


def test_guide_never_promises():
    for method in METHODS:
        for disk in (_disk(), _disk(GB256, "256", DiskKind.NVME, "NVMe")):
            text = C.method_time_guide(method, disk).lower()
            assert text.startswith("rough guide")
            assert "not promised" in text
            for word in ("guarantee", "exactly", "will take", "only takes"):
                assert word not in text


@pytest.mark.parametrize(
    "code,hours,hedge,overnight",
    [
        ("fr", "heures", "non promise", "toute la nuit"),
        ("de", "Stunden", "ohne Gewähr", "über Nacht"),
        ("es", "horas", "no se promete", "toda la noche"),
        ("it", "ore", "non è una promessa", "tutta la notte"),
    ],
)
def test_translated_guides(code, hours, hedge, overnight):
    lang.set_language(code)
    disk = _disk()
    everyday = C.method_time_guide(MethodId.EVERYDAY, disk)
    extra = C.method_time_guide(MethodId.EXTRA, disk)
    quick = C.method_time_guide(MethodId.QUICK_ZERO, disk)
    assert hours in everyday and hedge in everyday and "1 TB" in everyday
    assert overnight in extra and overnight not in everyday
    assert any(word in quick for word in ("minutes", "Minuten", "minutos", "minuti"))
    assert "Rough guide" not in everyday + extra + quick


def test_every_supported_language_renders_a_guide():
    for code in lang.LANGUAGE_ORDER:
        lang.set_language(code)
        for method in METHODS:
            text = C.method_time_guide(method, _disk())
            assert text and "{" not in text and "1 TB" in text
