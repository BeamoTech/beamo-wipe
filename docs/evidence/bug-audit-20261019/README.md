# Beamo Wipe bug audit — 2026-10-19

Six classes of reproducible product defects and one test-fixture defect are
fixed, with 276 new regression cases.
Final applicable local checks pass: **10,408 unique source/Orca passes,
28 unchanged skips, zero failures/errors**, including all 276 new cases.
Commit/push preparation follows verified evidence retention. No release is authorized.

Baseline: `29bd8059947ecdaf2a1d61726b8f75b1f82cebed` in
`/workspace/beamo-wipe`, branch `fix/safety-audit-20261019`.
[Source hashes](source-sha256.json) identify all 787 frozen runtime, test and
build inputs. Their manifest SHA-256 is
`eed16a687723c95d78550ceb833eafb40bd3bfbfb676a34c0d7983ff4a40be5b`.
Source stayed unchanged during final verification; documentation and evidence
are outside that freeze. Version 0.2.13, nwipe v0.42, Go 1.26.8, approved claims,
method mappings and wipe flags remain unchanged.

## Proven defects and repairs

| Defect | Before-edit proof | Repair and new cases |
| --- | --- | --- |
| Hardware MODEL changes hidden by the label/unknown-model display fallback retain stale target or boot authorization. | Primary independently reproduced six failures with three controls; the expanded 57-case regression has 28 original failures and 29 controls. | Preserve the original nine identity fields and append normalized raw MODEL. Legacy constructed disks retain model identity. 57 cases include actual guarded runner branches with a process spy. |
| Device MODEL newline continuations falsely attribute an owner abort, engine failure or verification mismatch. | Primary's original matrix has 11 failures and 21 controls; expanded matrix has 62 failures and 129 controls. | Trust native timestamps or complete authentic status rows for attribution. Ambiguous negatives remain indeterminate; advisory media checks become unavailable. Genuine failures and conservative possible-write evidence retain precedence. 191 cases cover all methods and large-log projection. |
| Staging and byte-only copy verification accept a non-executable kiosk or copied startup entrypoint. | Primary confirmed source 0644 acceptance despite clean Git mode status, then separately replayed original embedded copy checks accepting all three copied 0644 entrypoints. Normal and byte-tamper controls behave as expected. | Require executable regular kiosk input and recheck copied wrapper, kiosk and nwipe hook through the trusted source helper. Manifest schema is unchanged. Ten cases cover modes, missing/directory/link paths and malicious copied helpers. |
| Held Enter closes the curses Keyboard view and also accepts a retained confirmation token. | Primary trace reaches `KEYBOARD → CONFIRM → METHOD` using two repeated Enter events. | Reuse the existing Enter hold/release guard in Confirm. Three cases include interleaved editing and a fresh-key control. Token, countdown and separate Erase now remain required. |
| Interrupted GTK startup leaks its owned window or timer. | Primary reproduced a retained visible startup window after KeyboardInterrupt, while normal/error controls and an unrelated window behaved correctly. | Own cleanup across setup, launch and event-loop failures; retire only the owned source/window and quit only the owned loop level. Ten cases preserve peers, primary exceptions and independent cleanup. |
| Optional exception notes can replace primary cleanup errors and strand refresh completion on Python 3.10. | Primary replay of archived pre-guard source has two failures and two controls. | Guard the optional `add_note` capability in GTK cleanup and refresh. Four cases model the absent API and preserve ordinary note behavior. Python 3.10 itself was not run. |

The first complete gate also exposed a test-fixture cache defect: 22 launcher
cases errored in setup because cached `go test` output did not recreate a
temporary JSON file in a fresh container. The primary reproduced successful
generation, deletion, then a cache hit with the file still missing. A new
behavioral regression fails before the repair; the fixture now uses `-count=1`
and all 24 adjacent launcher checks pass. No product or existing test assertion
was changed. The failed full run (10,384 passed, 28 skipped, 22 setup errors)
and exact first freeze are retained under [history](history/). The only two
inputs changed after that freeze are the fixture invocation and new regression.

Exact primary pre-edit traces are under [proofs](proofs/). The first identity
candidate failed an unchanged model-mutation guard and was rejected; the final
append-only fingerprint preserves both checks. That failed candidate's log is
retained, rather than counted as a pass.

## Review and verification

The final canonical phase exits0. Main pytest has **10,407 passed / 28 skipped**
in1055.07s; independent Orca has **1 passed**. All10,159 baseline main test IDs
remain present, exactly276 cases were added, and every skip ID and reason
matches the setup baseline. The787 frozen source hashes still match.
[Exact summary and skip reasons](final-summary.json),
[full log](checks/full-source.log),
[main JUnit, gzip](checks/final-tests.xml.gz),
[Orca JUnit, gzip](checks/final-tests.xml.orca.xml.gz).

Four bounded subagents reviewed discovery/classification/authorization/argv;
runner/progress/cancellation/log evidence/recovery; Tk/GTK/curses/startup;
and boot/build/desktop/hardware compatibility. The primary independently
reproduced each finding, reviewed the complete product and test diff, integrated
the changes and reviewed report/export/recovery behavior. Additional review
found no further reproducible defect within those bounded scopes. This is not
a proof that every possible defect is absent.

