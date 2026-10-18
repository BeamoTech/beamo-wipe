# Beamo Wipe comprehensive bug audit, pass19

2026-10-17 / Codex. **BLOCKED: the canonical final Python phase aborts.**
No commit, push, hosted job, ISO build, native Windows acceptance or release.
All runtime uses fake devices, regular temporary files and private X11/DBus.
No physical media, firmware, host power or guest configuration was changed.

Repository BeamoTech/beamo-wipe, branch `fix/safety-audit-20261015`, worktree
`/root/dev/Beamo Wipe`, HEAD `35107a8d1a701093eac876a58ab4efd50e291673` plus
preserved uncommitted audit work. Starting766 inputs exactly match pass18 final;
final771 inputs retain762 unchanged starting inputs, change4 existing inputs
and add5 regression modules/214 cases. Runtime source SHA256:
`a69d8d2d8199b71a28f5f5280bad6d4bb13f46211d0f5e68a6f1d13d99c9460b`.
The source freeze, exact incremental patch, cumulative patches and42 untracked
audit modules are authenticated in `primary/`. The index remains empty.

## Proved and fixed locally

- Discovery preserves filesystem ancestry through bcache reported as a disk,
  descendants of blank holders, repeated holders and contradictory transitive
  parent records. Unresolved filesystem evidence refuses discovery; blank
  unmounted mapping controls remain. Mounted failures retain their established
  error category. Boot exclusion and launch authorization stay fail-closed.
- TkWizard records and retires its two exact confirmation/typing variable
  trace tokens before teardown. Independent observers and live input remain.
- Two fixture corrections release/settle the private audio worker after any
  first-click failure and remove only the independent checkbox peer trace after
  assertions. All301 original accessible assertions and24 original checkbox
  assertions remain; one worker-settlement assertion was added. Both60ms
  limits are unchanged. These fixes do not explain the prior74.932779ms click.

The final214 canonical cases plus8 fixture probes replayed privately on exact
starting source produce118 AssertionError failures/104 passing controls, no
errors, skips or deselections. The shared checkout was never restored.
Independent exact9-input review is in `ui-boot/final-cross-review.{json,md}`.

## Verification and failed gates

| Check | Actual result |
| --- | --- |
| Fresh baseline | 3522 passes, no skips |
| Corrected focused and adjacent cases | 329 passes, no errors/skips/failures |
| Source/archive/diff readback | PASS, all766 starting and771 final inputs |
| Lint/types, preview and negative boot guard | PASS on exact final source |
| Go1.26.8 race/vet/350000 fuzz, Windows AMD64 crossbuild | PASS; binary is not native acceptance |
| First full instrumented Python/Orca phase | FAILED: main abort/no JUnit; Orca1 pass |
| Canonical phase without extra observer/plugin setting | FAILED: main abort/no JUnit; Orca1 pass |
| Two shortened diagnostic prefixes | Each1061 actual JUnit passes,8711 later cases deliberately deselected |
| Full collection, first-failure diagnostic | 477 passes/1 failure; stopped by maxfail1 with actual traceback |
| Font provenance diagnostic | Deliberately canceled by root, exit143; no final JUnit or acceptance |
| Isolated supported Tk session lifetime proof | 2 assertion failures/6 controls; owned font IDs and wrong-thread finalization confirmed |
| New runner/cancellation/geometry/report campaigns | NOT RUN, held behind failed canonical phase |
| ISO/QEMU/native Windows/firmware/physical/hardware | NOT RUN/BLOCKED under current environment constraints |

The full-collection first failure is
`tests/test_audio_launch_ownership_pass14.py::test_start_error_after_spawn_never_leaves_a_competing_worker[False-False-True]`.
Its next-job wait fails and cleanup cannot join the worker. The immediate
thread snapshot locates that worker in `tkinter.font.Font.__del__`, called
during Event.wait's allocation path. This is concrete off-thread font
finalization evidence. The separate isolated proof confirms wizard-owned font IDs entering their finalizer
on a later worker after both supported normal and exception routes. The font
in the original full run is not identified; the exact native abort cause
remains unestablished. Both fatal traces report GC on that audio path.

The font provenance observer logs only scalar identity/thread/creation-stack
data and invokes original Font methods unchanged. It changes allocation and
GC timing; a passing instrumented diagnostic cannot replace the failed plain
canonical phase. No speculative GC suppression, threshold change, timing-limit
relaxation, broad trace sweep or native font neutralization was applied.

## Diagnostic corrections and history

`primary/diagnostic-history.md` separates rejected fixture hypotheses, proved
harness defects and unresolved incidents. Initial bcache fixture construction
errors are not product proof. An external absolute-path probe had global
autouse scope under full collection; identical repository-relative bytes have
module scope. Both the failed expanded run and corrected proof remain.

Global PYTEST_PLUGINS broke private child pytest import/report generation;
the controlled with/without comparison proves that harness defect. The plain
canonical run still aborted, so that defect cannot explain every failure.
Both full failed runs are preserved separately as `primary/failed-gate-1/`
and `primary/failed-gate-2/` (bulky raw bytes may be compacted as described below).
The first failure receipt's raw F-character field is explicitly not a case
failure count. Prefix1062 selection included the separately excluded Orca
case; actual JUnit passes are1061, as corrected in its count clarification.

Pass18's GTK latency, pass16's native loop-probe incident, pass8's unexplained
SIGTERM attribution and pass9's unavailable original timing trace remain
separate unresolved historical items in the canonical unfinished record.

## Remaining acceptance

The supported-lifecycle case now proves wizard-owned asset finalization on a
later worker. Correct its ownership boundary across both normal and exception
routes; the original full-run font identity and native abort attribution remain
open. Preserve
normal, exception, repeated teardown, peer-observer and worker-lifetime paths.
Then refresh exact-source review, rerun affected tests and all applicable local
gates, authenticate both main/Orca reports and required skips, and only then
run/read back the prepared fake artifact campaigns. No later passing test is
an explanation for an earlier failure. Do not commit/push while acceptance is
blocked; an eventual disk-selection change requires a `safety:` commit.

The canonical task record is
[`unfinished-work.md`](../../../.ai/memory/unfinished-work.md).
`primary/raw-evidence.tar.gz` and its SHA256 index retain bulky JUnit/log/
JSONL/crossbuild bytes at original relative names; working staging is preserved.
`SHA256SUMS` authenticates all final retained evidence files.


Root deliberately ended only the extra allocation-changing Font observer:
SIGINT was ignored, then an exact PID/start/ancestry-validated SIGTERM at
16:57:22.335849 UTC yielded exit143. Its raw partial log and explicit signal
receipt remain; no final pass or failure counts are inferred. Neither of the
previous full Python phases was canceled. The eight-case lifetime proof ran
serially afterward and all its child outcomes are authenticated in
`primary/native-asset-original-review.json`.
