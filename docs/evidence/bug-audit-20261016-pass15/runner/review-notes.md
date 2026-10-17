# Pass15 runner / evidence source audit

2026-10-16, Codex delegate /root/pass15_runner. BeamoTech/beamo-wipe,
/root/dev/Beamo Wipe, fix/safety-audit-20261015,
HEAD 35107a8d1a701093eac876a58ab4efd50e291673; uncommitted prior fixes preserved.
Read current AGENTS.md, relevant memory index/product constraints and unfinished
pass14 record. No product/test edit, commit, process/inventory/device/power/VM,
credential, hosted or external operation. Runtime scripts await root admission.

## Source reviewed and dispositions

- NwipeRunner start: both initial and under-lock duplicate refusals cover slow
  concurrent preflight; retained log FD closes inode-reuse hole. Late duplicate
  cannot discard ambiguous spawn ownership. Known child exec error releases;
  unknown parent-side spawn failure retains flock/log. No new defect proved.
- poll/progress/cancel: identity/sequence guards prevent old observations and old
  terminal readers replacing later runs; active request binding preserved.
  Status-probe ownership permits cancel wait as independent exit proof. Wait
  timeouts retain registration/lock; late Stop uses natural terminal evidence.
  Error paths retain uncertainty and do not offer a false clean terminal result.
- Completion projection: retains initialized method counter totals, last progress
  at original table position, failure/skip/abort/geometry records, summary/table
  separators and status-column collision marker. Full-line/whole-file/relevant-
  evidence caps fail closed. Fresh method/phase/context/collision combinations
  prepared in projection-state-matrix.py rather than editing retained tests.
- Evidence build: terminal verdict is revalidated against method-aware assessed
  log; exported snapshot remains exact tail checksum/size. Failed projection is
  mapped by controller to empty assessed log, not successful tail fallback.
- Recovery/ReportIntentStore: private modes, duplicate fields, byte bounds,
  stable descriptor metadata, directory/name identity, interface/flock ownership,
  same-boot/source journal and exact terminal evidence references remain checked.
  No resumed authorization is stored. No new defect proved.
- Export: baseline + two scans + rdev protections, worker identity recheck,
  directory-relative exclusive files, COMPLETE-after-content+fsync, read-only
  remount/readback, exact saved receipt and safe-removal check remain intact.
  No native export or real medium can be exercised here.
- Privacy: sharing allowlist scalar leaves, identifiers collected/scrubbed,
  canonical result wording rebuilt from validated core; owner bytes retained.
  No serial-bearing support code or newly introduced privacy leak proved.
- Large log recovery/export conservative refusal is intentional: a run may
  complete from its whole projection while its exact tail lacks any completion
  marker; recovery/export require that saved tail to corroborate success. This
  is a known conservative limitation, not a new claimed bug.

## Unproved candidate

engine_checks._HIDDEN_NONE accepts a path token prefix and arbitrary trailing
text. A timestamped malformed `No hidden sectors on /dev/sda/...` or appended
contrary text appears able to produce a hidden-capacity PASS. Existing tests
cover sdab/sda1/sda-test but no slash/trailing junk. Need parser trace, then
independent decision against module contract: malformed => unavailable, never
pass. Source-only suspicion is not a finding or authorization to modify code.

## Starting source hashes (SHA256)

- nwipe_runner.py: 7672c9c0646aa9679b87d9b729c3f9228f0cf1b7f9bb4b1c162a7e37e16dbf9b
- evidence.py: 512c9b024b3231bf2625b6c802a8dc2282c275153b62e2995d4d01ba9466b5c5
- engine_checks.py: a93a8c91feab0db967e6834367856b5d3a77b37d32a0d7c3bd8b6b7fb4b24183
- session_recovery.py: 128c5daa4c53197437682c637d3078917a79037a9edf5d1796fc9916cdd4ba53
- support_export.py: 23308f130079eb98cc8f77c597e227efbbf1cdb06234dd1336b2e034660bcc04
- report_intent.py: f147d8840ae6f8f9d58d07111b2f6c4db9e8792e1e30beb1f96f82afdb482c25
- privacy.py: bcb9c6ce4764a7e6df54b970aede4003c3f90357535fc42530b831eeef0face2
- diagnostic_report.py: fc01e84c6f917d679ea743bc104c5c5d6031de34bd9d68b6f6ee43f63986a1dd
- outcomes.py: 3bd0f5bc6f130a710d7552bb48cf6321630fa549e21e3727e1bf1c4e7dafa183

## Admitted runtime results

Root granted exclusive admission after UI probe completed. Ran the three scripts
sequentially; each exited normally0. Lane released after completion. All device
names were inert strings, all logs/evidence regular files. Actual process and
inventory boundaries were replaced with hard failures. No product/test edit.

