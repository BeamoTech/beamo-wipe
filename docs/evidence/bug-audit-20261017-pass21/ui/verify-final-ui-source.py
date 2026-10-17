"""Source/AST/archive/XML parsing only; never imports product or executes tests."""

import ast
import hashlib
import json
from pathlib import Path
import tarfile
import xml.etree.ElementTree as ET


root = Path("/root/dev/Beamo Wipe")
stage = Path("/tmp/pass21-primary")
out = root / "docs/evidence/bug-audit-20261017-pass21/ui"
digest = lambda data: hashlib.sha256(data).hexdigest()
freeze_bytes = (stage / "source-freeze.json").read_bytes()
freeze = json.loads(freeze_bytes)
start = json.loads((stage / "starting-freeze.json").read_bytes())
assert len(freeze) == 788 and len(start) == 779
current_bad = [name for name, sha in freeze.items() if digest((root / name).read_bytes()) != sha]
assert not current_bad, current_bad
archive_path = stage / "final-source-inputs.tar.gz"
with tarfile.open(archive_path, "r:gz") as archive:
    members = archive.getmembers()
    assert len(members) == len({member.name for member in members}) == len(freeze)
    assert {member.name for member in members} == set(freeze)
    assert all(member.isfile() for member in members)
    archive_bad = [member.name for member in members
                   if digest(archive.extractfile(member).read()) != freeze[member.name]]
assert not archive_bad, archive_bad
with tarfile.open(stage / "starting-inputs.tar.gz", "r:gz") as archive:
    members = archive.getmembers()
    assert len(members) == len({member.name for member in members}) == len(start)
    assert {member.name for member in members} == set(start)
    assert all(member.isfile() for member in members)
    assert all(digest(archive.extractfile(member).read()) == start[member.name] for member in members)
changed = sorted(name for name, sha in start.items() if freeze.get(name) != sha)
added = sorted(set(freeze) - set(start))
assert changed == ["src/beamo_wipe/diagnostics.py", "src/beamo_wipe/discover.py",
                   "src/beamo_wipe/ui/accessible_wizard.py", "src/beamo_wipe/ui/tk_wizard.py"]
assert len(added) == 9

runtime = hashlib.sha256()
runtime_names = sorted(name for name in freeze if name.startswith("src/beamo_wipe/"))
assert all(digest((stage / "original-replay" / name).read_bytes()) == start[name] for name in runtime_names)
for name in runtime_names:
    encoded_name, sha = name.encode(), freeze[name].encode()
    runtime.update(f"{len(encoded_name)}:".encode() + encoded_name)
    runtime.update(f"{len(sha)}:".encode() + sha)
runtime_sha = runtime.hexdigest()
assert runtime_sha == json.loads((stage / "source-review.json").read_bytes())["runtime_source_sha256"]

ui_inputs = ["src/beamo_wipe/ui/tk_wizard.py", "src/beamo_wipe/ui/accessible_wizard.py"]
pairs = [
    ("tk-variable-root-proof-v3.py", "test_tk_variable_interpreter_pass21.py", {"_admit", "test_native_variables_use_the_owned_root"}, 7),
    ("refresh-acceptance-proof.py", "test_refresh_acceptance_interruptions_pass21.py", {"_admit", "_accessible"}, 8),
    ("gtk-close-cleanup-proof.py", "test_accessible_close_cleanup_pass21.py", {"_module"}, 3),
    ("tk-trace-adoption-proof-v2.py", "test_tk_trace_adoption_pass21.py", {"_admit", "test_interrupted_owned_trace_is_retired"}, 4),
    ("realthread-refresh-proof.py", "test_refresh_commit_concurrency_pass21.py", {"_admit", "_accessible"}, 6),
]
ast_rows = []
for proof_name, test_name, allowed_changes, cases in pairs:
    proof_path, canonical_path = out / proof_name, root / "tests" / test_name
    proof_bytes, canonical_bytes = proof_path.read_bytes(), canonical_path.read_bytes()
    proof_ast, canonical_ast = ast.parse(proof_bytes), ast.parse(canonical_bytes)
    def functions(tree):
        return {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    proof_functions, canonical_functions = functions(proof_ast), functions(canonical_ast)
    assert proof_functions.keys() == canonical_functions.keys()
    different = sorted(name for name in proof_functions
                       if ast.dump(proof_functions[name]) != ast.dump(canonical_functions[name]))
    assert set(different) == allowed_changes, (test_name, different)
    assertion_count = 0
    assertion_map = {}
    for name in proof_functions:
        if name in {"_admit", "_accessible", "_module"}:
            continue
        before = [ast.dump(node) for node in ast.walk(proof_functions[name]) if isinstance(node, ast.Assert)]
        after = [ast.dump(node) for node in ast.walk(canonical_functions[name]) if isinstance(node, ast.Assert)]
        assert before == after, (test_name, name)
        assertion_map[name] = len(before)
        assertion_count += len(before)
    def static_nodes(tree):
        return [ast.dump(node) for node in tree.body
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                         and isinstance(node.value.value, str))]
    assert static_nodes(proof_ast) == static_nodes(canonical_ast), test_name
    ui_inputs.append(str(canonical_path.relative_to(root)))
    ast_rows.append(dict(proof=proof_name, proof_sha256=digest(proof_bytes),
                         canonical="tests/" + test_name, canonical_sha256=digest(canonical_bytes),
                         cases=cases, changed_functions=different,
                         unchanged_functions=sorted(set(proof_functions) - set(different)),
                         non_admission_assertions=assertion_count,
                         assertion_map=assertion_map, all_non_admission_assertions_identical=True,
                         static_import_class_constant_main_ast_identical=True))

