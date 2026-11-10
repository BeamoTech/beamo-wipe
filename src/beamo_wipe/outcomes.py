# SPDX-License-Identifier: GPL-3.0-or-later
"""One conservative result vocabulary for UI, reports, and recovered evidence."""

from dataclasses import asdict, dataclass
import re
from typing import Any


@dataclass(frozen=True)
class ResultView:
    code: str
    message: str
    next_step: str
    tone: str
    icon: str
    success: bool = False

    @property
    def announcement(self) -> str:
        return f"{self.message}. {self.next_step}"

    def payload(self) -> dict[str, Any]:
        return {**asdict(self), "announcement": self.announcement}


STOP_WARNING = "Stopping cannot restore files already erased."

# Former shared next step for every failure. No outcome shows it any more;
# it stays as the translated generic baseline each specific step must differ
# from, so the locale tables keep their existing keys.
SUPPORT = (
    "Files may still be on the disk. Save the report if available and contact support. "
    "Shut down before disconnecting."
)
# Every result that does not prove a finished erase leads its next steps with
# this sentence. Each outcome then names its own actions; the report is
# volatile, so saving it comes before any shutdown.
FILES_MAY_REMAIN = "Files may still be on the disk."
NEXT_OPEN_FAILED = (
    "Save the report if available. Shut down, check the disk's connection and "
    "avoid USB hubs, then start again. If this repeats, contact support."
)
NEXT_GEOMETRY = (
    "Save the report if available and contact support before trying this disk "
    "again. Shut down before disconnecting."
)
NEXT_VERIFICATION_FAILED = (
    "The disk may be unreliable; do not treat or sell it as erased. Consider "
    "replacing or physically destroying it. Save the report if available and "
    "contact support. Shut down before disconnecting."
)
NEXT_ENGINE_FAILED = (
    "The disk may be failing; do not treat or sell it as erased. Consider "
    "replacing or physically destroying it. Save the report if available and "
    "contact support. Shut down before disconnecting."
)
NEXT_INTERRUPTED = (
    "Save the report if available. To erase the whole disk, shut down and start "
    "again from the beginning. If this repeats, contact support."
)
NEXT_CANCELLED = (
    "Save the report if available. To erase the whole disk, shut down and start "
    "again from the beginning. For help, contact support."
)
NEXT_COMPLETION_MISSING = (
    "Save the report if available. Shut down, then start again from the "
    "beginning. If the result is the same, contact support."
)
NEXT_PROCESS_FAILED = (
    "Save the report if available. Shut down, then start again from the "
    "beginning. If it fails again, contact support."
)
NEXT_INDETERMINATE = (
    "Save the report if available and contact support. Do not sell or give away "
    "the disk until an erase is confirmed. Shut down before disconnecting."
)
AFTERCARE_SUCCESS = (
    "Only this validated selected disk was processed. Other disks were not. "
    "Putting an operating system back on is a separate task."
)
MSG_START_FAILED = "The erase could not start"
NEXT_START_FAILED = "Keep the disks connected and contact support. Do not bypass protection."
MSG_VERIFIED = "Erase completed; verification passed"
# Trailing space joins the lead to AFTERCARE_SUCCESS in every language.
NEXT_VERIFIED_LEAD = "Read-back checked exposed storage only. Hidden copies may remain. Save the report if needed. "
MSG_UNVERIFIED = "Erase completed; verification was not performed"
NEXT_UNVERIFIED_LEAD = "The erase was not checked by a read-back pass. Save the report if needed. "
MSG_OCCUPIED = "The disk is in use"
NEXT_OCCUPIED = "The erase did not complete. Save the report and ask support what is using the disk. Do not force access."
MSG_OPEN_FAILED = "The disk could not be opened"
MSG_GEOMETRY = "The disk could not be used safely"
MSG_VERIFICATION_FAILED = "Read-back verification failed"
MSG_INTERRUPTED = "The erase was interrupted"
MSG_CANCELLED = "Stopped by you"
MSG_COMPLETION_MISSING = "Erase completion could not be confirmed"
MSG_PROCESS_FAILED = "The erase did not finish"
MSG_ENGINE_FAILED = "The disk reported an erase error"
MSG_INDETERMINATE = "The result could not be confirmed"
MSG_STOP_UNCONFIRMED = "Stop could not be confirmed"
NEXT_STOP_UNCONFIRMED = "The erase may still be running. Keep the disk and Beamo USB connected. Do not start another erase. Contact support."
PREVIEW_OK = "Preview finished"
PREVIEW_FAILED = "Preview of a failed erase"
PREVIEW_NEXT = "Nothing on this computer was erased. No overwrite or verification was performed."

