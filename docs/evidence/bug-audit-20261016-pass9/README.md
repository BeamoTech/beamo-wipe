# Comprehensive source audit, pass 9 — 2026-10-16

Repository: BeamoTech/beamo-wipe, branch `fix/safety-audit-20261015`, worktree
`/root/dev/Beamo Wipe`, HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
Started with the two pass8 fixes and their tests/evidence local and uncommitted.
No new source defect has been confirmed so far. Existing work is preserved.

Three bounded reviewers inspected discovery/safety, runner/recovery, and
UI/boot/build; the primary inspected diagnostics, report/export/privacy and
verification integration. All execution uses fake inventories, processes,
firmware or regular temporary files. No actual erase/device/USB/guest operation,
hosted CI, PR, merge or release is part of this audit.

Result: **no new proven source defect; all final applicable local gates pass**.
Acceptance/commit/push remain **BLOCKED** by unexplained execution results:
the historical pass8 SIGTERM and the two auxiliary GTK timing misses below.
Neither successful replacements nor source inspection establish their causes.
No source or test was changed by pass9. The existing pass8 changes are preserved.

The final source/test bytes are recorded in [source-freeze.json](source-freeze.json).
Historical pass8 SIGTERM attribution remains separately tracked; this pass
makes no inference about its sender or cause.

## Fresh bounded evidence

Counts below overlap the full gate and must not be added as unique tests.

- Discovery/safety: 589 unique focused/adjacent tests plus 195 independently
  generated fake mutation/token cases passed. Early GTK initialization failures
  on missing/default displays were retained; a private 72-DPI Xvfb replacement
  passed all 13 affected operation-identity cases. No new finding or source edit.
- Runner/recovery: 384 test executions passed. 41,370 generated short-log
  comparisons matched completion tuples for every method and complete engine
  advisory payloads, including provenance. Independent original-source pass8
  reproduction: five failures/five controls; current projection fix approved.
- Diagnostics: independent 104 tests passed, including all ten pass8 cases.
  Original-source reproduction: three failures/seven controls. Oversized integer
  overflow is naturally reproduced; parser recursion is explicitly injected.
  Natural deep JSON is retained as a safe-refusal control, not claimed as a
  naturally reproduced decoder failure on this interpreter.
- Primary: 334 diagnostic/report/receipt adjacent tests passed. Expanded
  export/evidence/manifest suite: 1,102 passed/12 manufacturing-image skips.
  Malformed single-field report mutations across eleven outcomes and three
  languages made 202,752 API calls with no exception. This measures exception
  robustness of result interpretation, sharing-copy creation, encoded text and
  HTML rendering. It does not assert all semantic privacy/escaping properties,
  encode the sharing copy, or exercise filesystem exports; separate tests cover
  those boundaries. Four API calls are counted per mutated fixture.
- UI/boot/build: 215 focused tests passed. Actual fake Tk preview was captured
  at 72 DPI through selection, token, method, countdown, working, stop consent
  and interrupted result. Reviewer and primary inspected screenshots. The
  explicit disabled Erase action and fake-only banner are visible.

## Failed runs retained

A broad toolkit run without private runtime failed external AT-SPI discovery
with a missing shared bus socket and a sound-dialog click timing assertion
(76.45ms against a60ms limit). The corrected private-runtime run passed external
AT-SPI but still missed that timing limit at137.61ms:623passed/1failed/7skipped.
These are not passing gates. The source executes sound discovery on its worker
thread; constructor/submit inspection found no discovery wait/join. Concurrent
review suites and Go compilation were active, but timing traces alone do not
prove scheduling as the cause. The separate full gate has passed that exact
case; an isolated focused check remains pending after it retires. Test limits
and source have not been altered. Exact initial/private traces are retained.


## Final verification and state

The complete local `ci-hosted.sh tests` phase exited0: **6,222 passed /14
expected image-only skips**,713.76s. Separate private Orca: **1 passed**,118.16s.
[JUnit summary](final-summary.json) confirms **6,223 unique passes**, no
failures/errors/duplicate IDs, and lists all14skips: two generated live-build
configuration cases and twelve manufacturing-ISO cases. The mandatory GTK
result guard passed. Those image checks remain unrun, not passing.

The exact GTK sound timing case passed once in that full gate. After all main
and auxiliary jobs retired, the isolated private72DPI sound adjacency group
passed **5cases** in0.70s, including slow discovery and closed-dialog behavior.
[Isolated log](ui/sound-isolated.txt), [JUnit](ui/sound-isolated.xml),
[review](ui/README.md). These passes do not attribute the earlier76.45ms/
137.61ms constructor-click timings; no test threshold was raised. No new
product defect was proved. The shared-bus setup error was resolved in private
runtime; all seven isolated-X11 skips in that auxiliary run execute in the
full gate.

Fresh [lint](lint-baseline.txt), [preview](preview.txt) and
[negative safety mutation](negative.txt) phases exited0. Ruff/mypy/security/
shell/developer-format checks pass. The literal TODO detection-regex warning
and mypy untyped-body notes are existing informational output. The negative
phase intentionally sees the private unsafe mutant fail, then verifies the
unaltered source passes; that expected mutant failure is not a gate failure.
Pinned Go1.26.8 [race](go-race.txt), [vet](go-vet.txt) and
[350,000fuzz executions](go-fuzz.txt) passed; native inventory override remained
unset. These local fake-firmware checks are not native Windows qualification.

Final diff and both existing regression modules were reread. All558frozen
application/test hashes and the four pass8 hashes still match. Runtime source
SHA-256:`be7d8d674e102743e61984ca60ba63c912c4b514d52dd755f243049f88562d5c`.
Only audit documentation/evidence was added in pass9. HEAD remains35107a8;
index empty; existing fixes/tests remain **LOCAL UNCOMMITTED**. No push, PR,
merge, hosted run, deployment or release occurred. Physical media/firmware,
ISO/QEMU and native Windows remain separate NOT TESTED acceptance boundaries.

Remaining next actions are recorded in the canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md): obtain
original termination audit evidence; explain the auxiliary timing variation
with measured constructor/GTK/wall/thread-CPU traces if further investigation
is undertaken. Do not infer CPU causality merely from concurrent jobs, modify
performance assertions, or commit/push while acceptance remains blocked. No
blind full-suite retry is needed. No test or process remains running.

## Artifact integrity

Readable copied transcripts strip trailing whitespace and surplus blank EOF
lines. Exact original bytes are retained in `original-transcripts.tar.gz`,
with `original-transcripts-sha256.txt`. `artifact-sha256.txt` covers all retained
artifacts except itself. This formatting changes no application/test bytes.
This bounded audit does not prove the absence of bugs.
