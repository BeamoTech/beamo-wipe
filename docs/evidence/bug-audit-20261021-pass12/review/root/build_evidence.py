"""Retain PASS12 only after the frozen complete local sequence succeeds."""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import re
import shutil
import subprocess
import xml.etree.ElementTree as E

repo = Path("/workspace/beamo-wipe")
r = Path(__file__).parent
w = r.parent
out = repo / "docs/evidence/bug-audit-20261021-pass12"
load = lambda path: json.loads(path.read_text())
freeze = load(r / "final-freeze.json")
assert load(r / "final-sequence.status.json")["exit_code"] == 0
assert load(r / "final-tests.status.json")["exit_code"] == 0
assert not out.exists(), "retain once; preserve any failed attempt before correction"
source = load(r / "final-source-sha256.json")
assert len(source) == 825
assert all(hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest for name, digest in source.items())
assert hashlib.sha256((r / "final-source-sha256.json").read_bytes()).hexdigest() == freeze["source_manifest_sha256"]

groups = [
    "final-new-regressions", "final-preference-independent",
    "final-doctor-independent", "final-doctor-reviewer",
    "final-model-discovery", "final-model-launch_reuse_matrix",
    "final-model-terminal_handoff_model", "final-model-journal_admission_model",
    "final-lint", "final-preview", "final-negative", "doctor-test", "doctor-desktop",
    "final-go-new", "final-go-root-native-probe", "final-go-reviewer-parser-probe",
    "final-go-reviewer-readiness-probe", "final-go-epoch-model", "final-go-race",
    "final-go-vet", "final-go-fuzz", "final-windows-test-build",
    "final-desktop-build", "actual-preview-inspect", "artifact-inspection",
    "system-browser-tests", "final-tests",
]
statuses = {name: load(r / (name + ".status.json")) for name in groups}
assert all(record["exit_code"] == 0 for record in statuses.values())
canonical_log = (r / "final-tests.log").read_text()
assert "[ci-hosted] PASS phase=tests" in canonical_log
assert "warnings summary" not in canonical_log
assert not re.search(r"\b\d+ warnings?\b|\b(?:DeprecationWarning|ResourceWarning|RuntimeWarning|SyntaxWarning|UserWarning|PytestUnraisableExceptionWarning)\b", canonical_log)


def report(path, passed, skipped):
    cases = list(E.parse(path).iter("testcase"))
    ids = {(case.get("classname"), case.get("name")) for case in cases}
    assert len(cases) == len(ids) == passed + skipped
    assert all(case.find(kind) is None for case in cases for kind in ("failure", "error"))
    skips = [case for case in cases if case.find("skipped") is not None]
    assert len(skips) == skipped
    return {
        "cases": len(cases), "passed": passed, "skipped": skipped,
        "failures": 0, "errors": 0,
        "junit_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "skips": [
            {"id": case.get("classname") + "::" + case.get("name"),
             "message": case.find("skipped").get("message")}
            for case in skips
        ],
    }


reports = {
    "final-tests.xml": report(r / "final-tests.xml", 11797, 28),
    "final-tests.xml.orca.xml": report(r / "final-tests.xml.orca.xml", 1, 0),
}
new_cases = list(E.parse(r / "final-new-regressions.xml").iter("testcase"))
assert len(new_cases) == 28 and all(case.find(kind) is None for case in new_cases for kind in ("failure", "error", "skipped"))

go_rows = [json.loads(line) for line in (r / "final-go-race.log").read_text().splitlines() if line.startswith("{")]
go_pass = {(row.get("Package"), row["Test"]) for row in go_rows if row.get("Action") == "pass" and row.get("Test")}
go_skip = {(row.get("Package"), row["Test"]) for row in go_rows if row.get("Action") == "skip" and row.get("Test")}
assert len(go_pass) == 459 and len(go_skip) == 2

out.mkdir(parents=True)


def retain(src, target, compress=False):
    destination = out / (target + (".gz" if compress else ""))
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    destination.write_bytes(gzip.compress(data, mtime=0) if compress else data)


retain(r / "final-source-sha256.json", "source-sha256.json")
for name in [
    "baseline.json", "runtime-observation.json", "starting-source-sha256.json",
    "final-freeze.json", "independent-models.json", "run_group.py",
    "run_final_sequence.py", "build_evidence.py", "verify_retained.py",
    "inspect_live_preview.py", "review_artifacts.py", "system_browser_check.py",
    "test_preference_snapshot_probe.py", "native_json_independent_test.go",
    "native-json-independent-overlay.json", "doctor_independent_probe.py",
]:
    retain(r / name, "review/root/" + name)