# Plain words for the result screen (#134, owner-approved 2026-11-03). Each
# view's `message` above stays the technical status line: evidence, the saved
# report, the photo record and support keep it, and the screen keeps it under
# Show more (failures also keep it as What happened). Only the two finished
# outcomes get a note and a short What next list; failures keep their What
# happened / What it means for your disk / What to do next sections.
# Never "checked" or "verified" for Quick zero; no certificate or "cannot be
# recovered" wording (docs/claims.md); the SSD limit stays in both notes.
HEADLINE_VERIFIED = "Done — this disk was erased and checked"
HEADLINE_UNVERIFIED = "Done — this disk was overwritten with zeros (not checked)"
NOTE_VERIFIED = (
    "The check read the disk back after the last overwrite. It covers the "
    "storage the disk shows; on an SSD, the disk's controller decides what "
    "remains. Other disks were not erased."
)
NOTE_UNVERIFIED = (
    "Quick zero does not read the disk back, so nothing confirms the "
    "overwrite reached every part. On an SSD, the disk's controller decides "
    "what remains. Other disks were not erased."
)
WHAT_NEXT = "What next"
NEXT_ITEM_SHUT_DOWN = "Shut down when you have finished."
NEXT_ITEM_REMOVE_USB = "When the computer is off, remove the Beamo USB."
NEXT_ITEM_KEEP = (
    "Keeping this computer? If this was its main disk, install an operating "
    "system before you use it again."
)
NEXT_ITEM_GIVE_VERIFIED = "Giving it away or selling it? This disk is ready to pass on."
# {method} is the translated Everyday method name.
NEXT_ITEM_GIVE_UNVERIFIED = (
    "Giving it away or selling it? Erase it again with {method} first — it "
    "checks its work."
)
HEADLINE_VERIFICATION_FAILED = "Not confirmed — the check after the erase failed"
HEADLINE_ENGINE_FAILED = "Not finished — the disk reported an error"
HEADLINE_PROCESS_FAILED = "Not finished — the erase ended with an error"
HEADLINE_COMPLETION_MISSING = "Not confirmed — the erase may not have finished"
HEADLINE_INDETERMINATE = "Not confirmed — the result is unknown"
HEADLINE_INTERRUPTED = "Not finished — the erase was interrupted"
HEADLINE_CANCELLED = "Stopped — you stopped the erase before it finished"
HEADLINE_OCCUPIED = "Not finished — the disk was in use"
HEADLINE_OPEN_FAILED = "Nothing erased — the disk could not be opened"
HEADLINE_GEOMETRY = "Nothing erased — the disk could not be used safely"
HEADLINE_START_FAILED = "Nothing erased — the erase could not start"
HEADLINE_STOP_UNCONFIRMED = "Not confirmed — the erase may still be running"


