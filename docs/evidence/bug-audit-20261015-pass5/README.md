# Additional comprehensive bug audit — 2026-10-15

Baseline: `604e72b3ae1fe1a2abdda08200b8f271cb5c675d`.
Branch: `fix/safety-audit-20261015`.
Implementation: `cdfe9fac6238c8fd3d867c9ef48c4ca3248facce`, committed and pushed after all applicable
local gates passed. Source and evidence are unmerged and unreleased.

Three bounded reviewers revisited discovery/authorization, runner/evidence,
and wizard/UI/boot/build boundaries. The primary independently reviewed all
changes and original failures and inspected persistence, diagnostics and report
export integration. Only fake inventory/processes and ordinary temporary files
were used. No connected disk, firmware or host session was changed.

## Verified fixes

| Problem | Result | New cases |
| --- | --- | ---: |
| Falsy malformed `children` metadata was treated as an empty list. | Reject malformed disk/nested/flat topology; preserve absent/null/list/tuple defaults. | 24 |
| Truncating a findmnt bracket suffix could invent boot identity or discard a real full-path alias. | Preserve actual aliases/existing full paths, reject incomplete/empty annotations, propagate lookup errors into fail-closed discovery. | 18 |
| Model continuation text could forge passing hidden-storage or zero-error checks. | Positive advisory checks require genuine pinned-engine record/header structure; conservative error/warning handling remains. | 7 |
| Startup text retained import-time English after a language change, and GTK announced hardcoded English status. | Resolve current language at snapshot time and translate spoken working status without changing stage state. | 6 |
| Export cleanup I/O errors skipped remaining owned directories/descriptors. | Attempt remaining cleanup through `finally`, including worker parent close after volume close failure; never retry a failed close. | 4 |

The 59 new cases produce **38 intended failures and 21 passing controls**
against an exact private baseline source tree, and **59 passes** on the fixed
source. [Original reproduction](original-reproduction.txt),
[fixed regressions](fixed-regressions.txt). No checkout revert was used.
Ten existing synthetic fixture modules were updated to genuine positive-log
formats; all existing assertions remain, including malformed-number/conflict
and whole-log projection checks. The primary compared every existing `assert`
AST against the baseline across all ten modules; all were identical. Genuine
v0.42 fixtures still pass.

The first discovery draft did not cover an existing source whose `realpath`
was unchanged; two further original/draft failures prompted an explicit
`lstat` existence check that catches only `FileNotFoundError`. The first
cleanup draft covered mount-state resources; a separate worker-close failing
regression exposed the same adjacent omission and drove the final correction.
Two early full-test runs were deliberately interrupted on their exact owned
pytest PIDs for these final fixes. Their missing-JUnit failures are superseded,
not passing evidence. A later complete integration run found three fixture
failures (5,944 passes, 14 image-only skips): an older positive collision
control still used a shortened banner, and both GTK localization tests
inspected an unrelated surviving window. The positive/foreign fixture headers
now use the genuine banner with all assertions retained; GTK tests identify
only their own new window and deliberately preserve an unrelated window.
[Failed integration run](failed-integration-gate.txt),
[60 ordered UI cases](startup-window-isolation-fixed.txt), and
[12 parser cases](collision-fixture-fixed.txt) document correction. Product
source did not change for these fixture corrections. Only the replacement
final frozen-source gate below is the passing result.

## Independent and adjacent checks

These selections overlap the final suite and must not be summed as unique
passes:

- Discovery/boot/authorization/methods: reviewer reported 394 unique passes,
  zero skips; all 42 discovery regressions included once. Parent reproof and
  final complete gate independently verify the source.
- Runner/process/progress/cancellation/retry/log/evidence/recovery:
  [499 passes](runner-focused.txt) and a refreshed
  [1,176-case completion matrix](completion-matrix.txt). The matrix uses the
  [existing retained harness](../bug-audit-20261015-continuous/completion-matrix.py).
  [Reviewer handoff](runner-review-summary.txt) is explicitly a summary,
  rather than a fabricated raw terminal transcript.
- UI/app/keyboard/Tk/GTK/console/boot/kiosk:
  [1,203 passes](ui-focused.txt), initially 31 setup skips. All 31 were executed
  successfully with [pinned Go](ui-go-supplement.txt),
  [isolated X11](ui-x11-supplement.txt), and
  [32 focused startup cases](startup-focused.txt).
- Real GTK labels reproduced [French/German English leakage](startup-label-before.txt)
  before the fix. All six new localization/state tests pass at 72 DPI.
- Primary [380 persistence/report/export/diagnostics tests](persistence-focused.txt)
  passed. Cleanup [original lock failure](cleanup-before.txt),
  [adjacent worker failure](cleanup-worker-before.txt), and
  [independent final approval/check](cleanup-review.txt) are retained.

## Final qualification status

The final frozen-source gate passed on 2026-10-16:

- [Full pytest](final-tests.txt): **5,947 passed / 14 image-only skipped**, zero
  failures/errors, in 503.04s; mandatory GTK result guard passed.
- Separate private Orca: **1 passed**. Combined **5,948 unique passing cases**;
  [JUnit-derived summary](final-summary.json) confirms no duplicate case IDs.
- Skips: two generated live-build-configuration cases and twelve manufacturing-
  ISO cases. Browser, GTK, decoder, Go and required source tests executed.
- [Lint/types/security/shell/developer formatting](lint.txt),
  [preview web/console/helper/JS](preview.txt) and
  [private safety mutation](negative.txt) passed.
- Pinned [Go 1.26.8](go-version.txt) [uncached race](go-race.txt),
  [vet](go-vet.txt) and [350,000 fuzz executions](go-fuzz.txt) passed after the
  final source/test freeze. Native inventory opt-in stayed unset.

The full gate ran locally via `BEAMO_GATE_CHILD=1 ./scripts/ci-hosted.sh tests`,
with pinned Go and the no-space `/tmp/beamo-wipe-audit-python` venv alias on
PATH, `GOTOOLCHAIN=local`, and an explicit scratch JUnit path. Pytest 9.0.3,
Playwright 1.63.0 and the required system GTK/Orca/decoder dependencies were
present. The script isolates suite and speech in private XDG/D-Bus/Xvfb
sessions at 1600×1000 and 72 DPI. No guard or assertion was weakened.
The existing TODO-regex warning in unchanged `release_manifest.py:40` and mypy
untyped-body notes are informational; no material lint/type issue remains.
All [20 frozen source/test files](source-sha256.txt) match the final working
and committed bytes. Runtime source digest:
`017ad382226e57a8b129e14fcb71b5ca7f8dfd094c9d466a1506aeaeae014082`.
No methods, nwipe flags/version, confirmation gates, claims, Go version,
publication controls or shipped surface boundaries were relaxed.

No ISO/QEMU, native Windows, physical media/reconnect/firmware, hosted CI,
PR, production publication or release was performed. Those remain separate
public-candidate qualification, not a local pass. This pass does not claim
absolute absence of defects. The canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md) tracks state
and the separate qualification item.

Fresh bounded reviews and the replacement complete local gate found no further
reproducible actionable defect after the fixes. The canonical local audit item
is complete; this is not a proof of bug-free software or hardware qualification.
All source/test bytes stayed frozen during final gates and match the source
commit. Only evidence/handoff documentation changed after that commit.
Workflow inspection and read-only GitHub checks found no branch PR or hosted
runs; the existing branch push did not invoke PR/main qualification triggers.
The source branch is pushed, unmerged, and unreleased.
