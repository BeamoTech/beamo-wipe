"""Private identifiers cannot corrupt fixed report semantics or policy labels."""

import copy
import json

import pytest

from beamo_wipe import lang, outcomes, privacy
from beamo_wipe.models import MethodId
from beamo_wipe.support_export import _bundle_files
from test_result_presentations import CASES, case_evidence

EXTRA = (CASES[0][0], MethodId.EXTRA, *CASES[0][2:])
COLLISIONS = ["sharing", "verified", "a", "everyday", "prng", "last", "completed", "cancelled", "en"]


def _collision(case, secret):
    _, evidence, log = case_evidence(case)
    evidence["device"]["serial"] = secret
    evidence["device_presentation"]["id_value"] = secret
    evidence["device"]["model"] = "private-model-" + secret
    evidence["warnings"].append("private-warning-" + secret)
    return evidence, log


@pytest.mark.parametrize("case", [*CASES, EXTRA], ids=lambda case: case[0] + "-" + case[1].value)
@pytest.mark.parametrize("secret", COLLISIONS)
def test_structural_collisions_preserve_original_result_and_policy(case, secret):
    evidence, _ = _collision(case, secret)
    before = copy.deepcopy(evidence)
    assert outcomes.present_evidence(evidence).code == case[0]
    shared = privacy.make_sharing_copy(evidence)
    assert evidence == before
    assert privacy.is_sharing_copy(shared)
    assert shared["privacy"]["policy"] == privacy.POLICY_ID
    assert shared["privacy"]["notice"] == privacy.NOTICE
    assert shared["outcome"] == evidence["outcome"]
    prose_fields = {"title", "description", "docs_name", "operation_summary"}
    for key, value in evidence["method"].items():
        if key in prose_fields:
            assert outcomes._method_copy_field_matches(
                shared["method"][key], value, sharing=True
            )
        else:
            assert shared["method"][key] == value
    assert shared["locale"] == evidence["locale"]
    assert outcomes.present_evidence(shared).code == case[0]
    assert "serial" not in shared["device"]
    assert secret.casefold() not in shared["device"]["model"].casefold()
    assert secret.casefold() not in shared["warnings"][-1].casefold()


@pytest.mark.parametrize("source_language", lang.LANGUAGE_ORDER)
@pytest.mark.parametrize("display_language", lang.LANGUAGE_ORDER)
def test_sharing_after_language_restart_preserves_validated_result(source_language, display_language):
    lang.set_language(source_language)
    _, evidence, _ = case_evidence(CASES[0])
    before = copy.deepcopy(evidence)
    lang.set_language(display_language)
    assert outcomes.present_evidence(evidence).code == "verified"
    shared = privacy.make_sharing_copy(evidence)
    assert outcomes.present_evidence(shared).code == "verified"
    assert shared["method"] == evidence["method"]
    assert evidence == before


@pytest.mark.parametrize("case", [CASES[0], CASES[1], CASES[6]])
def test_exported_sharing_summary_keeps_success_quickzero_and_cancel_outcomes(case):
    evidence, log = _collision(case, "sharing")
    raw = json.dumps(evidence).encode()
    bundle = _bundle_files(raw, log.encode(), "complete", privacy_reduced=True)
    shared = json.loads(bundle[privacy.SHARE_JSON])
    assert outcomes.present_evidence(shared).code == case[0]
    assert privacy.NOTICE in bundle[privacy.SHARE_SUMMARY].decode()
    assert outcomes.VIEWS[case[0]].message in bundle[privacy.SHARE_SUMMARY].decode()
    assert bundle["result.json"] == raw