def _build_views() -> dict[str, ResultView]:
    def remains(step: str) -> str:
        return FILES_MAY_REMAIN + " " + step

    def stopped(step: str) -> str:
        return STOP_WARNING + " " + remains(step)

    return {
        "start_failed": ResultView(
            "start_failed",
            MSG_START_FAILED,
            NEXT_START_FAILED,
            "danger",
            "danger",
        ),
        "verified": ResultView(
            "verified",
            MSG_VERIFIED,
            NEXT_VERIFIED_LEAD + AFTERCARE_SUCCESS,
            "ok",
            "check",
            True,
        ),
        "unverified": ResultView(
            "unverified",
            MSG_UNVERIFIED,
            NEXT_UNVERIFIED_LEAD + AFTERCARE_SUCCESS,
            "warn",
            "warn",
            True,
        ),
        "occupied": ResultView(
            "occupied",
            MSG_OCCUPIED,
            NEXT_OCCUPIED,
            "danger",
            "danger",
        ),
        "open_failed": ResultView(
            "open_failed",
            MSG_OPEN_FAILED,
            remains(NEXT_OPEN_FAILED),
            "danger",
            "danger",
        ),
        "geometry_unusable": ResultView(
            "geometry_unusable",
            MSG_GEOMETRY,
            remains(NEXT_GEOMETRY),
            "danger",
            "danger",
        ),
        "verification_failed": ResultView(
            "verification_failed",
            MSG_VERIFICATION_FAILED,
            remains(NEXT_VERIFICATION_FAILED),
            "danger",
            "danger",
        ),
        "interrupted": ResultView(
            "interrupted",
            MSG_INTERRUPTED,
            stopped(NEXT_INTERRUPTED),
            "warn",
            "warn",
        ),
        "cancelled": ResultView(
            "cancelled", MSG_CANCELLED, stopped(NEXT_CANCELLED), "warn", "warn"
        ),
        "completion_missing": ResultView(
            "completion_missing",
            MSG_COMPLETION_MISSING,
            remains(NEXT_COMPLETION_MISSING),
            "warn",
            "warn",
        ),
        "process_failed": ResultView(
            "process_failed",
            MSG_PROCESS_FAILED,
            remains(NEXT_PROCESS_FAILED),
            "danger",
            "danger",
        ),
        "engine_failed": ResultView(
            "engine_failed",
            MSG_ENGINE_FAILED,
            remains(NEXT_ENGINE_FAILED),
            "danger",
            "danger",
        ),
        "indeterminate": ResultView(
            "indeterminate",
            MSG_INDETERMINATE,
            remains(NEXT_INDETERMINATE),
            "warn",
            "warn",
        ),
        "stop_unconfirmed": ResultView(
            "stop_unconfirmed",
            MSG_STOP_UNCONFIRMED,
            NEXT_STOP_UNCONFIRMED,
            "danger",
            "danger",
        ),
    }


VIEWS = _build_views()

NOTHING_ERASED_CODES = frozenset(
    {"preview", "start_failed", "occupied", "open_failed", "geometry_unusable"}
)

# Outcome codes whose message or next step refers the owner to support.
# Derived from the vocabulary so copy edits cannot silently orphan the
# support destination shown beside them.
SUPPORT_CODES = frozenset(
    code
    for code, view in VIEWS.items()
    if "support" in (view.message + " " + view.next_step).lower()
)


def view_needs_support(code: object) -> bool:
    """True when the outcome's copy refers the owner to support."""
    return isinstance(code, str) and code in SUPPORT_CODES


def may_have_erased(code: str) -> bool:
    """True unless the outcome proves nothing was erased.

    Unknown codes show guidance: the post-erase note is conditional
    ("may"), so it stays honest when the erase state is uncertain.
    """
    return code not in NOTHING_ERASED_CODES


def _apply_language() -> None:
    global VIEWS
    VIEWS = _build_views()


def preview_view(ok: bool) -> ResultView:
    return ResultView(
        "preview",
        PREVIEW_OK if ok else PREVIEW_FAILED,
        PREVIEW_NEXT,
        "info",
        "info",
        ok,
    )


@dataclass(frozen=True)
class PlainResult:
    """What the result screen says in plain words (#134).

    ``checklist`` is empty except for the two finished outcomes; screens then
    show the failure sections (or a preview's next step) as before.
    """

    headline: str
    note: str = ""
    checklist: tuple[str, ...] = ()

    @property
    def numbered(self) -> tuple[str, ...]:
        return tuple(f"{i}. {item}" for i, item in enumerate(self.checklist, 1))

    @property
    def announcement(self) -> str:
        parts = [self.headline + "."]
        if self.note:
            parts.append(self.note)
        if self.checklist:
            parts.append(WHAT_NEXT + ": " + " ".join(self.numbered))
        return " ".join(parts)


def _headlines() -> dict[str, str]:
    # Read at call time so the current language's values apply.
    return {
        "verified": HEADLINE_VERIFIED,
        "unverified": HEADLINE_UNVERIFIED,
        "verification_failed": HEADLINE_VERIFICATION_FAILED,
        "engine_failed": HEADLINE_ENGINE_FAILED,
        "process_failed": HEADLINE_PROCESS_FAILED,
        "completion_missing": HEADLINE_COMPLETION_MISSING,
        "indeterminate": HEADLINE_INDETERMINATE,
        "interrupted": HEADLINE_INTERRUPTED,
        "cancelled": HEADLINE_CANCELLED,
        "occupied": HEADLINE_OCCUPIED,
        "open_failed": HEADLINE_OPEN_FAILED,
        "geometry_unusable": HEADLINE_GEOMETRY,
        "start_failed": HEADLINE_START_FAILED,
        "stop_unconfirmed": HEADLINE_STOP_UNCONFIRMED,
    }


