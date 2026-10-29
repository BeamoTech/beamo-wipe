# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional report line for nwipe 0.42's logged random-data generator.

Fake nwipe log text only. Source: nwipe v0.42 (6082bde060091e66365d852a1877f2ee80c67105)
options.c nwipe_options_log(), nwipe.c auto-selection, prng.c labels, logging.c format.
"""

from __future__ import annotations

import copy
import html
import json

import pytest

from beamo_wipe import lang, outcomes
from beamo_wipe.models import MethodId
from beamo_wipe.nwipe_runner import (
    NWIPE_PRNG_AUTO_LABELS,
    NWIPE_PRNG_LOG_NAMES,
    completion_for_method,
    logged_random_generator,
)
from beamo_wipe.outcomes import present_evidence
from test_result_presentations import ERASED, STATUS, case_evidence

STAMP = "[2026/10/27 09:15:02]"
HEADER = f"{STAMP}  notice: Program options are set as follows..."
FORCE = f"{STAMP}  notice:   force        = 0 (off)"
METHOD = f"{STAMP}  notice:   method       = PRNG Stream"

# Exact strings from options.c nwipe_options_log() at the pinned commit.
MANIFEST_NAMES = (
    "Mersenne Twister",
    "Lagged Fibonacci generator",
    "XORoshiro-256",
    "SplitMix64",
    "AES-256-CTR (CSPRNG)",
    "ISAAC (CSPRNG)",
    "ISAAC-64 (CSPRNG)",
    "ChaCha20 (CSPRNG)",
)
# Exact prng.c nwipe_prng_t labels at the pinned commit.
PRNG_C_LABELS = (
    "Mersenne Twister",
    "ISAAC (CSPRNG)",
    "ISAAC-64 (CSPRNG)",
    "Lagged Fibonacci",
    "XORoshiro-256",
    "SplitMix64",
    "AES-256-CTR (CSPRNG)",
    "ChaCha20 (CSPRNG)",
)


def prng_line(name: str) -> str:
    return f"{STAMP}  notice:   prng         = {name}"


def auto_line(label: str) -> str:
    return f"{STAMP}    info: Auto-selected fastest PRNG: {label}"


def manifest(name: str, *, auto: str | None = None) -> str:
    lines = []
    if auto is not None:
        lines.append(auto_line(auto))
    lines += [HEADER, FORCE, prng_line(name), METHOD]
    return "\n".join(lines) + "\n"


def test_allowlists_match_the_pinned_nwipe_source():
    assert NWIPE_PRNG_LOG_NAMES == frozenset(MANIFEST_NAMES)
    assert tuple(NWIPE_PRNG_AUTO_LABELS) == PRNG_C_LABELS
    assert set(NWIPE_PRNG_AUTO_LABELS.values()) == set(MANIFEST_NAMES)
    assert NWIPE_PRNG_AUTO_LABELS["Lagged Fibonacci"] == "Lagged Fibonacci generator"
    assert "Unknown" not in NWIPE_PRNG_LOG_NAMES


@pytest.mark.parametrize("name", MANIFEST_NAMES)
def test_every_manifest_name_is_read_exactly(name):
    assert logged_random_generator(manifest(name)) == name


@pytest.mark.parametrize("label", PRNG_C_LABELS)
def test_matching_auto_selection_corroborates(label):
    name = NWIPE_PRNG_AUTO_LABELS[label]
    assert logged_random_generator(manifest(name, auto=label)) == name


@pytest.mark.parametrize(
    "text",
    [
        "",
        None,
        b"bytes",
        # No manifest: an auto-selection record alone is not the applied value.
        auto_line("SplitMix64") + "\n",
        # The manifest header must precede the record.
        prng_line("SplitMix64") + "\n" + HEADER + "\n",
        # nwipe's own unknown value, and names outside the allowlist.
        manifest("Unknown"),
        manifest("Lagged Fibonacci"),
        manifest("xoroshiro256_prng"),
        manifest("AES-256-CTR (CSPRNG) "),
        # Conflicting or repeated records.
        manifest("SplitMix64", auto="XORoshiro-256"),
        manifest("SplitMix64") + prng_line("SplitMix64") + "\n",
        manifest("SplitMix64") + prng_line("XORoshiro-256") + "\n",
        auto_line("SplitMix64") + "\n" + manifest("SplitMix64", auto="SplitMix64"),
        # Cut-off final record, CRLF, other levels and spacing are not exact.
        "\n".join([HEADER, prng_line("SplitMix64")]),
        manifest("SplitMix64").replace("\n", "\r\n"),
        manifest("SplitMix64").replace("  notice:   prng", "    info:   prng"),
        manifest("SplitMix64").replace("prng         =", "prng =", 1),
        manifest("SplitMix64").replace(STAMP, "[2026-10-27 09:15:02]"),
        # Bare continuations (for example text after LF in a device model).
        HEADER + "\n" + "  prng         = SplitMix64\n",
    ],
)
def test_anything_but_one_exact_record_is_unknown(text):
    assert logged_random_generator(text) is None


# Verbatim records from a captured nwipe 0.42 KVM run (committed at
# docs/evidence/usb-lab-20260907/kvm-followup/final-records/updated-boot/
# nwipe-boundary.txt, lines 28-34 and 77-87); stdout lines are not log records.
CAPTURED = (
    "Selected PRNG: SplitMix64\n"
    ".Auto-selected fastest PRNG: SplitMix64\n"
    "[2026/09/07 22:16:27]  notice: Initialising Additive Lagged Fibonacci Generator (PRNG)\n"
    "[2026/09/07 22:16:28]  notice: Initialising XORoshiro-256 (PRNG)\n"
    "[2026/09/07 22:16:29]  notice: Initialising SplitMix64 (PRNG)\n"
    "[2026/09/07 22:16:30]  notice: Initialising AES-256-CTR (CSPRNG)\n"
    "[2026/09/07 22:16:31]  notice: Initialising ChaCha20 (CSPRNG)\n"
    "[2026/09/07 22:16:31]  notice: Self-test has passed for ChaCha20 (CSPRNG)\n"
    "[2026/09/07 22:16:32]    info: Auto-selected fastest PRNG: SplitMix64\n"
    "[2026/09/07 22:16:33]  notice: Found /dev/loop0, VIRT    , Loopback device,  268 MB, "
    "S/N=????????????????????\n"
    "[2026/09/07 22:16:33]  notice: Program options are set as follows...\n"
    "[2026/09/07 22:16:33]  notice:   force        = 0 (off)\n"
    "[2026/09/07 22:16:33]  notice:   autonuke     = 1 (on)\n"
    "[2026/09/07 22:16:33]  notice:   autopoweroff = 0 (off)\n"
    "[2026/09/07 22:16:33]  notice:   do not perform a final blank pass\n"
    "[2026/09/07 22:16:33]  notice:   do not wait for a key before exiting\n"
    "[2026/09/07 22:16:33]  notice:   do not show GUI interface\n"
    "[2026/09/07 22:16:33]  notice:   banner       = nwipe 0.42\n"
    "[2026/09/07 22:16:33]  notice:   prng         = SplitMix64\n"
    "[2026/09/07 22:16:33]  notice:   method       = Fill With Zeros\n"
)


def test_captured_nwipe_042_records_parse():
    assert logged_random_generator(CAPTURED) == "SplitMix64"
    # The benchmark's own "Initialising ..." records never count as the choice.
    benchmark_only = "".join(
        line + "\n" for line in CAPTURED.splitlines() if "Initialising" in line
    )
    assert logged_random_generator(HEADER + "\n" + benchmark_only) is None


def test_device_text_cannot_supply_a_record():
    # nwipe prints at most a 40-byte model; a full record needs more.
    shortest = prng_line(min(MANIFEST_NAMES, key=len))
    assert len(shortest) > 40
    assert len(HEADER) > 40


def _case(method, log, code="verified"):
    exit_code = 0
    return (code, method, exit_code, log, False, False)


@pytest.mark.parametrize("method", [MethodId.EVERYDAY, MethodId.EXTRA])
def test_random_data_methods_record_the_generator(method):
    log = manifest("XORoshiro-256") + STATUS + ERASED
    wiz, ev, normalized = case_evidence(_case(method, log))
    assert ev["nwipe"]["prng"] == "XORoshiro-256"
    assert set(ev["nwipe"]) == {"version", "argv_redacted", "prng"}
    # Display only: the outcome and completion check are unchanged.
    view = present_evidence(ev)
    assert view == outcomes.VIEWS["verified"]
    assert completion_for_method(0, normalized, wiz.selected.path, method)[2] == "completed"
    _, plain, _ = case_evidence(_case(method, STATUS + ERASED))
    assert set(plain["nwipe"]) == {"version", "argv_redacted"}
    assert present_evidence(plain) == view


def test_saved_record_with_generator_recovers_unchanged(tmp_path):
    from beamo_wipe.evidence import recover_result, write_evidence_atomic

    logfile = tmp_path / "nwipe.log"
    log = manifest("ISAAC-64 (CSPRNG)") + STATUS + ERASED
    _, ev, normalized = case_evidence(_case(MethodId.EVERYDAY, log), str(logfile))
    assert ev["nwipe"]["prng"] == "ISAAC-64 (CSPRNG)"
    logfile.write_text(normalized)
    path = write_evidence_atomic(ev, log_dir=tmp_path)
    assert recover_result(path) == outcomes.VIEWS["verified"]
    saved = json.loads(path.read_text())
    assert saved["nwipe"]["prng"] == "ISAAC-64 (CSPRNG)"
    # The value is re-derivable from the exact snapshot the record digests.
    assert logged_random_generator(normalized) == saved["nwipe"]["prng"]


def test_zero_fill_never_records_a_generator():
    log = manifest("XORoshiro-256") + STATUS + ERASED
    _, ev, _ = case_evidence(_case(MethodId.QUICK_ZERO, log, "unverified"))
    assert present_evidence(ev) == outcomes.VIEWS["unverified"]
    assert "prng" not in ev["nwipe"]


def _summary(ev):
    from beamo_wipe.result_summary import build_result_summary

    return build_result_summary(ev, evidence_sha256="a" * 64)


@pytest.mark.parametrize("code", lang.LANGUAGE_ORDER)
def test_report_line_follows_overwrites_in_every_language(code):
    from beamo_wipe import result_summary as S
    from beamo_wipe.result_summary import build_result_report_html

    try:
        lang.set_language(code)
        log = manifest("AES-256-CTR (CSPRNG)") + STATUS + ERASED
        _, ev, _ = case_evidence(_case(MethodId.EVERYDAY, log))
        lines = _summary(ev).splitlines()
        line = f"{S.H_RANDOM_GENERATOR}: AES-256-CTR (CSPRNG)"
        assert line in lines
        assert lines.index(line) == lines.index(f"{S.H_OVERWRITES}: 1") + 1
        page = build_result_report_html(ev, evidence_sha256="a" * 64)
        assert (
            f'<th scope="row">{html.escape(S.H_RANDOM_GENERATOR, quote=True)}</th>'
            "<td>AES-256-CTR (CSPRNG)</td>"
        ) in page
        if code != "en":
            assert S.H_RANDOM_GENERATOR == lang.translated(
                code, "result_summary", "H_RANDOM_GENERATOR"
            )
            assert S.H_RANDOM_GENERATOR != "Random data generator"
    finally:
        lang.set_language("en")


def test_report_omits_unknown_or_irrelevant_generators():
    from beamo_wipe import result_summary as S

    log = manifest("SplitMix64") + STATUS + ERASED
    _, ev, _ = case_evidence(_case(MethodId.EVERYDAY, log))
    assert f"{S.H_RANDOM_GENERATOR}: SplitMix64" in _summary(ev)
    for value in (None, "", "Unknown", "SplitMix64 ", "<b>x</b>", 7, ["SplitMix64"]):
        changed = copy.deepcopy(ev)
        changed["nwipe"]["prng"] = value
        assert S.H_RANDOM_GENERATOR not in _summary(changed), value
    missing = copy.deepcopy(ev)
    del missing["nwipe"]["prng"]
    assert S.H_RANDOM_GENERATOR not in _summary(missing)
    assert "unavailable" not in [
        line.split(": ", 1)[-1] for line in _summary(missing).splitlines()
        if line.startswith(S.H_RANDOM_GENERATOR)
    ]
    # Zero fill does not use the generator even if a record claims one.
    _, zero, _ = case_evidence(_case(MethodId.QUICK_ZERO, STATUS + ERASED, "unverified"))
    zero["nwipe"]["prng"] = "SplitMix64"
    assert S.H_RANDOM_GENERATOR not in _summary(zero)


def test_nothing_erased_results_do_not_name_a_generator():
    from beamo_wipe import result_summary as S

    _, ev, _ = case_evidence(
        ("open_failed", MethodId.EVERYDAY, 0, "Unable to open device '{path}'.", False, False)
    )
    assert present_evidence(ev).code == "open_failed"
    ev["nwipe"]["prng"] = "SplitMix64"
    assert S.H_RANDOM_GENERATOR not in _summary(ev)
    _, failed, _ = case_evidence(
        ("engine_failed", MethodId.EVERYDAY, 0, "{path}: >>> FAILURE! <<<", False, False)
    )
    failed["nwipe"]["prng"] = "SplitMix64"
    assert f"{S.H_RANDOM_GENERATOR}: SplitMix64" in _summary(failed)


def test_sharing_copy_drops_the_generator():
    from beamo_wipe import result_summary as S
    from beamo_wipe.privacy import SHARE_JSON, SHARE_SUMMARY, make_sharing_copy
    from beamo_wipe.support_export import _bundle_files

    log = manifest("ChaCha20 (CSPRNG)") + STATUS + ERASED
    _, ev, normalized = case_evidence(_case(MethodId.EVERYDAY, log))
    share = make_sharing_copy(ev)
    assert "prng" not in share["nwipe"]
    assert present_evidence(share) == outcomes.VIEWS["verified"]
    bundle = _bundle_files(
        json.dumps(ev).encode(), normalized.encode(), "complete", privacy_reduced=True
    )
    owner = bundle["RESULT.txt"].decode()
    assert f"{S.H_RANDOM_GENERATOR}: ChaCha20 (CSPRNG)" in owner
    assert "ChaCha20" in bundle["REPORT.html"].decode()
    for name in (SHARE_JSON, SHARE_SUMMARY):
        assert name in bundle, name
        assert "ChaCha20" not in bundle[name].decode(), name
    assert S.H_RANDOM_GENERATOR not in bundle[SHARE_SUMMARY].decode()
