# Pass16 runner, evidence, export and recovery source review

2026-10-17; Codex delegate `/root/pass16_runner`.
Repository `/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`,
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`; dirty prior work preserved.
Current AGENTS, relevant memory index/product constraints, unfinished pass15
record and pass15 evidence/review notes read. Shared guide is absent with the
recorded owner continuation. Notes confer no additional authority.

No product/test edits, staging, commit, push, PR, hosted job, credentials,
external messages, native inventory/engine, devices, power/firmware, guest/loop
or mount operation. All prepared runtime campaigns await root admission.
Exact starting file hashes are in starting-source-hashes.json.

## Reviewed paths and conclusions

- Launch/argv: exact one positional canonical whole-disk path plus boot exclude;
  known method/rounds/verify/noblank bound to confirmed method. `--force`,
  duplicate/unknown flags, alternate engine basename/path, uncontrolled log
  destinations and missing real-live environment remain refused. Engine/version
  checks, rdev/size/transport/identity rediscovery repeat under the shared lock.
- Process ownership: duplicate start is refused both before preflight and under
  the lock. Named wipe-lock and retained log-inode checks occur again directly
  before Popen. Known reaped child exec errors release resources; uncertain
  parent-side failures retain lock/log ownership. No new defect established.
- Poll/concurrency: request/process/sequence checks prevent stale callers,
  observations and terminal reads from overwriting a replacement run. Process
  polling is claimed independently of cancellation waits. Progress remains
  below100 until explicit successful method-aware completion.
- Cancellation: pre-signal and late natural exits classify complete logs;
  `ProcessLookupError` does not itself prove cancellation. Wait timeouts and
  cleanup errors retain process/lock uncertainty. A failed wait permits a later
  retry; the wizard remains guarded until confirmed cleanup. Sleep inhibitor
  stop is called by `_release_wipe_lock` on all relevant refusal/terminal paths.
- Parsing/projection: exact final decimal100, initialized method denominators,
  final writing/verifying phase, exact Drive Status banner, target-binding,
  colliding eight-character cells, explicit negative markers and Error Summary
  conflicts remain conservative. Whole-log projection keeps all error-table
  context, first occurrences of initialized denominator pairs, last progress at
  original context position, status rows, warning records and collision facts.
  Unreadable/changed/replaced/capped/incomplete logs remain indeterminate.
- Snapshot normalization: raw1MiB reads and normalized3MiB evidence cap remain
  finite and distinct. read_export_log reconstructs exact captured suffix
  decoding, then authenticates length/digest before recovery/export. No new
  raw-vs-normalized bug established by source review.
- Evidence/outcomes: result.ok cannot upgrade a contradictory assessed log;
  absent/failed assessment is mapped to empty assessed text by controller.
  Quick zero cannot be verified. Exact type/method/count/copy/exit/interruption
  consistency and authenticated private evidence bytes remain required.
- Recovery: same boot/build journal, private directory/name/lock identities,
  exact terminal digest, target/boot context and monotonic times are checked.
  Consent/request/countdown do not survive as authorization. Success and
  nothing-erased claims require exact saved log corroboration.
- Export: baseline target/boot remain required; optional identity loss/movement,
  duplicate hardware IDs, ambiguous weak identities and extra new USBs refuse.
  Controller and worker repeat discovery/rdev checks; private mount namespace
  writes bounded directory-relative exclusive files, publishes COMPLETE only
  after content+fsync, read-only remount/readback and ordinary unmount.
  Actual mounts/devices are outside this audit's runtime authorization.
- Privacy/reports: sharing allowlist strips identifiers, paths/logs/nested
  payloads; canonical result copy is regenerated from validated core. Original
  owner evidence bytes are retained. Safe support destinations/codes and report
  receipts remain structured and exact. No fresh privacy defect established.
- Display timing: progress observations are not completion evidence; exact
  terminal clock validity, stale samples, phase/counter/quantum changes and
  measured/engine ETA agreement gate estimates. No fresh timing defect proved.

## Candidates rejected or pending

1. Large-log success whose completion lies outside authenticated tail may be
   indeterminate in recovery/export. This is the explicit conservative
   limitation recorded in pass15, not a new bug or justification to relax
   corroboration.
2. A separate malformed positive hidden-storage line can be ignored when an
   independent complete positive line exists. Fresh traces are prepared to
   assess this. A malformed line is not automatically a trustworthy negative;
   source suspicion alone is not a supported bug. Mixed-record behavior must be
   evaluated against the intended whole-log contract before any repair.
3. Binary replacement between validation and exec would require privileged
   mutation of the pinned immutable live image. No supported product defect
   or new permission follows from that hypothetical threat.
4. A child diagnostic helper outliving nwipe does not establish another erase
   engine. Cancellation ownership concerns require proof of an erase-capable
   process, not speculation about helper lifetime.

## Prepared bounded runtime work (not yet run)

- fresh-boundaries.py: 153 semantic/full-projection cases,153 actual >1MiB fake
  terminal polls, successful evidence/export/recovery roundtrips and suffix
  tamper refusal;54 mixed malformed-advisory traces.
- cancel-boundaries.py:144 fake cancellation cases across three device families,
  three methods, complete/incomplete logs and eight natural/error/timeout/retry
  states. Real private ordinary-file flock/log descriptors must stay retained
  while uncertain and retire after confirmed exit. No OS PID is signaled and
  fake waits never sleep.
- Native subprocess/inventory and `/dev`, `/sys`, `/proc` opens are guarded;
  target paths are inert strings. Preparation changed only /tmp/pass16-runner.

## Admitted runtime results and final disposition

Root explicitly admitted the two campaigns in sequence, after the UI lane ended.
Executed with `/root/dev/Beamo Wipe/.venv-linux/bin/python3`; both exited normally0.
No campaign was stopped/killed/timed out. Command receipts are in
command-exits.json. Runtime lane was released immediately after inspecting JSON
outcomes; no further runtime campaign is active on this delegate.

- fresh-boundaries.py:153 explicit semantic/full-projection cases PASS and153
  actual >1MiB fake terminal polls PASS. Negative/error/advisory prefixes were
  placed before padding, with final status afterward, so the actual scan had
  to preserve early facts outside the captured tail. Seventeen context/order/
  failure/counter/advisory variants across three device families and methods;
  zero mismatches, zero semantic errors, unchanged source.
-90 successful generated evidence/presentation/exact suffix/export-readiness/
  atomic checksum/recovery roundtrips PASS. Appending to the authenticated log
  makes recovery indeterminate; exact byte restoration permits recovery again.
  Quick zero remains unverified. No native export or mount was used.
- cancel-boundaries.py:144 fake process cases PASS. Natural exits are retained;
  status/wait errors and TERM/KILL timeouts follow expected uncertainty/retry
  semantics. Private ordinary-file lock/log descriptors remain open during
  uncertain stop/wait and are closed before terminal publication. Fake wait
  methods never sleep; fake terminate/kill never signal an OS PID. Every final
  process/status/cancellation slot and descriptor is retired.
- Both campaigns guard subprocess/inventory and native device/sys/proc opens;
  zero acquisition attempts. Exact source hashes are included in summaries.
-54 exploratory mixed malformed-positive traces yield18PASS each for malformed
  record before, after, or foreign to a complete valid positive record. This
  does not establish a new bug: an independent complete positive record remains
  proof while an invalid positive line is ignored; it is not a trusted negative
  record. Genuine target indeterminate records in the semantic matrix still
  override positives, while foreign negatives do not apply. No erase outcome
  changes. Root may independently assess stricter advisory policy, but no
  repair or regression module is proposed from these exploratory traces.

No supported fresh bug found in this assigned runner/evidence/export/recovery/
privacy source and runtime scope. Limits: bounded fake-only campaigns do not
constitute actual nwipe, mount, ISO/QEMU, Windows or physical-device acceptance.
Historical pass8 signal and pass9 timing blockers remain unresolved; these
passing checks do not attribute those earlier events.

Actual ordinary fixture logs and authenticated evidence/sidecars are under
fixtures/0001..0153. fresh-actual.json authenticates all153 full input logs;
90 successful directories also retain result JSON/checksum. They are scratch
artifacts for root retention, not source changes. Root owns durable canonical
handoff/acceptance and any later requested patch review.
