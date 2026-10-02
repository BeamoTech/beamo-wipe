# WSL local-suite follow-up — 2026-10-02

Base: `b73ea196f3223ba0a07e8c9182000f2c7da6eab5`.
Branch: `codex/local-wsl-test-followup`. The commit containing this receipt
identifies the final change (`git log -1 --format=%H --
docs/evidence/local-wsl-test-followup-20261002.md`).
[Machine-readable results](local-wsl-test-followup-20261002.json) bind the seven
tested files to SHA-256 identities. Their bytes matched the final worktree;
only this dated receipt and its JSON were added after test execution.

## Findings and corrections

Fresh revalidation of the merged [GTK dependency correction](gtk-dependency-123.md)
and [negative-gate cleanup](negative-gate-cleanup-124.md) found two additional
full-suite failures: 5,603 passed, 57 skipped, two failed on the base revision.
The original traces are retained in the operator audit.

- Orca's private Xvfb startup waited for a filesystem socket. WSL's
  `/tmp/.X11-unix` is a read-only tmpfs mount here, while a real X11 client can
  connect through Xvfb's abstract socket. The test helper now probes
  `xdpyinfo -display <private-display>` and checks that its owned server is
  still running. Each probe has a one-second timeout within a five-second
  readiness deadline per candidate. Existing occupied displays are skipped.
  Failed/interrupted startup terminates and reaps only its owned child, with
  bounded five-second TERM and five-second KILL waits. Cleanup errors remain
  visible, and an existing exception is preserved. No parent display or mount
  is changed. `x11-utils` is declared in both hosted and local setup.
- Python 3.12's JSON decoder accepts this fixture's 1,500 nested arrays; export
  then rejects their unsupported schema. The test previously required a
  malformed-decoder error. It now permits exactly those two rejection
  messages and still requires indeterminate recovery. A separate controlled
  `RecursionError` test requires indeterminate recovery and export's malformed
  error response. Production parsing, schema and safety code
  remain unchanged.

## Observed verification

Environment: WSL2 x86_64, Ubuntu 24.04, Python 3.12.3, pytest 9.0.3,
PyGObject 3.48.2, GTK 3.24.41, ATK 2.52.0 and Orca 46.1. WSL Windows-drive
automount and interop remained disabled. All test devices were fake.

| Check | Result |
| --- | --- |
| New lifecycle/JSON regressions plus real parent-path Orca and wiring check | 24 passed, zero skips, 89.05 s |
| New lifecycle/JSON regressions in the separate venv without `gi` | 22 passed, zero skips |
| Prescribed complete `scripts/test-all.sh` under private D-Bus/Xvfb at 72 DPI | 5,623 passed, 57 skipped, zero failures/errors, 831.44 s |
| Required GTK regressions from #123, real Orca and all 19 #124 cleanup/private-gate cases | Executed and passed in that full report |
| Ruff, blocking mypy, ShellCheck, whitespace checks | Passed |
| Canonical CI/development local links and heading fragments | 17 validated before this receipt; receipt links also checked |

The full command was `BEAMO_WIPE_DRY_RUN=1 dbus-run-session -- xvfb-run -a
-s '-screen 0 1600x1000x24 -dpi 72' ./scripts/test-all.sh -rs
--junitxml=<audit>/results/full.xml`, using the GTK venv on PATH and private
runtime directories. The runner used a 1,800-second outer deadline and
bounded cleanup of its owned process group; no cleanup errors were reported.

The 57 skips were 37 missing Playwright, five missing Chrome, 12 missing
manufacturing ISO, two missing generated live-build configuration and one
legacy-gcloud-CLI case. These local exclusions do not substitute for hosted
Linux/image/browser/native-Windows qualification. No new hosted run, image
build, release signing or publication occurred in this preparation.

Raw commands, logs, JUnit, original traces, source comparisons and inspection
errors are retained under the operator's local
`BeamoWipe/local-verification-followup/20261002T162334Z-wsl-json-media/` audit.
The original dated receipts and published release assets were left intact.

## Remaining qualification and physical work

The existing main [run 36880357290](https://github.com/BeamoTech/beamo-wipe/actions/runs/36880357290)
passed on the base revision. The earlier documentation-merge
[run 36647113738](https://github.com/BeamoTech/beamo-wipe/actions/runs/36647113738)
finished with failure on `498e1847e60cd80ab1a2c6c448e4e8dbe2254354`.
Neither run qualifies this new change. PR creation starts hosted execution;
follow [CI policy](../ci.md#execution) for authorization and require a passing
exact-commit `CI gate` before merge.

Physical #119 remains **NOT TESTED**. The operator confirmed physical access
is unavailable; the test USB currently reports **No Media**, and the fresh
Secure Boot query is **INSPECTION FAILED** (access denied). The earlier Imager
write/verification report is not the required reconnect/readback. No reboot,
firmware change or erase was attempted. Qualified readback, dedicated hardware
with valuable disks disconnected, an established way to control/capture boot,
and complete enforcement/trust/revocation/SBAT evidence remain prerequisites
under the [physical acceptance procedure](../secure-boot-acceptance.md).
