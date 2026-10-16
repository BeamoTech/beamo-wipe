# SPDX-License-Identifier: GPL-3.0-or-later
"""Versioned allowlist for a privacy-reduced sharing copy.

The owner's original evidence bytes are never mutated. A sharing copy is a
new document that keeps outcome, method, duration, verification, warnings,
safe build identity, and support codes, and drops disk identifiers, paths,
host details, and engine logs.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Mapping, cast

POLICY_VERSION = 1
POLICY_ID = "beamo-wipe-sharing-v1"
SHARE_JSON = "SHARE.json"
SHARE_SUMMARY = "SHARE.txt"
WITHHELD = "withheld"
NOTICE = (
    "Privacy-reduced sharing copy. Not identity evidence. "
    "Do not use this copy where a serial, hardware ID, or device path is required."
)
UNSUITABLE = (
    "Unsuitable where full identity evidence is required. "
    "Use the original report for serials, hardware IDs, or device paths."
)

_IDENTIFIER_DEVICE_KEYS = ("serial", "wwn", "path", "realpath", "name", "label")
_KEEP_ROOT = frozenset(
    {
        "schema_version",
        "beamo_wipe_version",
        "source_commit",
        "build_id",
        "build_status",
        "source_dirty",
        "nwipe_version",
        "nwipe_commit",
        "outcome",
        "completion",
        "failure_reason",
        "device",
        "device_presentation",
        "method",
        "timestamps",
        "nwipe",
        "exit_evidence",
        "verification",
        "warnings",
        "interruption",
        "presentation",
        "result_description",
        "locale",
    }
)
_KEEP_DEVICE = frozenset({"model", "size_bytes", "size_gb_label", "kind", "bus"})
_KEEP_DEVICE_PRESENTATION = frozenset({"title", "capacity", "connection", "kind"})
_KEEP_METHOD = frozenset(
    {
        "id",
        "nwipe_method",
        "rounds",
        "verify",
        "noblank",
        "docs_name",
        "title",
        "overwrite_passes",
        "verification_passes",
        "description",
        "operation_summary",
    }
)
_KEEP_TIMESTAMPS = frozenset(
    {
        "started_at_wall",
        "ended_at_wall",
        "started_monotonic",
        "ended_monotonic",
        "duration_s",
        "duration_source",
        "wall_confidence",
        "wall_provenance",
    }
)
_KEEP_NWIPE = frozenset({"version"})
_KEEP_EXIT = frozenset({"exit_code", "signal"})
_KEEP_VERIFICATION = frozenset({"requested", "verified", "scope"})
_KEEP_COMPLETION = frozenset({"validated", "reason"})
_KEEP_INTERRUPTION = frozenset({"interrupted", "cancelled", "origin"})
_KEEP_LOCALE = frozenset({"language", "keyboard_layout"})
_KEEP_PRESENTATION = frozenset(
    {"code", "message", "next_step", "tone", "icon", "success"}
)


def _object_mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, dict) else {}


def is_sharing_copy(evidence: object) -> bool:
    if not isinstance(evidence, dict):
        return False
    privacy = evidence.get("privacy")
    return (
        isinstance(privacy, dict)
        and privacy.get("copy") == "sharing"
        and privacy.get("unsuitable_for_identity_evidence") is True
        and privacy.get("policy_version") == POLICY_VERSION
        and privacy.get("policy") == POLICY_ID
    )


def collect_secrets(evidence: Mapping[str, Any]) -> tuple[str, ...]:
    found: list[str] = []

    def add(value: object) -> None:
        if isinstance(value, str):
            text = value.strip()
            if text:
                found.append(text)
                base = os.path.basename(text.replace("\\", "/")).strip()
                if base and base != text:
                    found.append(base)

    device = _object_mapping(evidence.get("device"))
    for key in _IDENTIFIER_DEVICE_KEYS:
        add(device.get(key))
    add(evidence.get("boot_device"))
    add(evidence.get("logfile"))
    provenance = (
        _object_mapping(evidence.get("provenance"))
    )
    add(provenance.get("evidence_file"))
    presentation = (
        _object_mapping(evidence.get("device_presentation"))
    )
    add(presentation.get("id_value"))
    add(presentation.get("system_path"))
    nwipe = _object_mapping(evidence.get("nwipe"))
    argv = nwipe.get("argv_redacted")
    if isinstance(argv, list):
        for item in argv:
            if isinstance(item, str) and item.startswith("/dev/"):
                add(item)
    unique = sorted(set(found), key=len, reverse=True)
    return tuple(unique)


def _scrub(value: object, secrets: tuple[str, ...]) -> object:
    if isinstance(value, str):
        if not secrets:
            return value
        pattern = "|".join(re.escape(secret) for secret in secrets)
        return re.sub(pattern, lambda _match: WITHHELD, value, flags=re.IGNORECASE)
    if isinstance(value, list):
        return [_scrub(item, secrets) for item in value]
    if isinstance(value, dict):
        return {key: _scrub(item, secrets) for key, item in value.items()}
    return value


def _pick(mapping: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    return {key: mapping[key] for key in allowed if key in mapping}


def _scalar_fields(mapping: Mapping[str, Any]) -> dict[str, Any]:
    """Allowed leaves cannot carry arbitrary nested keys into a sharing copy."""
    return {
        key: value for key, value in mapping.items()
        if value is None or isinstance(value, (str, int, float, bool))
    }


def _restore_safe_strings(shared: dict[str, Any], evidence: Mapping[str, Any]) -> None:
    """Identifiers cannot redact validated codes or canonical application copy."""
    from beamo_wipe import NWIPE_PINNED_COMMIT, NWIPE_PINNED_VERSION, __version__, lang
    from beamo_wipe.build_identity import BUILD_ID_RE, COMMIT_RE, STATUSES
    from beamo_wipe.evidence import ALLOWED_OUTCOMES, WALL_PROVENANCE, valid_wall
    from beamo_wipe.keyboard import LAYOUTS
    from beamo_wipe.methods import METHODS
    from beamo_wipe.models import MethodId
    from beamo_wipe.outcomes import VIEWS, present_evidence

    def keep(section: str | None, key: str, allowed) -> None:
        source = evidence if section is None else _object_mapping(evidence.get(section))
        target = shared if section is None else shared.get(section)
        value = source.get(key)
        if isinstance(target, dict) and isinstance(value, str) and value in allowed:
            target[key] = value

    reasons = {*VIEWS, "completed"}
    keep(None, "outcome", ALLOWED_OUTCOMES)
    keep(None, "failure_reason", reasons)
    keep("completion", "reason", reasons)
    keep(None, "build_status", STATUSES)
    for key, expected in (
        ("beamo_wipe_version", __version__),
        ("nwipe_version", NWIPE_PINNED_VERSION),
        ("nwipe_commit", NWIPE_PINNED_COMMIT),
    ):
        keep(None, key, {expected})
    for key, pattern in (("source_commit", COMMIT_RE), ("build_id", BUILD_ID_RE)):
        value = evidence.get(key)
        if isinstance(value, str) and pattern.fullmatch(value):
            keep(None, key, {value})
    keep("nwipe", "version", {NWIPE_PINNED_VERSION})
    keep("locale", "language", lang.LANGUAGE_ORDER)
    keep("locale", "keyboard_layout", LAYOUTS)
    keep("interruption", "origin", {"user", "system", "none"})
    keep("timestamps", "duration_source", {"monotonic"})
    keep("timestamps", "wall_confidence", {"unverified", "unavailable"})
    keep("timestamps", "wall_provenance", WALL_PROVENANCE)
    for key in ("started_at_wall", "ended_at_wall"):
        value = _object_mapping(evidence.get("timestamps")).get(key)
        if isinstance(value, str) and valid_wall(value):
            keep("timestamps", key, {value})

    method = _object_mapping(evidence.get("method"))
    method_id = method.get("id")
    if isinstance(method_id, str) and method_id in {item.value for item in MethodId}:
        spec = METHODS[MethodId(method_id)]
        keep("method", "id", {spec.method_id.value})
        keep("method", "nwipe_method", {spec.nwipe_method})
        keep("method", "verify", {spec.verify})
        keep("verification", "requested", {spec.verify})

    # Rebuild fixed result prose from the original validated core, rather than
    # trusting arbitrary copied prose or weakening sharing-result validation.
    # The current report language may differ from the original session's.
    view = present_evidence(evidence)
    shared["presentation"] = _pick(view.payload(), _KEEP_PRESENTATION)
    shared["result_description"] = view.message


def make_sharing_copy(evidence: Mapping[str, Any]) -> dict[str, Any]:
    """Build a new sharing document. Does not mutate ``evidence``."""
    secrets = collect_secrets(evidence)
    root = _scalar_fields(_pick(evidence, _KEEP_ROOT))
    for key, allowed in (
        ("device", _KEEP_DEVICE),
        ("device_presentation", _KEEP_DEVICE_PRESENTATION),
        ("method", _KEEP_METHOD),
        ("timestamps", _KEEP_TIMESTAMPS),
        ("nwipe", _KEEP_NWIPE),
        ("exit_evidence", _KEEP_EXIT),
        ("verification", _KEEP_VERIFICATION),
        ("completion", _KEEP_COMPLETION),
        ("interruption", _KEEP_INTERRUPTION),
        ("presentation", _KEEP_PRESENTATION),
        ("locale", _KEEP_LOCALE),
    ):
        root.pop(key, None)
        section = evidence.get(key)
        if isinstance(section, dict):
            root[key] = _scalar_fields(_pick(section, allowed))
    root.pop("warnings", None)
    warnings = evidence.get("warnings")
    if isinstance(warnings, list):
        root["warnings"] = [item for item in warnings if isinstance(item, str)]
    shared = cast(dict[str, Any], _scrub(root, secrets))
    _restore_safe_strings(shared, evidence)
    shared["privacy"] = {
        "policy_version": POLICY_VERSION,
        "policy": POLICY_ID,
        "copy": "sharing",
        "unsuitable_for_identity_evidence": True,
        "notice": NOTICE,
    }
    return shared


def encode_sharing_copy(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
