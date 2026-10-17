# Comprehensive audit, pass 8 — 2026-10-16

Baseline: `35107a8d1a701093eac876a58ab4efd50e291673`.
Repo/worktree: BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`.
Branch: `fix/safety-audit-20261015`.
Implementation: local uncommitted; acceptance BLOCKED on original termination
attribution. HEAD remains the baseline; no PASS8 commit or push.

Fresh bounded reviews covered discovery/classification/boot exclusion/safety,
engine/process/progress/evidence/methods, wizard/Tk/GTK/console/recovery/boot/build,
and primary persistence/privacy/export/diagnostics/receipt integration. Existing
passing history was a baseline, not acceptance for this pass.

## Reproduced fixes

- The streaming large-log assessment appended the final observed progress
  sample after later Error Summary rows. An otherwise parseable unfinished
  final table then became malformed: explicit I/O failure warnings became
  unavailable; a clean zero-count advisory could also become unavailable.
  Completion still failed closed. The scanner now preserves the sample's
  original position relative to retained records and does not duplicate a
  sample already retained. It still retains bounded data, validates log identity,
  refuses overlong/unterminated records, and binds assessment to the target and
  method. Ten new cases yield five original failures/five passing controls.
  [Original proof](runner-order-original.log), [fixed cases](runner-order-fixed.log),
  [independent review](discovery-projection-review.md).
- Diagnostic validation let oversized positive/negative elapsed integers raise
  `OverflowError`, instead of the documented malformed-report `SafetyError`.
  A JSON decoder `RecursionError` likewise escaped that boundary. The existing
  refusal catch now covers both. No schema, allowed field, identity, privacy
  policy or erase outcome was loosened. Ten new cases yield three original
  failures/seven passing controls. Two failures use actual encoded oversized
  integers; the recursion failure is explicitly injected at the JSON decoder.
  Bounded raw deep-JSON cases are passing malformed-data controls on this
  CPython3.12 runtime, not a claim of naturally reproduced parser exhaustion.
  [Original proof](diagnostic-before.txt), [fixed adjacent cases](diagnostic-fixed.txt),
  [independent review](ui-review.txt).

The **20 final new cases** produce **eight intended failures /12 passing
controls**, zero setup errors, on an isolated exact baseline source tree; all
**20 pass** on the fixed source. The working tree was never reverted.
[Exact-baseline proof](original.txt), [reproduction script](original-proof.py),
[fixed regressions](fixed.txt), [four frozen source/test hashes](source-sha256.txt).
No existing test was changed or weakened.

## Fresh independent coverage

These counts overlap the full suite; do not add them as unique passes.

- Discovery/safety: **542** adjacent tests, no skips
  ([log](discovery-suite.txt), [review](discovery-review.md)).
  **756** malformed/mounted/transport/duplicate/retry/concurrent/identity cases
  ([script](discovery-matrix.py), [result](discovery-matrix.txt)); **5,000**
  seeded token inventories and **102** argv controls/mutations
  ([script](discovery-token-argv.py), [result](discovery-token-argv.txt));
  **900** authorization combinations: six normal controls/894 refusals
  ([script](discovery-auth.py), [result](discovery-auth.txt)). All production
  inventory/process/mount/cmdline boundaries were guarded or substituted.
- Engine/evidence: **650** final adjacent tests, no skips
  ([log](runner-fixed-adjacent.log), [review](runner-review.txt)).
  **45,000** exact method/exit completion comparisons and **5,000** advisory
  payload comparisons across seeded logs pass after the fix
  ([script](runner-projection.py), [result](runner-projection-fixed.log)).
  Only no-matched-record provenance is normalized: projection legitimately
  drops irrelevant lines and may become empty. The final matrix permits no
  malformed-summary semantic differences.
- Runner fix independently: **259** adjacent tests, **600** table/progress/
  counter/order combinations, six evidence-cap boundaries and four malformed
  record refusals pass. All three method verdicts match full text. The reviewer
  independently reproduced five failures/five controls on exact original code.
  [Review](discovery-projection-review.md), [matrix](discovery-projection-review.py),
  [result](discovery-projection-review.txt), [suite](discovery-projection-suite.txt).
- Diagnostic fix independently: **140** adjacent tests
  ([log](ui-diagnostic-review.txt)) plus a baseline/fixed boundary comparison
  ([script](ui-diagnostic-boundary-matrix.py), [result](ui-diagnostic-boundary-matrix.txt));
  a second reviewer passed **109** adjacent tests
  ([log](runner-diagnostic-review.log)) and **64** four-entrypoint cases:
  44 malformed refusals/20 valid controls through validation, verification,
  bundling and request decoding
  ([script](runner-diagnostic-matrix.py), [result](runner-diagnostic-matrix.log)).
- UI/state/recovery: **654** tests plus **751** adjacent async/stop/shutdown/
  keyboard/sound/report tests, no skips ([UI](ui-tests.txt), [adjacent](ui-adjacent.txt),
  [review](ui-review.txt)). Fresh **64,000** navigation events, **54** nested
  overlays/language/method cases and **40** concurrent refresh/retry sessions
  ([script](ui-state-matrix.py), [result](ui-state-matrix.txt)); **240** fully
  stubbed kiosk exit/engine/power-token combinations
  ([script](ui-kiosk-matrix.py), [result](ui-kiosk-matrix.txt)).
- Boot/build fixtures: **316 passed /two expected generated-lb-config skips**
  ([log](ui-build.txt)). This is source-fixture coverage, not image acceptance.
  Actual `./preview` was launched at 72 DPI and visually inspected by reviewer
  and primary; [screenshot](ui-preview.png), [owned-process teardown](ui-preview.txt).
- Primary: **431** baseline adjacent tests ([log](primary-baseline.txt));
  **476** diagnostic JSON-leaf mutations: seven valid/469 safe refusals,
  no unhandled exceptions ([script](diagnostic-matrix.py), [result](diagnostic-matrix.txt)).
  **96** regular-file preference observations cover corruption, unsafe modes,
  replacement during read, failed write/sync followed by retry, and 80 concurrent
  atomic writes ([script](intent-matrix.py), [result](intent-matrix.txt)).

## Final local acceptance

Final frozen-source local gate passed:

- [Main pytest](final-tests.txt): **6,222 passed /14 expected image-only skips**,
  no failures/errors, in 495.62s; mandatory GTK result guard passed.
- Separate private Orca: **1 passed**, giving **6,223 unique passes**. The
  [JUnit-derived summary](final-summary.json) confirms no duplicate IDs and
  lists every skip: two generated lb-config and twelve manufacturing-ISO cases.
- [Lint/types/security/shell/developer formatting](lint.txt), [preview](preview.txt)
  and [private negative safety mutation](negative.txt) passed.
- Pinned [Go1.26.8](go-version.txt) [uncached race](go-race.txt), [vet](go-vet.txt)
  and [350,000 fuzz executions](go-fuzz.txt) passed. Native inventory stayed unset.
- All [four frozen source/test hashes](source-sha256.txt) match tested bytes.
  Runtime source digest: `be7d8d674e102743e61984ca60ba63c912c4b514d52dd755f243049f88562d5c`.

The unchanged TODO-regex warning in release_manifest.py:40 and mypy untyped-body
notes are informational; no material lint/type warning remains. The local
ci-hosted.sh tests invocation used BEAMO_GATE_CHILD=1, pinned Go and the no-space
Python-venv alias on PATH, GOTOOLCHAIN=local, and explicit scratch JUnit paths.
Suite/Orca ran in private XDG/D-Bus/Xvfb sessions at72DPI. No dependency upgrade,
hosted execution or source/test change after final freeze was involved.

Focused termination investigation passed all16 neighboring cases,40 actual
repetitions and the full311-case Tk runtime module under child-process/signal
tracing. No signal-send syscall or delivered SIGTERM was observed; owned pytest
processes exited normally. [Summary](ui-termination-summary.json),
[owned teardown](ui-termination-ownership-final.json). A first repetition attempt
was pytest-deduplicated to one case and is not counted as40 repetitions.
The replacement full wrapper also [exited normally](final2-wrapper-signals.txt).
On2026-10-16 the owner answered **"No, not knowingly"** to stopping/canceling
the06:29UTC command. No platform execution-audit tool is exposed; the checked
local audit-log/kernel-audit/cgroup memory-event files are absent
([availability](attribution-availability.json)). This does not establish a cause.
The exact next action is to obtain original termination attribution from platform
execution audit evidence,
then reconcile acceptance before a safety-prefixed commit and push. No further
blind retry is required. All implementation/test bytes remain local uncommitted.

## Harness history and limits

All unsuccessful setup assumptions are retained, not counted as product bugs
or passing runs. One initial diagnostic object fixture exceeded16KiB; corrected
before final original proof. Initial raw-depth recursion assumptions did not
hold on CPython3.12; corrected tests and matrices explicitly inject that decoder
failure. Python3.11 was unavailable. A UI harness initially passed an unsupported
constructor argument; a runner diagnostic matrix used the wrong output filename.
A discovery wrapper initially blocked fake predecessor mount reads and lacked
DISPLAY; its complete fake-boundary private72DPI replacement passed. A first
baseline-import attempt loaded current code due pytest path precedence; the
reviewer corrected import binding and reproduced original failures. Initial
projection comparisons exposed a legitimate no-record provenance difference;
only that distinction is normalized. Earlier conservative classifications and
implementation-detail assertions were superseded before the final original
proof and strict corrected matrix. Reviewer records link exact setup traces.

No actual nwipe, native disk inventory, disk/USB action, host power/firmware
change, guest, hosted CI, PR, merge or release occurred. Only fake boundaries,
harmless owned children and regular temporary files were used. ISO/QEMU, native
Windows and physical media/firmware/reconnect acceptance remain separate and
unrun. No pinned version, claims, method, token, countdown, boot exclusion,
nwipe argv or shipped surface boundary was relaxed. The canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md) tracks current
state and separate qualification. This audit does not prove the absence of bugs.

## Artifact integrity

Readable text transcripts have trailing whitespace and surplus blank EOF lines
normalized. Exact bytes of affected files are retained in the deterministic
`original-transcripts.tar.gz`; `original-transcripts-sha256.txt` verifies them.
`artifact-sha256.txt` covers all retained artifacts except its own manifest.
No source/test byte was normalized or changed by evidence preparation.