def plain_result(view: ResultView, *, headline_code: str = "", notice: str = "") -> PlainResult:
    """Plain headline, note and What next list for ``view``.

    ``headline_code`` names the outcome to describe when the wizard replaced
    an indeterminate view's message (evidence could not be saved). ``notice``
    (a recovered session) leads a finished outcome's note, because the list
    replaces the next-step paragraph that otherwise carries it. Preview and
    unknown codes keep their own message as the headline.
    """
    code = headline_code or view.code
    headline = _headlines().get(code, view.message) if view.code != "preview" else view.message
    if view.code == "verified" and view.success:
        note, give = NOTE_VERIFIED, NEXT_ITEM_GIVE_VERIFIED
    elif view.code == "unverified" and view.success:
        from beamo_wipe import methods

        note = NOTE_UNVERIFIED
        give = NEXT_ITEM_GIVE_UNVERIFIED.format(method=methods.TITLE_PRNG)
    else:
        return PlainResult(headline)
    if notice:
        note = f"{notice} {note}"
    return PlainResult(
        headline,
        note,
        (NEXT_ITEM_SHUT_DOWN, NEXT_ITEM_REMOVE_USB, NEXT_ITEM_KEEP, give),
    )


def _method_copy_for_locale(spec: Any, language: str) -> dict[str, str]:
    """Rebuild stored method text without changing the UI's global language."""
    from beamo_wipe import lang, methods

    if language not in lang.LANGUAGE_ORDER:
        raise ValueError("Unsupported method language")

    def word(key: str) -> str:
        if language == lang.current():
            return getattr(methods, key)
        if language == "en":
            return lang.english("methods", key)
        return lang.translated(language, "methods", key)

    family = spec.nwipe_method.upper()
    count = spec.overwrite_passes
    title = word(f"TITLE_{family}")
    overwrite = word("OVERWRITE_ONE" if count == 1 else "OVERWRITE_MANY").format(
        count=count, pattern=word(f"PATTERN_{family}")
    )
    if spec.verify == "off":
        verification = word("NO_VERIFY")
    elif spec.verification_passes == 1:
        verification = word("VERIFY_LAST")
    else:
        verification = word("VERIFY_N").format(n=spec.verification_passes)
    description = f"{overwrite} {verification}"
    overwrites = (
        word("OPERATION_ONE") if count == 1 else
        word("OPERATION_THREE") if count == 3 else
        word("OPERATION_N").format(count=count)
    )
    operation = word(
        "OPERATION_VERIFIED" if spec.verification_passes else "OPERATION_UNVERIFIED"
    ).format(overwrites=overwrites)
    return {
        "title": title,
        "description": description,
        "docs_name": description,
        "operation_summary": operation,
    }


def _method_copy_field_matches(actual: object, expected: str, *, sharing: bool) -> bool:
    if actual == expected:
        return True
    if not sharing or not isinstance(actual, str):
        return False
    from beamo_wipe import lang, privacy

    placeholders = {
        privacy.WITHHELD,
        lang.english("privacy", "WITHHELD"),
        *(
            lang.translated(code, "privacy", "WITHHELD")
            for code in lang.LANGUAGE_ORDER
            if code != "en"
        ),
    }
    for placeholder in placeholders:
        if placeholder not in actual:
            continue
        # Sharing may replace any secret substring of canonical copy with a
        # placeholder. Retained words must still be in their original order.
        pattern = ".+".join(re.escape(piece) for piece in actual.split(placeholder))
        if re.fullmatch(pattern, expected, flags=re.DOTALL):
            return True
    return False