### Confirmed defect: UTF-8 raw/normalized snapshot bound mismatch

- Exact-source utf8-tail-probe.py ran30cases across3methods and ten complete valid
  UTF-8 raw logs. é/€/😀 are each cut at every interior byte by the raw1MiB tail.
- 18interior-cut cases: runner.ok true; generated outcome verified/completed;
  generated/direct presentation and recovery indeterminate; terminal export
  readiness raises SafetyError malformed evidence.12whole-codepoint controls
  preserve verified/unverified presentation, recovery and export readiness.
- Example: complete valid UTF-8 raw1048577bytes, tail starts at the second byte
  of é. Replacement decoding normalizes the1MiB capture to1048578UTF-8 bytes.
  The runner's full projection proves completion, read_export_log authenticates
  the normalized snapshot with status tail, but outcomes.py rejects its size.
- Root cause: outcomes.present_evidence limits the **normalized** captured size
  to the **raw** read bound1024*1024. Decoder errors='replace' may expand invalid
  boundary bytes even when the original entire file is validUTF-8. Maximum
  expansion is bounded3×rawbytes. read_export_log already reconstructs capture
  normalization and allows8MiB; no unsafe relaxation or unbounded read needed.
- Artifacts utf8-tail-probe.{py,json,txt}, utf8-tail-exit.json,
  utf8-exact-log-fixtures.tar.gz (ten exact fixtures). Ordinary raw files and
  authenticated evidence/sidecars also remain in utf8-tail-probe/.
- No production effect, native inventory, device or engine operation occurred.
  Proof violations are not passing regression outcomes. Root independently
  validates and decides/implements any fix.

### Malformed positive hidden-storage candidate

- hidden-record-probe.py:54pure-parser traces, exit0. Normal/whitespace positives
  pass; three genuine negative-only/negative-before/negative-after sets each
  unavailable; foreign negative control leaves pass. Slash-only suffixes are
  excluded by _mentions (correctly anticipated by root); slash plus a later
  explicit target mention can cause prefix attribution for /dev/sda.
- Trailing ' -- HIDDEN SECTORS INDETERMINATE!', ', except an unknown HPA',
  ' uncertain', ' (indeterminate)', ': unknown', NUL and Unicode line separator
  still produce PASS, contradicting the module's malformed=>unavailable wording.
  Known hdparm-invalid suffix correctly makes the result unavailable.
- This is independent of the UTF-8 bound finding and has weaker real-engine
  reachability: pinned positive engine records end at the device name. Root
  should independently assess whether strict positive-line validation is
  appropriate; no unsafe selection/erase or engine behavior is alleged.
- Artifacts hidden-record-probe.{py,json,txt}, remaining-exits.json.

### Fresh projection and terminal/Stop combinations

- projection-state-matrix.py:432short full/projection cases PASS,324actual
  >1MiB fake poll/late-Stop/running-Stop cases PASS,0mismatches/0native calls.
- Three device families, three methods, four initialized phases, twelve
  context/order/error/collision/model variants. Explicit negative summaries
  and contradictory method counters have independently asserted reasons.
- All logs unchanged; all fake process slots retired. Source bytes unchanged.
  108distinct exact large fixtures retained in exact-large-fixtures.tar.gz;
  short/full/projection hashes and all case outcomes in projection-rows.json,
  actual-large-results.json; projection-summary.json records exact source hashes.
- Short-name targets cannot share an eight-character status cell; those are
  explicit no-collision controls alongside long NVMe/eMMC collision cases.
- Commands/exits retained; elapsed22.537s. This bounded runtime campaign was
  alone in the shared runtime lane.

## Authorized regression module (prepared, not executed by delegate)

Root independently repeated the30-case UTF-8 trace and approved writing only
`tests/test_utf8_log_snapshot_bounds_pass15.py`. Added38cases:30valid UTF-8 edge
cases across3methods;3actual near-worst-case invalid-UTF8 raw1MiB captures;
5invalid type/nonpositive/over3MiB size-metadata refusals. Each functional case
covers fake runner completion, exact normalized bytes/digest, generated outcome
and presentation, atomic evidence/checksum, authenticated read_export_log,
recover_result, prepare_terminal_evidence, and unchanged source log. Native
process/inventory acquisition and /dev,/sys,/proc opens fail the fixture.
Module does not import the proposed new constant, so original-source tests fail
for the semantic defect rather than missing import. Primary owns source repair
and runtime admission. No production source edit by this delegate.
Prepared module SHA256:
50a3592d799553f2ec9adf24b1703fac2b85e7b818f1e908d3db28b2ac231dbf.