reports = {}
for label in ("final-canonical-original", "canonical-fixed", "final-focused-corrected"):
    path = stage / (label + ".xml")
    tree = ET.fromstring(path.read_bytes())
    cases = tree.findall(".//testcase")
    counts = dict(tests=len(cases), failures=sum(node.find("failure") is not None for node in cases),
                  errors=sum(node.find("error") is not None for node in cases),
                  skips=sum(node.find("skipped") is not None for node in cases))
    counts["passing"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skips"]
    status = json.loads((stage / (label + "-status.json")).read_bytes())
    properties = []
    retry_properties = []
    if label in {"final-canonical-original", "final-focused-corrected"}:
        for case in cases:
            for prop in case.findall("properties/property"):
                if prop.attrib.get("name") == "actual_refresh_retry_trace":
                    retry = json.loads(prop.attrib["value"])
                    retry_properties.append(retry)
                    assert retry["state"] == "OWNER" and not retry["alive"] and retry["threads"] == 1
                    assert [scan["phase"] for scan in retry["scans"]] == ["retry"]
                    continue
                if prop.attrib.get("name") != "actual_refresh_acceptance_trace":
                    continue
                trace = json.loads(prop.attrib["value"])
                source_key = "src/beamo_wipe/ui/" + ("tk_wizard.py" if trace["surface"] == "tk" else "accessible_wizard.py")
                if label == "final-canonical-original":
                    assert trace["provenance"]["sha256"] == start[source_key]
                if label == "final-focused-corrected":
                    expected = freeze[source_key]
                    assert trace["provenance"]["sha256"] == expected
                    first = trace["first"]
                    assert first["alive"] == [False] and not first["errors"]
                    if trace["fault"] == "normal-control":
                        assert first["state_at_return"] == "REFRESHING" and len(first["scans"]) == 1
                    else:
                        assert first["state_at_return"] == first["state_after_join"] == "PICK_BLOCKED"
                        assert not first["scans"] and not first["registered"]
                        assert first["completions"][0]["error_id"] == trace["original_error_id"]
                properties.append(dict(surface=trace["surface"], fault=trace["fault"],
                                       source=trace["provenance"], first=trace["first"],
                                       cleanup_alive=trace["cleanup_alive"]))
        assert len(properties) == 6
        assert all(not any(prop["cleanup_alive"]) for prop in properties)
    if label == "final-canonical-original":
        assert counts == dict(tests=219, failures=89, errors=0, skips=0, passing=130)
        assert not retry_properties
    if label == "final-focused-corrected":
        assert len(retry_properties) == 4
    reports[label] = dict(sha256=digest(path.read_bytes()), counts=counts,
                          exit_code=status["exit_code"], selected_actual_thread_traces=properties,
                          actual_thread_retry_traces=retry_properties)
assert reports["canonical-fixed"]["counts"] == dict(tests=213, failures=0, errors=0, skips=0, passing=213)
assert reports["final-focused-corrected"]["counts"] == dict(tests=290, failures=0, errors=0, skips=0, passing=290)
row = dict(review="source/AST/archive/XML parsing only; no product imports or test execution",
           frozen_inputs=len(freeze), starting_inputs=len(start), unchanged_start_inputs=len(start)-len(changed),
           source_freeze_sha256=digest(freeze_bytes), archive_sha256=digest(archive_path.read_bytes()),
           all_current_and_archived_frozen_inputs_match=True, changed=changed, added=added,
           starting_archive_inputs_authenticated=len(start), original_replay_runtime_inputs_authenticated=len(runtime_names),
           runtime_inputs=len(runtime_names), runtime_source_sha256=runtime_sha,
           selected_ui_inputs={name: freeze[name] for name in ui_inputs},
           ui_cases=sum(row["cases"] for row in ast_rows), ast=ast_rows, reports=reports,
           pending="Root final full gates, campaign/artifact retention, broader qualification")
target = out / "FINAL-UI-SOURCE-REVIEW.json"
target.write_text(json.dumps(row, indent=2) + "\n")
print(json.dumps(dict(result="PASS", receipt=str(target), sha256=digest(target.read_bytes()),
                      frozen_inputs=len(freeze), runtime_source_sha256=runtime_sha,
                      ui_cases=row["ui_cases"], non_admission_assertions=sum(item["non_admission_assertions"] for item in ast_rows))))
