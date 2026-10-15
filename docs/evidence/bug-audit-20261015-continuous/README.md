# Continuous local bug audit — 2026-10-15

Baseline: `20ae39a556ab961baf204e3108e6ebc93b695ac5`.
Branch: `fix/safety-audit-20261015`.
Implementation: `af2b6e9c3d053b65e666d807a87207db14521cb2`, committed and pushed after local gates passed.

The owner requested an active goal: repeat comprehensive audit/fix passes
until a fresh complete pass finds no further reproducible, actionable bugs.
The goal is bounded to authorized local fake-device work; no absolute absence
of defects or unrun hardware qualification is claimed.

Three bounded reviewers rotated discovery/authorization and recovery/reporting
ownership, while the primary revisited wizard/UI/app/boot/build surfaces and
integration. Every suspected defect needed a failing test or concrete trace
before a minimal fix. Independent reviews and fresh follow-up sweeps continued
after the initial findings, exposing and correcting incomplete draft fixes.

## Verified fixes

- Preserve mounted-device exclusion evidence before display filtering. Malformed
  metadata, inconsistent physical/virtual types, hidden rows, and raw/nested/flat
  mount representations must not expose another path to the mounted storage.
  Nonempty malformed mount strings cannot be cleaned into an unmounted state.
- Preserve unrelated zero-capacity readers in historical recovery baselines.
  Target and boot capacity must remain positive; an empty reader gains no erase
  eligibility or recovered authorization.
- Bind diagnostic read/write operations to one validated private directory
  descriptor. Intermediate symlinks or replacement directories cannot redirect
  them outside the approved log directory.
- Refuse successful completion when complete target-bound counter totals
  contradict the launched method. All five known pinned status phases constrain
  denominators; only existing valid terminal phases can establish completion.
  Large-log projection retains distinct counter pairs within its evidence cap.
- Require an exact decimal terminal percentage. Malformed sub/super-100 values
  that float-round to 100 cannot supply a completion marker.
- Reject older concurrent runner telemetry reads after a newer read or start.
  This prevents a stale phase from overwriting a newer observation. Ordinary
  Wizard ticks serialize; the reproduced defect is at the concurrent runner API.
- Keep the collapsed Tk comparison title readable. The control now uses its
  available parent width instead of wrapping “Compare disks” mid-word. No
  selection or checkbox behavior changes.

All device paths and firmware/process boundaries in testing were fixtures.
The pinned nwipe v0.42 binary, methods, flags, confirmation gates, approved
claims, Go version, publication controls and surface boundaries are preserved.

## Proof and verification

The 101 new regression cases produce **67 intended failures / 34 passing
controls** against a private exact-baseline source tree, and **101 passes** on
the fixed source. Original source was loaded from Git without reverting or
mutating the checkout. [Original reproduction](original-reproduction.txt),
[fixed cases](fixed-regressions.txt).

Fresh follow-up sweeps found no further actionable defect in their scopes:

- Discovery/authorization: [132-case malformed graph/alias matrix](discovery-matrix.txt),
  with its [reproduction script](discovery-matrix.py); independent review passed
  216 discovery/recovery cases.
- Runner/evidence/progress: [1,176-case completion matrix](completion-matrix.txt)
  and [script](completion-matrix.py); 595 broader checks passed. The
  [reviewer summary](runner-review-summary.txt) is explicitly a summary, not a
  fabricated raw transcript. An independent reviewer passed 242 runner cases,
  27 cancellation/retry cases and 331 recovery/export cases on the frozen hash.
- Recovery/report/diagnostics/export: a fresh 331-test sweep found no new issue;
  [independent recovery review](recovery-independent-review.txt) passed 88 cases.
- Wizard: [30,000 seeded public actions over 100 fake sessions](wizard-exploration.txt)
  preserved owner/token/countdown/explicit-action and boot-exclusion invariants,
  including ten fake starts. [Harness](wizard-exploration.py). Expected missing
  fake-device rdev notices are informational, not live identity evidence.
- Boot/build/compatibility: [185 source/fixture checks](boot-build-focused.txt)
  passed; all four isolated [Tk startup cases](startup-fullscreen.txt) passed.
