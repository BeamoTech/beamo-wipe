# Current-source bug audit ? 2026-10-24

This exact-source report is historical. The source now includes the newer
work and two further fixes recorded in the
[October 25 continuation](../bug-audit-20261025/README.md). Its combined source
requires new runtime qualification; the older receipts remain unchanged.

Base: `9764d93ac21273aa79ae4618629b0a30e3eda271` (Beamo Wipe 0.2.14).
Branch: `codex/wipe-audit-20261024`; worktree:
`C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`.
**Status: LOCAL FIXES SAVED; FINAL VERIFICATION BLOCKED.**
Runtime/test input identity: `ed606e09bb66493629f618c34a22627cc5275965a3c9ac235294ca0dea6615b0`.
See [the machine-readable verification record](verification.json).

The older October 14 dirty audit worktree is preserved separately. Its results
do not qualify this source. No commit, push, hosted job, release, firmware
change or physical media operation occurred in this pass.

## Confirmed defects and corrections

- Status parsing: overlapping optional-marker whitespace and leading rate
  padding caused eight exact-source cases to exceed a five-second computation
  bound on 65,535 spaces. Factor the marker and separate CR/LF prefixes from
  the rate field. All 29 timeout/control cases pass; 192,160 old/new predicate
  comparisons and another 24,000 reviewer comparisons found no language/group
  difference. These finite samples do not prove a universal complexity bound.
- Report cleanup: failures during unmount or close replaced the original
  refusal, and early cleanup failures could skip remaining resources. Preserve
  the primary exception object, attempt remaining cleanup once, and log fixed
  stages plus exception types only. A pending success cannot survive cleanup
  failure. This now covers worker, mounted-state, bundle-directory, member-file
  and optional-log helpers; ordinary optional-log I/O errors remain unavailable.
- Interrupted report acquisition: worker, bundle and member-file handles were
  opened before protection. Acquire them inside protected scopes. A further
  fake-mount trace proved both RW and RO mounts could be left without explicit
  cleanup after command-side effects but before mount-state assignment. Mark
  cleanup pending before each command and retain exact-device checks during
  ordinary cleanup. No real mount was used for these regressions.
- Cancellation evidence: the wizard replaced observed engine exits with 143.
  Preserve the observed exit code, including negative SIGTERM/SIGKILL values,
  through persisted evidence. Positive shell codes remain positive codes and
  are not used to guess a signal. Interruption flags/copy remain unchanged.
- Rendered GTK sound test: construction plus scheduling measured about 95 ms
  against a 60 ms assertion. The revised test proves worker-thread discovery,
  GTK idle progress while discovery is withheld, and rejection of late results
  after closure. A synchronous-worker mutation fails the intended assertion.
  All 19 separate headless audio timing cases and their limits are unchanged.

The six new test modules contain 161 cases. Disk selection, boot exclusion,
authorization/countdown, methods, nwipe flags/pins and product claims are unchanged.
Four bounded independent reviews were read-only. Their findings were independently
reproduced before fixes. The last proposed mount gap was reproduced by the parent
in four failing cases and fixed before the final full run.

## Local verification

Raw commands, source manifests, stdout/stderr, JUnit, queried exits and cleanup
receipts: `C:/Users/Jack/beamo-release-evidence/wipe-audit-pass2-20261024`.
Each product harness checks exact source bytes before/after, owned process and
descendant reaping, unchanged parent `/tmp` metadata/network namespace and absence
of its private sentinel outside the namespace. A transport exit is not a test exit.

Tests use the existing WSL distribution as host UID 1000, unprivileged private
user/mount/network namespaces, private `/tmp` and loopback, and 72 DPI Xvfb. The full
run additionally bound an owned ordinary fixture directory inside its namespace.
That choice violated the live log filesystem guard in three fake recovery cases;
it is invalid for full qualification and must be corrected. Application runtime
remained private tmpfs. This is local source-test
evidence, not pinned hosted-container, ISO, controller, cold-readback or physical
acceptance. No host disk or USB is passed into tests.