- Primary integrated new regressions: **276 passed**, zero failures/errors/skips.
  [Log](checks/new-regressions.log), [JUnit](checks/new-regressions.xml).
- Primary report/export/recovery selection: **401 passed**.
  [Log](checks/recovery-report.log), [JUnit](checks/recovery-report.xml).
- Focused final subagent checks: storage 733 passed, runner 1,356 passed,
  boot/build 76 passed, wizard/cleanup adjacent checks passed. These selections
  overlap the complete suite; do not sum them as unique tests.
- [Lint/types/security/shell](checks/lint.log),
  [web/console/helper preview and embedded JavaScript](checks/preview.log),
  [private safety mutation](checks/safety-negative.log),
  [Go race](checks/go-race.log), [vet](checks/go-vet.log),
  [350,027 fuzz executions](checks/go-fuzz.log),
  [launcher builds](checks/desktop-build.log) and
  [Windows test cross-compilation](checks/windows-test-build.log) pass.
- [Supplemental browser assertions](checks/system-browser.log): **9 passed**
  using explicitly selected system Chromium 155.0.8059.79 and unchanged test
  assertions. This does not qualify the missing Playwright-pinned browser.
- Actual `./preview` inspected on private Xvfb at 72 DPI:
  [capture receipt](preview/capture.json). The unaltered image remains local at
  `/workspace/beamo-tools/audit-20261019/root/tk-preview-72dpi.png`.
  Text and buttons are visible without clipping. The owned preview child was
  terminated after capture; normal-close acceptance is not inferred.
  Automatic approval review rejected the optional screenshot export because it
  considered that image export and external destination unverified. The image
  is omitted from the published tree; code and text evidence continue normally.
- A deterministic 1,500-case [projection comparison](review/projection-differential.json)
  found no difference in outcome or advisory-check statuses between complete
  logs and bounded streaming assessment. Original log bytes remain unchanged.

Canonical source command:

```sh
/workspace/beamo-tools/beamo-dev env BEAMO_GATE_CHILD=1 \
  BEAMO_GATE_JUNIT=/workspace/beamo-tools/audit-20261019/root/final-tests.xml \
  bash scripts/ci-hosted.sh tests
```

It runs main pytest and mandatory Orca on separate private D-Bus/Xvfb sessions
at 72 DPI. Lint, preview and negative checks use the same local phase wrapper.
Go checks use the pinned toolchain, with native inventory opt-in unset.
[Artifact review](artifact-review.json) records actual PE/ELF build hashes and
dirty-source identity. Cross-builds are not native execution acceptance.

One initial integrated invocation used private display :99; the new fixture
guard rejected ten GTK cases. The corrected invocation changes only the
display to private :300; all 275 pass. The setup error remains in workspace
history and is not counted as a product failure or pass. Lint's unchanged TODO
warning comes from the literal placeholder-detection regex in
`release_manifest.py:40`; mypy's untyped-body notes are informational.

## Remaining qualification

Local development uses `/workspace/beamo-tools/activate.sh` or the disposable
`/workspace/beamo-tools/beamo-dev` wrapper. The version receipt and exact
entrypoints are retained under [development](development/). An additional
environment probe proved that the wrapper discarded piped stdin; it now keeps
stdin attached and allocates a TTY only for terminal sessions. The identical
probe changes from empty input/exit1 to exact input/exit0, and ShellCheck and
Bash syntax checks pass. The already-running source gate uses its original
container; project runtime/test/build inputs are unchanged by this helper fix.
An initial stdin-fed version probe produced no output and is not counted as
verification; the successful version receipt came from executing a script file.

The28 skips comprise14 absent image/build artifacts,9 unavailable pinned-browser
cases,4 external Microsoft documentation checks denied by the proxy, and1 legacy
gcloud check. Their exact IDs and reasons are retained in final-summary.json.
No unexpected skip was introduced. The managed network denies the pinned Playwright download and four external
Microsoft documentation checks. Generated live-image fixtures are absent;
the legacy gcloud CLI is outside current development requirements. Exact skip
IDs and reasons are retained with the final source result. Skips are not
passes. The system-browser supplement covers nine assertions with a different
runtime and does not change canonical skip counts.

ISO/QEMU, native Windows/macOS, real firmware, physical disks/USB and physical
reconnect acceptance are **not run** for these changes. This worker lacks KVM;
the project reserves final ISO/native qualification for separately authorized
isolated workers. No real nwipe, physical device mutation, host restart,
firmware change, hosted CI, merge or release was performed.

The owner explicitly resolved the missing shared-guide stop condition and
instructed continuation. Current repository Blacksmith guidance governs;
the pasted legacy GCP CI baseline was not executed. The canonical
[unfinished record](../../../.ai/memory/unfinished-work.md) retains the history,
remaining qualification and commit/push state. Raw working evidence remains
under `/workspace/beamo-tools/audit-20261019/`; authentication and environment
dumps are excluded from this retained selection.