def present_evidence(evidence: object) -> ResultView:
    """Interpret a generated/validated record; malformed combinations fail closed.

    File callers must first authenticate the saved bytes. This checks semantic
    consistency, not authenticity of arbitrary user-supplied dictionaries.
    """
    unknown = VIEWS["indeterminate"]
    if not isinstance(evidence, dict):
        return unknown
    try:
        from beamo_wipe.methods import METHODS
        from beamo_wipe.models import MethodId

        from beamo_wipe.evidence import SUPPORTED_SCHEMA_VERSIONS
        from beamo_wipe.privacy import is_sharing_copy
        from beamo_wipe.nwipe_runner import NWIPE_LOG_SNAPSHOT_UTF8_BYTES

        if (
            type(evidence.get("schema_version")) is not int
            or evidence["schema_version"] not in SUPPORTED_SCHEMA_VERSIONS
        ):
            return unknown
        sharing_copy = is_sharing_copy(evidence)
        device = evidence["device"]
        if not isinstance(device, dict):
            return unknown
        if sharing_copy and "path" in device:
            return unknown
        if not sharing_copy and (
            not isinstance(device.get("path"), str)
            or not device["path"].startswith("/dev/")
        ):
            return unknown
        exit_evidence = evidence["exit_evidence"]
        if type(exit_evidence["exit_code"]) is not int:
            return unknown
        exit_code = exit_evidence["exit_code"]
        signal = exit_evidence["signal"]
        if signal != (-exit_code if exit_code < 0 else None) or (
            signal is not None and type(signal) is not int
        ):
            return unknown
        method = evidence["method"]
        if type(method["rounds"]) is not int or type(method["noblank"]) is not bool:
            return unknown
        spec = METHODS[MethodId(method["id"])]
        if any(
            method.get(k) != getattr(spec, k)
            for k in ("nwipe_method", "rounds", "verify", "noblank")
        ):
            return unknown
        # The report prints these stored counts beside the result. They must
        # describe the pinned method that produced the completion verdict.
        if any(
            type(method.get(k)) is not int or method[k] != getattr(spec, k)
            for k in ("overwrite_passes", "verification_passes")
        ):
            return unknown
        locale = evidence.get("locale")
        if not isinstance(locale, dict) or not isinstance(locale.get("language"), str):
            return unknown
        expected_copy = _method_copy_for_locale(spec, locale["language"])
        if any(
            not _method_copy_field_matches(method.get(key), value, sharing=sharing_copy)
            for key, value in expected_copy.items()
        ):
            return unknown
        interruption = evidence["interruption"]
        verification = evidence["verification"]
        completion = evidence["completion"]
        outcome = evidence["outcome"]
        reason = completion["reason"]
        if (
            type(interruption["interrupted"]) is not bool
            or type(interruption["cancelled"]) is not bool
        ):
            return unknown
        if (
            type(verification["verified"]) is not bool
            or verification["requested"] != spec.verify
        ):
            return unknown
        if completion.get("validated") is not True:
            return unknown
        view = unknown
        if outcome == "interrupted":
            if not interruption["interrupted"] or verification["verified"]:
                return unknown
            if (
                reason == "cancelled"
                and interruption["cancelled"]
                and interruption.get("origin") == "user"
            ):
                view = VIEWS["cancelled"]
            elif reason == "interrupted" and not interruption["cancelled"]:
                view = VIEWS["interrupted"]
        elif interruption["interrupted"] or interruption["cancelled"]:
            return unknown
        elif outcome == "failed":
            if reason == "verification_failed" and spec.verify == "off":
                return unknown
            if (reason == "process_failed" and exit_code == 0) or (
                reason == "completion_missing" and exit_code != 0
            ):
                return unknown
            if verification["verified"] or reason not in {
                "occupied",
                "open_failed",
                "geometry_unusable",
                "verification_failed",
                "interrupted",
                "completion_missing",
                "process_failed",
                "engine_failed",
            }:
                return unknown
            view = VIEWS[reason]
        else:
            if (
                exit_evidence["exit_code"] != 0
                or exit_evidence["signal"] is not None
                or reason != "completed"
            ):
                return unknown
            if not sharing_copy and (
                not re.fullmatch(r"[0-9a-f]{64}", evidence["log_checksum_sha256"])
                or type(evidence["log_snapshot_size_bytes"]) is not int
                or not 0 < evidence["log_snapshot_size_bytes"] <= NWIPE_LOG_SNAPSHOT_UTF8_BYTES
            ):
                return unknown
            if outcome == "verified" and spec.verify == "last" and verification["verified"]:
                view = VIEWS["verified"]
            elif (
                outcome == "completed"
                and spec.verify == "off"
                and not verification["verified"]
            ):
                view = VIEWS["unverified"]
        if sharing_copy:
            presentation = evidence.get("presentation")
            if not isinstance(presentation, dict) or any(
                presentation.get(key) != value for key, value in asdict(view).items()
            ):
                return unknown
        return view
    except (KeyError, TypeError, ValueError, AttributeError):
        pass
    return unknown