| Run | Actual result |
| --- | --- |
| `current-cleanup-causal-red` | 34 failed / 10 passed, exit 1 |
| `current-cleanup-green` | 44 passed, exit 0 |
| `current-parser-red` | Eight computation timeouts / 21 controls passed, exit 1 |
| `current-parser-green` | 29 passed, exit 0 |
| `parser-equivalence` | 192,160 comparisons, zero differences |
| `helper-and-cancel-corrected-red` | 46 failed / eight passed, exit 1 |
| `helper-and-cancel-final-green` | 54 passed, exit 0 |
| `member-causal-red` | 15 failed / 67 passed, exit 1 |
| `member-and-helpers-green` | 84 passed including two FileExistsError controls, exit 0 |
| `mount-acquisition-red` | Four failed / 44 passed, exit 1 |
| `mount-acquisition-adjacent-green` | 311 passed, exit 0 |
| `causal-audio-green` | Revised rendered test plus 19 headless cases passed, exit 0 |
| `causal-audio-sync-negative` | Intended synchronous mutation rejected, exit 1 |
| `mount-acquisition-lint` | Configured syntax/security/full lint, shell and mypy passed, exit 0 |
| `final-runtime-preview` | Fake web/console/helper and three JS syntax cases passed, exit 0 |
| `final-runtime-negative` | Expected private-mutant failure and production safety pass, gate exit 0 |
| `final-network-docs` | Four exact-source live Microsoft URL tests passed, exit 0 |
| `recovery-failure-diagnosis` | All three failing full-run cases passed on private tmpfs |
| `recovery-module-diagnosis` | Entire recovery-alias module passed on private tmpfs |
| `recovery-disk-fixture-diagnosis` | Filesystem-only change reproduced all three refusals, exit 1 |
| `final-reviewed-full-gate` | INCOMPLETE after environment interruption; no final main JUnit, controller receipt or queried exit |

## Final full-run interruption

The recovered output contains 8,119 pass lines, three failed test lines and 18
skip lines before interruption at about 66%. These are partial log observations,
not a full-suite verdict. Orca separately has a complete one-pass JUnit receipt
(105.929 seconds). The main JUnit and original controller receipt are absent;
the raw stdout ends in NUL bytes. Raw bytes and hashes remain unchanged.

All three failures are the same unchanged fake recovery test. Isolated cases and
the entire module pass on private tmpfs. Moving only their fixture files to an
ordinary filesystem reproduces the three failures and the exact SafetyError:
`Log directory must be on the /tmp filesystem.` Production correctly refused.
No guard, assertion or production code was changed to accommodate this harness
mistake. The owned harness now restores full-run tmpfs fixture paths, uses a bounded
512 MiB private tmpfs, and requests pytest retention of failed fixtures. Its
new admission check requires at least 8 GiB free disk and 2 GiB available RAM
before any WSL/source/test startup. This is an audit-harness envelope, not a
product hardware claim. The current host was refused with exit 2, at about
361 MiB free disk and 1.06 GiB available RAM. Nested harness/namespace syntax
checks pass; the corrected full configuration is not yet qualified.

The 18 observed skips comprise unavailable gcloud for one legacy test, four
network-isolated URL checks, two absent lb-config artifacts, and eleven absent
manufacturing-ISO checks. The four URL checks subsequently passed unchanged
with ordinary network access. The other acceptance prerequisites remain absent.
Intentional failing nested mutation/JUnit fixtures also appear in the diagnostic
failure log; their records are distinct from the three actual main-suite failures.

Host free memory was observed at about 506 MiB and C: free space reached
92,262,400 bytes. A read-only Windows command returned access-violation status
`-1073741819`. The bounded stop helper timed out; a subsequent exact-PID, cwd,
command and output-handle check found the gate leader already absent and sent
no signal. Recovery observed WSL uptime of about 125 seconds, showing the test
environment had restarted since the much earlier run began. The restart's cause
was not independently established, and no host/WSL restart was requested.

