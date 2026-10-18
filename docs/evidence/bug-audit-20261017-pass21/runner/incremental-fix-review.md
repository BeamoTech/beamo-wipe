# Independent incremental fix review

2026-10-17 / Codex delegate `/root/pass21_runner_reports`; source-only second
round. The adjacent JSON records exact source, archive, diff and root-owned test
receipt identities. All 779 starting archive inputs were authenticated against
their freeze; exactly the four inspected runtime files differ, and the other
775 starting inputs remain unchanged. No delegate product import or runtime
occurred. No shared source/test edit was made.

**Verdict: PASS source review of the proved bounded changes.** Final canonical
modules, final source freeze and full gate acceptance remain pending and require
a subsequent exact-byte review.

- `diagnostics.py`: adding Unicode Zl/Zp to the existing space-replacement
  condition fixes the writer/reader framing and fallback display issue at its
  common sanitizer. Control-character replacement, truncation, normal Unicode,
  field bounds, file ownership and JSON framing remain unchanged. Root reports
  the unchanged original29-case proof as20FAIL/nine controls. This delegate
  re-read the proof and root receipts without rerunning them.
- `discover.py`: only conversion of a floating infinity's `OverflowError` into
  the existing malformed-value `ValueError` route changes numeric handling.
  Finite int/float/exponent behavior remains unchanged. Physical disks without
  a nonempty slash-free kernel name are refused before a target can be minted;
  flat PKNAME layout and content evidence can therefore bind to admitted names.
  This strengthens exclusion and does not expand an eligible target set.
- `tk_wizard.py`: four existing Variable factories explicitly use the creating
  root. The owned-trace helper adopts the original registration token before
  the inspected outer `trace_add` return/failure boundary. It matches callback
  identity, adopts only the first matching registration, preserves independent
  peer registrations, and restores a preexisting instance `_register` override
  exactly unless a peer replaced the temporary override. Existing teardown still
  removes only the known owned token. Native constructors/destructors and
  traceback identities remain intact; no GC thresholds/modes change.
- Both refresh surfaces put Event creation under failure handling and keep the
  wake/acceptance decision under the same lock that gates discovery entry. An
  Event.set that wakes and then raises leaves acceptance false, resolves the
  claimed refresh as failed and preserves the original failure object. Tk
  schedules its result poll before accepting the worker and drops abandoned
  ownership. GTK retains its existing timer-drained result handling. These
  claims refer to the proved injection points, not every possible Python
  bytecode interruption.
- `accessible_wizard.py` close collects failures while attempting audio,
  dialog, timer, window and loop cleanup independently; retires the timer handle
  once; then rethrows the first original failure with later failure-type notes.
  Existing close idempotency remains. Closing the interface does not claim an
  erase process stopped; engine settlement remains the controller's separate
  responsibility.

The incremental diff does not change nwipe invocation, method mapping,
authorization/token/countdown, process cancellation/locking, log/evidence
storage, report mounting/export, shutdown policy, shipped surface boundaries,
engine/toolchain/release pins, claims, boot scripts, CI/publication, Companion or
USB Easy Use. The root-owned focused receipt was re-read:338 cases,0 failures,
errors or skips on the selected current input paths. Its result is distinct
from unrun final gates and from this delegate's source review.

Remaining acceptance is exact final tests/freeze inspection, fresh applicable
local gates, artifact/visual readback and durable handoff. Historical incident
attribution and unavailable platform/hardware qualifications remain separate.