for path in sorted((r / "model-replays").iterdir()):
    if path.is_file() and path.suffix in {".py", ".go", ".json", ".jsonl"}:
        retain(path, "review/model-replays/" + path.name, compress=path.suffix == ".jsonl")

for name in groups:
    retain(r / (name + ".status.json"), "checks/status/" + name + ".json")
    retain(r / (name + ".log"), "checks/" + name + ".log", compress=True)
retain(r / "final-sequence.status.json", "checks/status/final-sequence.json")
retain(r / "final-sequence.log", "checks/final-sequence.log", compress=True)
for name in [
    "final-tests.xml", "final-tests.xml.orca.xml", "final-new-regressions.xml",
    "final-preference-independent.xml", "system-browser-tests.xml",
]:
    retain(r / name, "checks/" + name, compress=True)
for name in ["actual-preview.json", "actual-preview.log", "artifact-review.json", "system-browser-runtime.json"]:
    retain(r / name, "checks/" + name)

for path in sorted(r.iterdir()):
    if not path.is_file() or "before" not in path.name:
        continue
    if path.suffix not in {".py", ".go", ".json", ".xml", ".log", ".exit"}:
        continue
    retain(path, "proofs/root/" + path.name, compress=path.suffix in {".xml", ".log"})
for owner in ["discovery", "runner", "ui", "recovery", "boot"]:
    for path in sorted((w / owner).iterdir()):
        if not path.is_file() or "checkpoint" in path.name.lower():
            continue
        if path.suffix not in {".py", ".go", ".json", ".xml", ".log", ".txt", ".exit", ".jsonl", ".md", ".patch", ".diff"}:
            continue
        retain(path, "reviewers/" + owner + "/" + path.name, compress=path.suffix in {".xml", ".log", ".jsonl"})

execution = {
    "recorded_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "client_timezone": "America/Chicago", "container": load(r / "final-sequence.status.json"),
    "groups": statuses, "source_frozen": True, "child_umask": "022",
    "private_display_dpi": 72, "actual_device_or_power_actions": False,
    "remote_write_or_release": False,
}
(out / "checks/execution.json").write_text(json.dumps(execution, indent=2) + "\n")

