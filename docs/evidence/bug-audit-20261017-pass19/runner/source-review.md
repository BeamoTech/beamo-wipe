# Pass19 runner, terminal evidence and report source review

2026-10-17 / Codex delegated runner reviewer. Source-only review of the shared
`fix/safety-audit-20261015` checkout, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673` plus the existing uncommitted audit
work. This note records inspection, not runtime acceptance. No application,
engine, native inventory, subprocess proof, device access or network call was
performed by this reviewer. Product and test source were not edited.

Current `AGENTS.md`, the relevant pass18 unfinished record, memory index and
the pass18 pinned-upstream record-origin review were read. Historical guide
text does not authorize physical-media, guest, publisher or hosted actions.

## Inspected contracts and source evidence

- `nwipe_runner.py:374` and `:411`: argv is bound to the selected pinned method;
  each required flag occurs exactly once, the sole positional target is last,
  boot exclusion is required and unexpected/force flags are refused. The
  final real-engine identity and competing-process checks occur under the
  one inherited wipe lock before spawn (`:1170` onward).
- `nwipe_runner.py:1117`: attempts clear prior result/observation/assessment and
  ownership state. Duplicate attempts refuse before log truncation. Readiness
  and signal cadence also reset at `:1213`; they are not inherited by retry.
  The named lock and original retained log inode are checked again before
  spawn. Parent-side ambiguous spawn failures retain uncertain ownership.
- `nwipe_runner.py:1313`: poll is bound to its active immutable request and
  process. Status probes are serialized; slow observation reads use a sequence
  token and process identity before publishing. Native SIGUSR1 requires its
  complete timestamped option/I/O record, not a model continuation or elapsed
  startup guess.
- `nwipe_runner.py:1429` and `:1503`: bounded reads bind the launch log inode,
  reject unstable reads and discard a cut first record for telemetry. Large
  completion projection requires complete LF records, bounded line/relevant
  evidence budgets and a stable complete file signature. It retains the first
  native-origin record, distinct initialized method denominators, final
  progress in its original table context, contradictory records and shared
  truncated device-column context.
- `nwipe_runner.py:852` and `:974`: process exit and 100% alone are insufficient.
  No-erasure statements lose priority when target activity contradicts them;
  explicit failure/mismatch/nonzero error rows defeat success. Completion is
  method-aware, requires the correct final phase/counters when using progress,
  and refuses incomplete terminal records. Quick zero remains unverified.
- `nwipe_runner.py:1726`: cancellation retains the registered process and lock
  until exit/cleanup is confirmed. Pre-signal natural exit uses terminal
  classification. In-flight stale poll/cancel results cannot replace a newer
  run. A still-live process or uncertain close keeps retry/shutdown guarded.
- `wizard.py:2302`: a ready-but-unavailable full-log assessment is supplied as
  an empty assessment to evidence; it does not accidentally fall back to a
  successful-looking suffix.
- `evidence.py:260`, `:552`, `:601` and `:654`: result creation re-evaluates
  method-aware completion, records exact normalized snapshot size/digest and
  keeps interruption dominant. Recovery authenticates evidence and the actual
  snapshot before returning success or a nothing-erased explanation. Regular
  file reads are size-bounded and stable; atomic publication never replaces an
  existing report and retires only its own publication on finalization failure.
- `session_recovery.py:298`, `:389`, `:551` and `:580`: records have exact fields,
  same-boot/build/session identities, unique baseline paths, positive target/
  boot sizes and a constrained terminal reference. Same-inode private locks
  govern journal writes and cached quiescence. Recovery binds device, method,
  log, engine, provenance and monotonic times before authenticating the result;
  no erase authorization or process resume is reconstructed.
- `support_export.py:1160`, `:1463`, `:1688` and `:2177`: log export authenticates
  the exact UTF-8 snapshot, rejects changed/unsafe files and rechecks successful
  and nothing-erased claims. README check passes require complete corroborating
  log evidence. Report COMPLETE is content-only; persistence/readback/removal
  have separate boundaries. No physical export procedure was executed here.
- `progress.py:335` onward, `engine_checks.py` and `result_summary.py`: progress
  remains display-only, finite/range/counter constrained and clock/staleness
  guarded. Advisory pass claims require complete records and provenance;
  malformed/contradictory input is unavailable. Readable report fields flatten
  controls and escape HTML, use canonical method prose and guarded result views.

## Rejected hypotheses

1. **Readiness retained by retry:** false; reset is present at runner 1213–1214.
2. **Failed whole-log scan falls back to a successful tail:** false in the
   actual wizard path; wizard 2302–2305 supplies an empty assessment.
3. **Model LF forges a native no-erasure/readiness record:** no new supported
   path. The prior official pinned nwipe/Debian source review establishes
   retained-LF model bounds, line-oriented sysfs/DMI handling and processed
   serial limits. Do not revive the rejected universal NVMe 40-byte claim.
4. **Projection discards early contradictory counters/origin:** distinct known
   denominator observations and the first native record are retained. Relevant
   negative records and error-table bodies/separators are also retained.
5. **Export treats a checksum or COMPLETE as erase proof/safe removal:** the
   controller additionally authenticates and classifies the snapshot; COMPLETE
   explicitly has `safe_to_remove: false`, and later readback/removal owns the
   removal receipt. A virtual read cannot prove physical reconnect acceptance.
6. **A stable replacement log can complete another request:** launch identity
   is checked, original inode retained, polling request is immutable/bound, and
   recovery additionally binds the journal's evidence digest and identity.

No new concrete runner/evidence/report defect was proved in this source-only
round, and no speculative product correction is recommended. This does not
clear the retained GTK latency, fixture-cleanup, historical incident or platform
acceptance blockers. The root owns serial fake-device proofs and final gates;
fresh campaign results must be tied to its final frozen bytes. Existing pass18
campaign scripts are prepared but were not run after that failed local gate.