- Tk layout: [independent review](ui-independent-review.md) covered 524 unique
  passing cases, including the full runtime, narrow/large-text/keyboard and
  comparison checks. Eleven initial dependency/isolated-X11 skips were executed
  successfully in a supplementary run and are not counted twice.

These selections overlap the final suite and must not be added as unique test
counts. All hardware/firmware inputs and process boundaries were fixtures.
Pinned upstream [method initialization](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/method.c#L1186)
and [status reporting](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c#L1322)
were checked before treating known phase counters as method evidence.

The real Tk `./preview --fullscreen` was navigated at 1600×1000 and 72 DPI.
[Before](tk-picker-before.png) and [after](tk-picker-after.png) show the verified
comparison-title defect and its correction. [Nine original layout failures](comparison-before-tests.txt)
now [pass](comparison-after-tests.txt).

An earlier full run was intentionally interrupted after this actual-screen
check found the title bug. Its missing-JUnit failure is not a source regression
or passing result. The replacement full local gate runs after the final UI fix;
that replacement gate passed. [Final summary](final-summary.txt):

- [Complete pytest](final-tests.txt): **5,888 passed / 14 image-only skipped**,
  no failures, in 524.14 seconds; mandatory GTK result guard passed.
- Private-session Orca: **one passed**. Combined **5,889 unique passes**.
- Remaining skips: two generated live-build-config checks and 12 manufacturing-
  ISO checks. Browser, GTK, QR-decoder and Go-renderer tests executed.
- [Lint/types/security/shell/developer-format](lint.txt),
  [preview web/console/helper/embedded JS](preview.txt), and
  [private safety mutation](negative.txt) passed.
- Pinned Go1.26.8 [uncached race tests](go-race.txt) (`-count=1`),
  [vet](go-vet.txt), and [350,000 parser fuzz executions](go-fuzz.txt) passed.
  Native inventory override stayed unset.

The complete gate used `./scripts/ci-hosted.sh tests` locally with
`BEAMO_GATE_CHILD=1`, pinned Go and `.venv-linux` on PATH through the no-space
`/tmp/beamo-wipe-audit-python` alias, `GOTOOLCHAIN=local`, and an explicit
scratch JUnit path. The script isolates suite and speech in private XDG/D-Bus/
Xvfb sessions at 1600×1000 and 72 DPI. Dependencies match the repository pins,
including pytest9.0.3 and Playwright1.63.0. No test guard was weakened.

[All 12 changed source/test hashes](source-sha256.txt) match the frozen final
inputs. Source/tests stayed unchanged through final verification. Transcript
trailing whitespace is normalized for Git. Lint's existing TODO warning is the
placeholder-detection regex in unchanged `release_manifest.py:40`; mypy
untyped-body messages are informational. No unresolved source lint/type error
or material warning remains.

After the fixes, fresh source reviews, mutation matrices, actual Tk inspection,
independent reviews and the full local gate found no further reproducible,
actionable defect in the authorized local scope. This is the stopping criterion
for the requested goal; it does not prove the program has no remaining bugs.

## Limits

No physical device was changed, no guest started, and no ISO built. ISO/QEMU,
native Windows and physical firmware/media/reconnect acceptance remain unrun
for this source. No hosted CI, PR, production publication or release is authorized here.
These require separate public-candidate qualification. T3 preview status/open
succeeded, but its snapshot client failed with the same automation error as
before; [manual browser inspection was unavailable](browser-inspection.txt).
No successful manual web inspection is claimed and no alternate browser
system was used. Existing repository browser regressions remain separate
checks. The owned preview HTTP server was positively identified and stopped.

Report export remains conservative when optional inventory cannot be identified,
including zero-capacity media; this change restores session journaling, not
export permission for ambiguous devices. Existing large-log crash-recovery
limits remain: supporting completion outside the authenticated retained suffix
can leave recovery indeterminate.

The committed implementation matches all frozen hashes. Only evidence and the
handoff record were edited afterward. Read-only GitHub queries and workflow
inspection confirmed no branch PR or CI run; branch pushes avoid PR/main
qualification triggers. The branch is not merged or released.

The canonical [unfinished-work record](../../../.ai/memory/unfinished-work.md)
tracks the active goal, current source state and separate qualification work.