Current source/fixture cwd inspection found no owned processes, and full candidate
byte readback matches its start manifest. This current snapshot cannot replace
the missing original teardown/source/namespace receipt. No full-gate pass is
claimed. Do not launch another heavy run on this constrained host.

The three failed fake fixture directories were archived and readback verified
before retiring only this run's disposable fixture tree (9,727 files,
146,976,768 allocated bytes). Source, raw logs and peer paths remain. The original
source transfer was also regenerated from retained Git objects and matched its
320,245,760-byte SHA-256 before the redundant 154,935,941-byte gzip was removed.
Receipts: `interrupted-final-recovery.json`, `interrupted-fixture-retirement.json`,
`redundant-transfer-removal.json` and `host-resource-interruption.json`.

## Retained failures and environment limits

- The first full run reproduced the GTK timing assertion. It was canceled with
  queried exit -15 after confirming the cause; its separate Orca test passed.
  The second full run was canceled with queried exit -15 after the reviewer
  reproduced deeper member-file cleanup defects. Both owned cleanups/guards
  passed; neither canceled run is a full-gate pass. The second cancellation's
  copied reason field incorrectly names the earlier GTK issue; this paragraph
  corrects that annotation without changing raw observations.
- `complete-export-adjacent` had 297 passes / ten missing-source-context failures
  because its filtered harness omitted packaging/scripts files. Correcting that
  snapshot produced 307 passes. The final mount fix then produced 311 passes.
- An intermediate cancellation test incorrectly expected signal 15 for positive
  shell exit 143. Four failures from that test expectation are not product bugs;
  the corrected red result above retains the true 46 failures.
- Initial WSL startup, absent `/mnt/c`, and ignored archived evidence during Git
  reconstruction were retained setup failures. The baseline transfer verified
  all 7,578 files / 314,127,504 bytes and exact tree/commit bytes. A later idle
  WSL check stopped three commands before tests; using the already registered
  distribution directly removes that preflight race without configuration changes.
- Lint's unchanged TODO detector matches its own `PLACEHOLDER_RE`; reviewed as
  a false-positive warning. Existing mypy untyped-body notices remain unchanged.
- Remote Lab `d3d0959` doctor/sync/Wipe planning passed as preparation. Framework
  self-test: 58 passed / one error because a descendant PID fixture was absent at
  its deadline. The valid receipt retains FAIL. Product evidence is separate;
  Lab implementation/pins were not changed to make that result pass.
- Native Windows Go test reached its 900-second bound without a test exit or
  test output. Owned Job termination returned 125, descendants were absent and
  cleanup had no errors. The Go inputs were unchanged, but the whole source
  inventory spanned Python/test edits. No native pass is claimed; vet/developer
  native gates remain unrun. Resource pressure makes a blind retry inappropriate.
- Only positively owned, completed source copies were retired after preserving
  and readback-verifying exact overlays. Four recovered capsules are recorded
  in `retirement-recovery.json`. The redundant Windows transfer tar was removed
  only after gzip byte/hash readback; its receipt is
  `transfer-archive-compaction.json`. No peer evidence/cache was removed.

## Remaining work

Run the full local gate on a suitable, authorized worker with adequate memory and
storage, private tmpfs fixture semantics, bounded owned cleanup and retained
failure evidence. The installed pytest retention fixture was inspected and hashed; validate
the full corrected Linux configuration before accepting it. No test, assertion, timing limit or guard may be weakened.
Verify final JUnit/skip/warning counts, queried exit and original cleanup receipts.
The interrupted run cannot be reused as a passing gate.

Native Windows Go timed out, native vet/developer and desktop qualification are
pending, and the Remote Lab framework self-test retains its error. ISO/QEMU and
physical acceptance retain their original prerequisites. Physical Secure Boot
task #119 and cold media readback remain NOT TESTED / BLOCKED. No commit/push is
permitted while required verification is incomplete; publication is separately
authorized. All source fixes and regression files remain in the local worktree.
