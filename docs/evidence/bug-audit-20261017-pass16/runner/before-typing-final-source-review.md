# Pass16 final runner/evidence and incremental union source review

2026-10-17; Codex delegate `/root/pass16_runner`.
BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`, branch
`fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`; all work remains local.

**No source-level objection to the reviewed final bytes.** This is an independent
source review, not a substitute for root's final runtime gates or acceptance.
No runtime campaign or source/test edit was performed for this review.

## Assigned sources remain unchanged

All13 originally reviewed files exactly match starting-source-hashes.json:
nwipe_runner.py,progress.py,engine_checks.py,evidence.py,outcomes.py,
session_recovery.py,support_export.py,report_intent.py,privacy.py,
diagnostic_report.py,sleep_inhibit.py,models.py,methods.py.
The exact final SHA256 values are in final-source-review.json. The earlier
153semantic/153large/90roundtrip/144cancel campaign source receipts consequently
still describe those files, subject to root's independent final validation.
No new runtime pass is asserted here.

## Independently reconstructed incremental union

Compared every source/static member in root's exact starting-source.tar.gz with
current bytes, without restoring or mutating shared files. The only incremental
source changes are discover.py,ui/accessible_wizard.py and ui/tk_wizard.py.
The independently generated final-union.diff and its SHA256 are retained;
final-source-review.json also records exact hashes of all58 compared files.
This comparison distinguishes this pass's changes from earlier uncommitted work.

- Discovery command-line boot ambiguity now considers all physical disk/rom
  observations, including picker-hidden media. Mount-derived identity still
  takes precedence. This only adds refusals when another plausible live medium
  makes command-line identity uncertain; it never creates a selectable target,
  repairs an identifier, changes an authorization token or changes nwipe argv.
- Discovery records repeated canonical physical paths before display filtering.
  A duplicate with only one surviving selectable row now refuses instead of
  losing the duplicate and appearing unique. Contradictory facts retain their
  earlier refusal. Two surviving rows remain two observations for the existing
  unique-target identity guard; zero eligible rows cannot become targets.
  No retained context is promoted into SessionStore or selectable/token peers.
- GTK's extracted `_remember_key_press` preserves the original parent guard
  logic and applies it to modal key presses too. First modal presses still
  propagate to ordinary dialog handlers; held/repeated guarded keys are
  consumed when the parent receives them after modal closure. Key release and
  X11 same-timestamp repeat-pair handling remain unchanged. This strengthens
  separate-action ownership without changing owner/token/countdown gates,
  method selection, cancellation implementation or erase process construction.
- Tk callback cleanup enumerates only the subtree being destroyed, identifies
  pending after scripts through their owning widget's Tcl command registry,
  and calls after_cancel on that owner. `_clear` excludes the surviving frame;
  root-owned poll/key-release/refresh jobs therefore remain during redraw.
  Full teardown marks the UI dead, cancels existing known jobs and retires the
  remaining root subtree callbacks before root.destroy. Callback cancellation
  does not invoke callbacks, authorize erasure, cancel an erase process, alter
  evidence or signal power. A newly rendered confirmation entry schedules its
  own focus callback; stale entry jobs are retired with their old widgets.

## Evidence, cancellation, argv and recovery implications

No runner, method, request/model, safety, evidence, outcome, export or recovery
bytes changed this pass. Existing one-target-plus-boot-exclude flags, pinned
engine, process registration, late Stop classification, uncertain-stop lock
retention, terminal cleanup and exact log/evidence authentication remain intact.
The UI changes cannot publish a terminal result or offer shutdown independently
of the wizard's guarded state. Discovery adds fail-closed refusals and supplies
no new authority. No completion, verification, successful export or recovered
success check was weakened. Quick zero remains unverified.

Root owns final focused/full gate reruns, exact source freeze, artifacts and
canonical unfinished record. Historical pass8 signal/pass9 timing attribution
and separate image/native/physical qualification remain outside this source
approval. Any later byte change invalidates approval for that changed file.