@pytest.mark.parametrize("section,key", [
    (None, "outcome"), ("method", "id"), ("completion", "reason"),
    ("locale", "language"), (None, "build_id"), (None, "source_commit"),
])
def test_unknown_control_values_are_still_scrubbed_and_never_upgraded(section, key):
    secret = "PRIVATE-MARKER"
    evidence, _ = _collision(CASES[0], secret)
    target = evidence if section is None else evidence[section]
    target[key] = secret
    shared = privacy.make_sharing_copy(evidence)
    assert secret not in privacy.encode_sharing_copy(shared).decode()
    if key in {"outcome", "id", "reason", "language"}:
        assert outcomes.present_evidence(shared).code == "indeterminate"


def test_validated_build_and_clock_values_survive_short_identifier_collision():
    evidence, _ = _collision(CASES[0], "1")
    evidence["source_commit"] = "1" * 40
    evidence["build_id"] = "12345678-1234-1234-1234-123456789abc"
    evidence["build_status"] = "production"
    evidence["timestamps"]["started_at_wall"] = "2026-10-16T10:00:00Z"
    evidence["timestamps"]["ended_at_wall"] = "2026-10-16T10:00:01Z"
    evidence["timestamps"]["wall_confidence"] = "unverified"
    evidence["timestamps"]["wall_provenance"] = "os_utc"
    shared = privacy.make_sharing_copy(evidence)
    for key in ("source_commit", "build_id", "build_status", "beamo_wipe_version", "nwipe_version", "nwipe_commit"):
        assert shared[key] == evidence[key]
    assert shared["timestamps"] == evidence["timestamps"]


def test_verification_scope_keeps_identifier_redaction():
    evidence, _ = _collision(CASES[0], "overwrite")
    before = copy.deepcopy(evidence)
    shared = privacy.make_sharing_copy(evidence)
    assert shared["verification"]["scope"] == privacy._scrub(
        evidence["verification"]["scope"], privacy.collect_secrets(evidence)
    )
    assert "overwrite" not in shared["verification"]["scope"]
    assert outcomes.present_evidence(shared).code == "verified"
    assert evidence == before


@pytest.mark.parametrize("case", [*CASES, EXTRA], ids=lambda case: case[0] + "-" + case[1].value)
@pytest.mark.parametrize("short_identifier", ["d", "h", "withheld"])
def test_multiple_identifiers_cannot_scrub_inserted_placeholders(case, short_identifier):
    evidence, _ = _collision(case, "overwrite")
    evidence["device"]["wwn"] = short_identifier
    evidence["device"]["label"] = "private-label"
    before = copy.deepcopy(evidence)
    shared = privacy.make_sharing_copy(evidence)
    assert outcomes.present_evidence(shared).code == case[0]
    assert outcomes._method_copy_field_matches(
        shared["method"]["operation_summary"],
        evidence["method"]["operation_summary"],
        sharing=True,
    )
    assert "overwrite" not in shared["method"]["operation_summary"]
    assert shared["warnings"][-1] == "private-warning-withheld"
    assert evidence == before


@pytest.mark.parametrize("placement", ["warnings_dict", "warnings_list", "root_scalar", "section_scalar"])
def test_malformed_container_keys_never_export_private_identifiers(placement):
    secret = "PRIVATE-CUSTOMER-SERIAL"
    evidence, _ = _collision(CASES[0], secret)
    if placement == "warnings_dict":
        evidence["warnings"] = {secret: "malformed warning"}
    elif placement == "warnings_list":
        evidence["warnings"] = ["ordinary warning", {secret: "malformed warning"}]
    elif placement == "root_scalar":
        evidence["beamo_wipe_version"] = {secret: "malformed version"}
    else:
        evidence["method"]["id"] = {secret: "malformed method"}
    before = copy.deepcopy(evidence)
    shared = privacy.make_sharing_copy(evidence)
    assert secret not in privacy.encode_sharing_copy(shared).decode()
    assert evidence == before
    assert all(isinstance(item, str) for item in shared.get("warnings", []))
    if placement == "warnings_list":
        assert shared["warnings"] == ["ordinary warning"]
    elif placement == "section_scalar":
        assert outcomes.present_evidence(shared).code == "indeterminate"
