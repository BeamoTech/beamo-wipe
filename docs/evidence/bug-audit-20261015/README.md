# Fake-device bug audit — 2026-10-15

Source baseline: `cad8ed397818bca09634be57cd8a46e0195690c2` (`main`).
Working branch: `fix/safety-audit-20261015`. These are local source checks,
not shipped-image qualification or release evidence.
Implementation commit: `ff0a3da08e56c3fb38941be20e42db9553269f32`, pushed to origin.

The owner instructed the audit to continue despite the unavailable shared
`/root/dev/AGENTS.md`; current project instructions remain authoritative.
Three bounded reviews covered discovery/safety/methods, engine/progress/evidence,
and boot/build/recovery/report export. The primary agent reviewed wizard state,
stop/retry/shutdown transitions, independently reproduced the defects, reviewed
the complete source changes, and ran the final gates.

## Verified defects and fixes

- SIGUSR1's job-wide percentage was described as a percentage within the
  current step. That secondary line could also show 100% before validated
  completion. Label it as overall progress in English, French and German and
  apply the existing pre-completion display clamp. The pinned engine's
  [signal handler](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c#L1350)
  logs `round_percent`. Completion decisions, engine flags and method plans
  are unchanged.
- The headline's displayed percentage was throttled and monotonic while the
  step line used a raw observation. A real-runner fake-log trace displayed
  40% beside 45% (throttle), or 40% beside 35% (regression). Both lines now
  share the displayed job percentage when available.
- Recovery and runner lock acquisition could accept a lock inode whose named
  path had been replaced. Recovery could also reuse obsolete quiescence or
  write a journal after losing named interface ownership. Verify the named
  inode after flock and before recovery reuse/writes; fail closed on changes.
- An interrupt during runner lock acquisition could leak an unpublished lock
  descriptor. Close it on `BaseException` as well as normal exceptions, then
  propagate the interruption.
- An unterminated final engine record could falsely pass hidden-capacity or
  I/O report checks. Incomplete logs cannot produce passing parsed checks;
  explicit warnings and failures remain visible.

The four new regression modules produce **14 failures and four passing normal
controls** against a private original-source copy, and **18 passes** against
the fixed source. [Original reproduction](original-reproduction.txt) and
[fixed regressions](fixed-regressions.txt) preserve both outcomes. Original
source was read from Git into a temporary import tree; the checkout was never
reverted or mutated for this reproduction.

## Verification

All applicable local gates passed. [Final summary](final-summary.txt):

- [Full pytest](final-tests.txt): 5,694 passed, 36 explicitly skipped; exit 0,
  including the mandatory mixed-module GTK result guard.
- Separate clean-session Orca: one passed.
- [Launcher supplement](launcher-tests.txt): 23 passed, resolving 22 skips
  from the full run; one bootstrap test overlaps the full suite.
- Combined: **5,717 unique passed / 14 image-dependent skipped**, no failures.
  The remaining skips are two generated live-build-config checks and 12
  manufacturing-ISO checks; no image qualification is claimed.
- Go 1.26.8 [race tests](go-test.txt) and vet passed; native inventory override
  remained unset. These are Linux/fake-firmware checks, not Windows acceptance.

Source/test identity is recorded in [source-sha256.txt](source-sha256.txt),
including the new regression modules. Hashes were checked after verification
and match the pushed implementation commit.
Transcript trailing whitespace is normalized for Git; test outcomes are retained.

Already completed:

- 294 wizard confirmation/refresh/stop/retry/shutdown tests passed.
- 439 discovery/safety tests passed; no new defect proved in that bounded review.
- 177 independent changed/adjacent tests passed on the final source; the affected
  runner/security selection also passed 66 tests.
- Independent progress review: 135 tests plus 36 language, staleness and boundary
  cases passed. Two actual-runner fake-log regressions proved and now cover
  throttled and regressing percentage consistency.
- Local [lint/types](lint.txt), [preview](preview.txt), and
  [safety mutation](negative.txt) phases passed using the existing gate script
  with `BEAMO_GATE_CHILD=1` (dependency installation omitted, no hosted dispatch).
  Lint's TODO warning is an existing false positive on the placeholder-detection
  regex in unchanged `release_manifest.py:40`; mypy's untyped-body messages are
  informational. No source lint or type errors were reported.

Test environment: Linux x86_64, Python 3.12.3, repository-pinned pytest 9.0.3
and Playwright 1.63.0/Chromium, pinned Go 1.26.8 and QR decoder installed; `.venv-linux` exposes
installed system GTK. A temporary `/tmp/beamo-wipe-audit-python` path alias avoids spaces
in generated fixture shebangs. PATH includes that environment so subprocesses
find pytest. Initial setup failures are not source regressions or gate passes.

A combined direct pytest run encountered a stale accessibility-bus socket
after speech testing. Its isolated AT-SPI case passed. The final run uses
the repository's existing separate speech/suite Xvfb and D-Bus runtime
directories through `scripts/ci-hosted.sh tests`, at 1600×1000 and 72 DPI.
Interrupted exploratory runs are not accepted as passing gates.

The first complete run used pytest 9.1.1 and returned 5,668 passed, 58 skipped
and two failures in missing-GTK simulation tests. Its `importorskip` uses
`importlib.import_module`, bypassing the simulation's builtin-import hook when
system GTK is installed. With the repository-pinned pytest 9.0.3, all 15
dependency-boundary tests pass without source changes. Browser/GTK dependency
preflight passed 33 tests. The final full run uses those declared dependencies;
the earlier failed run is not a passing gate.

## Limits and publication state

All exercised disks/firmware were fake and all lock fixtures were ordinary
temporary files. No host device was modified, no guest started, and no ISO
was built. ISO/QEMU, native Windows, physical firmware/media compatibility and
physical reconnect/readback are **NOT TESTED** for this source. T3 preview
navigation/snapshot automation failed repeatedly; no successful interactive
T3 browser inspection is claimed. Repository browser regression tests,
generated web/console/helper and embedded-JS checks passed independently.

No hosted CI, PR, deployment or release was performed. Source fixes were
committed and pushed only after the local gates passed. Workflow inspection
and GitHub queries confirmed no open PR or branch CI run; a branch without a
PR avoids automatic qualification. See the canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md).
