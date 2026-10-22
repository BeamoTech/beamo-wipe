"""Verify the retained PASS12 report, source freeze, and canonical deltas."""
from pathlib import Path
import gzip
import hashlib
import json
import xml.etree.ElementTree as E

out = Path(__file__).resolve().parent
repo = out.parents[2]
load = lambda path: json.loads(path.read_text())
manifest = load(out / "artifacts-sha256.json")
for name, record in manifest.items():
    path = out / name
    assert path.is_file(), name
    assert path.stat().st_size == record["bytes"], name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"], name

summary = load(out / "final-summary.json")
source = load(out / "source-sha256.json")
assert len(source) == summary["verified_source_files"] == 825
assert all(hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest for name, digest in source.items())
assert hashlib.sha256((out / "source-sha256.json").read_bytes()).hexdigest() == summary["source_manifest_sha256"]


def junit(path):
    with gzip.open(path, "rb") as stream:
        root = E.fromstring(stream.read())
    cases = list(root.iter("testcase"))
    ids = {(case.get("classname"), case.get("name")) for case in cases}
    assert len(cases) == len(ids)
    assert all(case.find(kind) is None for case in cases for kind in ("failure", "error"))
    skips = {
        (case.get("classname"), case.get("name")): case.find("skipped").get("message")
        for case in cases if case.find("skipped") is not None
    }
    return cases, ids, skips


main, main_ids, skips = junit(out / "checks/final-tests.xml.gz")
orca, orca_ids, orca_skips = junit(out / "checks/final-tests.xml.orca.xml.gz")
new_cases, new_ids, new_skips = junit(out / "checks/final-new-regressions.xml.gz")
prior, prior_ids, prior_skips = junit(repo / "docs/evidence/bug-audit-20261021-pass11/checks/final-tests.xml.gz")
assert len(main) == 11825 and len(skips) == 28
assert len(orca) == 1 and not orca_skips and not (main_ids & orca_ids)
assert len(new_cases) == len(new_ids) == 28 and not new_skips
assert prior_ids < main_ids and main_ids - prior_ids == new_ids
assert skips == prior_skips
assert summary["canonical_unique_passed"] == (len(main) - len(skips)) + len(orca) == 11798


def go_events(path):
    with gzip.open(path, "rt") as stream:
        rows = [json.loads(line) for line in stream if line.startswith("{")]
    passed = {(row.get("Package"), row["Test"]) for row in rows if row.get("Action") == "pass" and row.get("Test")}
    skipped = {(row.get("Package"), row["Test"]) for row in rows if row.get("Action") == "skip" and row.get("Test")}
    return passed, skipped


go_pass, go_skip = go_events(out / "checks/final-go-race.log.gz")
old_pass, old_skip = go_events(repo / "docs/evidence/bug-audit-20261021-pass11/checks/final-go-race.log.gz")
new_go_pass, new_go_skip = go_events(out / "checks/final-go-new.log.gz")
assert len(go_pass) == 459 and len(go_skip) == 2
assert old_pass < go_pass and go_pass - old_pass == new_go_pass and len(new_go_pass) == 41
assert old_skip == go_skip and not new_go_skip

assert summary["new_python_regression_cases"] == 28
assert summary["new_go_leaf_cases"] == 40
assert summary["verified_root_causes"] == 3
assert summary["unchanged_skips_unverified"] == 28
assert summary["all_existing_test_files_byte_identical"] is True
assert summary["old_assertions_preserved"] is True
assert summary["remote_write_or_release_performed"] is False
print(json.dumps({
    "retained_artifacts": len(manifest), "source_files": len(source),
    "canonical_unique_passed": 11798, "unchanged_skips": 28,
    "go_named_passes": 459, "go_native_skips": 2,
}))