readme = f'''# Beamo Wipe: twelfth comprehensive local audit

Three independently reproduced defects are repaired on baseline
`{freeze["baseline_commit"]}`, branch `fix/safety-audit-20261019`. Audit date:
2026-10-21, America/Chicago. The complete local gate records **11,798 unique
Python passes** (11,797 main plus one separate Orca case), **28 unchanged
unverified skips**, zero failures/errors and zero Python warnings. Every prior
main test ID remains and exactly 28 cases were added. Go and model results are
reported separately.

## Verified defects and repairs

| Baseline trigger | Repair | Exact final regression on baseline |
| --- | --- | --- |
| The report-intent reader compared only device/inode at its final pathname check. A mode, link-count, or same-size content change between final descriptor and pathname snapshots was accepted. | The final named snapshot now matches device, inode, size, mode, owner, link count, modification time and change time before the saved preference is trusted. | 6 failures / 2 normal controls; all 8 pass after repair. |
| Linux launcher inventory used permissive `encoding/json`. Duplicate semantic keys could turn contradictory SATA/path evidence into a direct USB restart plan, while invalid UTF-8 and unpaired surrogates became replacement characters in media identity. | A bounded preflight rejects malformed UTF-8, replacement-decoded strings, trailing values and duplicate exact/case/escaped Unicode-fold keys at every object depth before typed decoding. Normal Unicode, paired surrogates, numeric strings and unknown unique fields remain accepted. | 24 failing leaves / 16 controls; all 40 leaves plus their parent pass after repair. |
| Deeply nested output from the selected local Python made `dev.py doctor` raise `RecursionError` without its promised structured report. | The existing malformed-probe boundary now treats decoder recursion as invalid local probe output and returns the usual structured blocked report. | 8 failures / 12 controls; all 20 pass after repair. |

Root reproduced every issue before the edit, reviewed the complete diffs and
ran distinct probes: preference 6 failures/2 controls, native JSON 5
failures/2 controls, and doctor 2 failures/2 controls. Every probe passes on
the final freeze. Every existing test file is byte-identical, preserving all
old assertions. Only three product files and three new regression modules
change. All **825 frozen source/test/build inputs** match their manifest.

## Completed local checks

The configured syntax, shell, Ruff/security/format and mypy checks pass, as do
preview, private negative mutation, test/desktop doctors, the exact new tests
and independent probes. The uncached Go race run has **459 named passes** and
two unchanged native inventory/platform skips, retaining all 418 prior named
passes and adding exactly 41. Vet, 350,000 fuzz executions, Windows test
cross-compilation and Windows/Linux launcher cross-builds pass.

Checks ran serially in one unprivileged container with child umask 022 and
private 72-DPI display/session contexts. Independent artifact inspection checks
PE32+/ELF64 x86_64 headers, current source/build identity, hashes and executable
modes without executing native launchers. The actual fake-disk Tk welcome was
visually inspected after paint and closed through its registered normal-close
callback with exit 0. Nine supplemental browser assertions pass under system
Chromium; this does not qualify the missing pinned Playwright runtime.

## Five bounded reviews and independent replays

Root independently replayed each final model on frozen source. Discovery covers
720 two-snapshot/precedence states (68 positives, 652 refusals); runner covers
120 states and 360 accepted generations; terminal handoff covers 9,636
scenarios/29,304 events including 64 thread races; recovery covers 288 journal,
lock and fake-engine states; launcher request epochs cover 16 delayed-worker
states and 64 closed-session refusals. Every model has zero mismatches and zero
native callbacks. Reviewer-focused counts overlap the canonical gate and are
not added to unique coverage.

## Remaining qualification

All 28 prior Python skips remain unverified: generated image/artifact cases,
pinned-browser cases, Microsoft-document reachability checks and the legacy
gcloud check. Go's two native platform/inventory skips remain open. ISO/KVM,
actual device/nwipe behavior, native Windows execution, firmware, physical USB
and reconnect qualification also remain unverified. Local development evidence
does not establish complete release qualification.

Blacksmith remains the current hosted provider. No GCP/hosted gate, remote
write, PR, merge, release, real engine/device/mount/firmware/power or guest
action occurred. Publication remains pending the earlier automatic approval
review that rejected operational-backlog metadata export as internal data; no
retry or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass12/verify_retained.py` to
verify every retained hash, the frozen source, prior/current Python IDs and skip
reasons, and prior/current Go named outcomes. Clean post-commit launcher
identity is retained outside Git to avoid a self-reference.
'''
(out / "README.md").write_text(readme)
shutil.copyfile(r / "verify_retained.py", out / "verify_retained.py")

# Count every artifact that the manifest will bind, including final-summary.
retained_count = sum(path.is_file() for path in out.rglob("*")) + 1
summary = {
    "base_commit": freeze["baseline_commit"], "branch": "fix/safety-audit-20261019",
    "audit_date": "2026-10-21", "client_timezone": "America/Chicago",
    "verified_root_causes": 3, "canonical_reports": reports,
    "canonical_unique_passed": 11798, "canonical_main_passed": 11797,
    "canonical_orca_passed": 1, "unchanged_skips_unverified": 28,
    "canonical_python_warning_count": 0, "new_python_regression_cases": 28,
    "baseline_main_test_ids_retained": 11797,
    "baseline_skip_ids_and_reasons_unchanged": True,
    "verified_source_files": 825, "source_manifest_sha256": freeze["source_manifest_sha256"],
    "all_existing_test_files_byte_identical": True, "old_assertions_preserved": True,
    "go_full_race_named_pass_events": len(go_pass),
    "go_full_race_native_skips": sorted(test for _, test in go_skip),
    "new_go_leaf_cases": 40, "new_go_named_pass_events": 41,
    "baseline_go_named_results_retained": 420, "system_browser_supplement_passed": 9,
    "system_browser_is_pinned": False, "go_fuzz_executions": 350000,
    "retained_artifacts": retained_count, "native_or_physical_qualification": False,
    "remote_write_or_release_performed": False,
}
(out / "final-summary.json").write_text(json.dumps(summary, indent=2) + "\n")
manifest = {
    str(path.relative_to(out)): {"bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    for path in sorted(out.rglob("*")) if path.is_file()
}
assert len(manifest) == retained_count
(out / "artifacts-sha256.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
subprocess.run(["python3", str(out / "verify_retained.py")], cwd=repo, check=True)
print(json.dumps({"sources": 825, "retained_artifacts": len(manifest),
                  "unique_python_passes": 11798, "unchanged_skips": 28,
                  "go_named_passes": len(go_pass), "verified_roots": 3}))
