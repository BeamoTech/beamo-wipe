# SPDX-License-Identifier: GPL-3.0-or-later
"""The result screen's "Save a report" panel (#135), one model for every UI.

The panel turns the locked report snapshot and the latest read-only USB
detection into numbered steps, one status line and which controls to show.
It never starts or gates an export: Save still runs the wizard's evidence
gate and the export's own scans. Strings come from ``copy`` at call time so
a language switch applies.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

STEP_DONE = "done"
STEP_NOW = "now"
STEP_TODO = "todo"


@dataclass(frozen=True)
class ReportStep:
    text: str
    state: str = STEP_TODO


@dataclass(frozen=True)
class ReportPanel:
    """Panel kinds: preview, preparing, evidence, unavailable, ready,
    saving, saved, failed. ``usb`` is the detection state for ready/failed.
    """

    kind: str
    tone: str
    headline: str
    steps: tuple[ReportStep, ...] = ()
    detail: str = ""
    usb: str = ""
    show_save: bool = False
    save_enabled: bool = False
    save_reason: str = ""
    show_retry: bool = False
    retry_enabled: bool = False
    retry_reason: str = ""
    notice: str = ""

    @property
    def step_lines(self) -> tuple[str, ...]:
        from beamo_wipe import progress as P

        marks = {STEP_DONE: P.STAGE_DONE_MARK, STEP_NOW: P.STAGE_NOW_MARK}
        return tuple(
            f"{index}. {step.text}{marks.get(step.state, '')}"
            for index, step in enumerate(self.steps, 1)
        )

    @property
    def lines(self) -> tuple[str, ...]:
        """Everything the panel says, in reading order (consoles, tests)."""
        out = [self.headline]
        if self.detail:
            out.append(self.detail)
        out.extend(self.step_lines)
        if self.show_save and not self.save_enabled and self.save_reason:
            out.append(self.save_reason)
        if self.show_retry and not self.retry_enabled and self.retry_reason:
            out.append(self.retry_reason)
        out.append(self.notice)
        return tuple(line for line in out if line)


def usb_status(usb: Any) -> str:
    """The live detection line for one probe result (None: not checked)."""
    from beamo_wipe import copy as C
    from beamo_wipe import support_export as X

    if usb is None:
        return C.REPORT_USB_ON_SAVE
    state = getattr(usb, "state", "")
    if state == X.PROBE_FOUND:
        return C.REPORT_USB_FOUND.format(label=usb.label, filesystem=usb.filesystem)
    if state == X.PROBE_NONE:
        return C.REPORT_USB_NONE
    if state == X.PROBE_MANY:
        return C.REPORT_USB_MANY
    if state == X.PROBE_FORMAT:
        if usb.filesystem:
            return C.REPORT_USB_FORMAT.format(filesystem=usb.filesystem)
        return C.REPORT_USB_FORMAT_UNKNOWN
    if state == X.PROBE_REFUSED:
        next_step = X.next_step_for(usb.detail)
        return f"{usb.detail} {next_step}".strip() if next_step else usb.detail
    if state == X.PROBE_UNAVAILABLE:
        return C.REPORT_USB_UNAVAILABLE
    return C.REPORT_USB_LOOKING


def _ready_steps(usb: Any) -> tuple[tuple[ReportStep, ...], bool]:
    """Steps 1-5 before saving, and whether Save may be pressed now."""
    from beamo_wipe import copy as C
    from beamo_wipe import support_export as X

    found = usb is not None and getattr(usb, "state", "") == X.PROBE_FOUND
    unchecked = usb is None
    status = usb_status(usb)
    steps = (
        ReportStep(C.REPORT_STEP_INSERT, STEP_DONE if found else STEP_NOW),
        ReportStep(status, STEP_DONE if found else (STEP_TODO if unchecked else STEP_NOW)),
        ReportStep(C.REPORT_STEP_SAVE, STEP_NOW if found or unchecked else STEP_TODO),
        ReportStep(C.REPORT_STEP_WHERE),
        ReportStep(C.REPORT_STEP_REMOVE),
    )
    return steps, found or unchecked


def build_report_panel(
    report: Any,
    *,
    preview: bool,
    usb: Optional[Any],
    evidence_warning: str = "",
) -> ReportPanel:
    """One panel state from a ``ReportView`` and the latest USB probe.

    ``usb`` None means live detection is not running (a fixture-injected
    exporter); Save is then offered and checks the USB itself.
    """
    from dataclasses import replace

    from beamo_wipe import copy as C

    panel = _build(report, preview=preview, usb=usb, evidence_warning=evidence_warning)
    if panel.kind == "preview":
        return panel
    notice = C.REPORT_STATUS_NOTICE
    if panel.kind != "saved":
        notice += " " + C.REPORT_VOLATILE
    return replace(panel, notice=notice)


def _build(
    report: Any, *, preview: bool, usb: Optional[Any], evidence_warning: str
) -> ReportPanel:
    from beamo_wipe import copy as C

    if preview:
        return ReportPanel("preview", "info", C.REPORT_PREVIEW)
    if report.saving_evidence:
        return ReportPanel("preparing", "info", report.headline, detail=evidence_warning)
    if report.evidence_error:
        # Ref #153: the evidence failure stays a prominent warning with its
        # own Retry, before anything about USB sticks.
        return ReportPanel(
            "evidence", "warn", report.headline, detail=evidence_warning,
            show_retry=True, retry_enabled=bool(report.can_retry_evidence),
            retry_reason=C.RETRY_UNAVAILABLE,
        )
    if report.status == "saving":
        steps = (
            ReportStep(C.REPORT_STEP_INSERT, STEP_DONE),
            ReportStep(C.REPORT_STEP_CHECKING, STEP_NOW),
            ReportStep(C.REPORT_STEP_SAVING, STEP_NOW),
            ReportStep(C.REPORT_STEP_WHERE),
            ReportStep(C.REPORT_STEP_REMOVE),
        )
        return ReportPanel(
            "saving", report.tone, report.headline, steps=steps,
            detail=C.EXPORT_GUIDE_WORKING,
        )
    if report.status == "saved":
        steps = (
            ReportStep(C.REPORT_STEP_INSERT, STEP_DONE),
            ReportStep(C.REPORT_STEP_CHECKED, STEP_DONE),
            ReportStep(C.REPORT_STEP_SAVED, STEP_DONE),
            ReportStep(report.message, STEP_DONE),
            ReportStep(C.REPORT_STEP_REMOVE_NOW, STEP_NOW),
        )
        return ReportPanel("saved", report.tone, report.headline, steps=steps)
    if not report.can_save:
        detail = report.message or C.REPORT_NOT_OFFERED
        if report.status == "error":
            detail = _failure_text(report.message)
        return ReportPanel("unavailable", report.tone, report.headline, detail=detail)
    ready_steps, ready = _ready_steps(usb)
    kind = "failed" if report.status == "error" else "ready"
    return ReportPanel(
        kind, report.tone, report.headline, steps=ready_steps,
        detail=_failure_text(report.message) if kind == "failed" else "",
        usb=getattr(usb, "state", "") if usb is not None else "",
        show_save=True, save_enabled=ready,
        save_reason="" if ready else C.REPORT_SAVE_WAIT,
    )


def _failure_text(message: str) -> str:
    """What happened / what to do for a failed save (existing wording)."""
    from beamo_wipe import copy as C
    from beamo_wipe.recovery import format_recovery_text, recovery_for_export
    from beamo_wipe.support_export import next_step_needs_support

    text = format_recovery_text(recovery_for_export(message), compact=True)
    if next_step_needs_support(message):
        text += "\n" + C.support_text()
    return text
