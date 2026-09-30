# Negative-gate subprocess cleanup — #124

2026-09-29, Codex. Base `c170c85aff70ca55bebe5674ef6854e9c02b4999`
(the preserved local #123 commit). Branch `codex/negative-gate-cleanup-124`.
The commit containing this receipt identifies the exact correction:
`git log -1 --format=%H -- docs/evidence/negative-gate-cleanup-124.md`.
No production code, hosted gate script, workflow, disk operation or release
was changed. No hosted job, push, merge or publication was performed.

## Reproduced leak and protected invariant

`tests/test_boot_pipeline_pass5_negative.py` launched `bash ci-hosted.sh
negative` with a stdout pipe, polled a readiness marker for up to 15 seconds,
inspected its temporary checkout's safety source, then called
`communicate(timeout=30)`. It had no `finally` or child owner. A timeout or
source-inspection exception left the child running and its pipe open.

Before editing, a controlled replacement launched only a Python child which
created the existing readiness marker and slept for 30 seconds. Its first
`communicate` deadline was reduced to 50 ms. The unchanged test raised
`subprocess.TimeoutExpired` at line 81 after 0.106 seconds; the child still
ran, `waitpid(pid, WNOHANG)` returned `(0, 0)`, and stdout remained open.
A `ps` lookup of **that exact PID only** also showed the sleeping process.
The reproduction harness then terminated and reaped its child and closed the
pipe. [Results](negative-gate-cleanup-124-results.json) retain the original
traceback, PID observation and cleanup record, not just a process-table claim.

The invariant is unchanged: the negative mutation must stay in its private
import tree, never in the checkout another process could import. All five
original assertions are AST-identical, including the observed bytes, mtime,
permissions, gate exit status and final source checks. The shell gate still
requires the specific `DID NOT RAISE` proof for uncertain boot identity, then
passes the pristine fake-device test. Its source and production safety code
were not edited.

## Ownership, cleanup and bounds

The test now owns the launch and all subsequent operations through
`tests/negative_gate_child.py::owned_gate_child`. It starts a new POSIX session
using the repository's existing `start_new_session=True` launch convention.
The inspected shell, sleep wrapper and pytest descendants inherit that group;
none detach into another session. Cleanup signals only that owned group. If
a parent-side startup error occurs before a private group is available, it
signals only the acquired child PID, never the parent's inherited group.
A small `Popen` subclass retains access to the acquired PID if initialization
raises before the context-manager assignment completes. A failed exec with
no live child is left to the standard `Popen` failure cleanup.

Cleanup on normal return or any `BaseException`:

1. Send SIGTERM and drain output during a **1 s** grace interval. Remaining
   group members receive the rest of the same interval even if the shell
   exited and they closed their inherited output descriptors.
2. If the group/owned child remains, send SIGKILL. Allow **1 s** for final
   `communicate`; output collection failures do not bypass reaping.
3. Independently call `wait(timeout=1)` and close every parent-owned pipe.
   A cleanup failure raises an explicit error; if another exception already
   exists, its instance/type/traceback remain the raised error and cleanup
   diagnostics are recorded as its cause.

Configured cleanup waits total at most **3 s**, plus scheduling/system-call
and Python interruption overhead. The original probe and collection deadlines
remain 15 s and 30 s (48 s total configured waits including worst-case cleanup).
There is no unbounded `wait`, `communicate`, join, or retry. The code avoids
`Popen.__exit__`, whose wait is unbounded. Pipe draining is synchronous on
POSIX; no reader thread can retain the stream lock during close.

This is intentionally Linux/macOS bash-test support, not a Windows Job Object
implementation. Other platforms skip this POSIX shell test explicitly. Only
the direct child is waitable/reapable by this parent; the descendant fixture
has its own parent reap it and writes proof. Detached descendants are outside
the current gate's launch contract. An unkillable kernel task or OS cleanup
failure cannot be promised away: wait/collection failures remain visible
rather than being treated as confirmed success.

## Verification

macOS arm64, Python 3.10.0; harmless local commands and fake disks only.

```sh
BEAMO_WIPE_DRY_RUN=1 python3 -m pytest -p no:cacheprovider -o addopts='' -q \
  tests/test_negative_gate_child_cleanup.py tests/test_boot_pipeline_pass5_negative.py \
  tests/test_boot_exclusion_fails_closed.py

BEAMO_WIPE_DRY_RUN=1 PYTEST_ADDOPTS='-p no:cacheprovider' \
  ./scripts/test-all.sh -o addopts='' --junitxml=/private/tmp/beamo-wipe-124-full.xml
```

- Focused lifecycle/boot-safety run: **93 passed, 12.73 s**.
- Five separate repeated runs of lifecycle plus actual private-checkout gate:
  **19 passed each**, all exit zero; wall times 15.908, 16.384, 15.689,
  13.012 and 19.207 seconds (including pytest startup).
- Across those runs, the stubborn-child timeout/escalation test's maximum
  measured duration was **1.212 s**. The original negative-test timeout path
  with cleanup took at most **0.191 s**; its direct child was reaped and pipe
  closed. Both tests allow a 5 s outer regression bound for scheduler overhead.
- Readiness uses a marker or bounded descriptor readiness, not a guessed
  startup sleep. Assertions require `Popen.returncode`, closed pipe state and
  `waitpid` raising `ChildProcessError` after reaping. Unrelated sentinel
  processes remain alive throughout the tested cleanup.
- Cases cover success, nonzero early exit, failed exec, acquired-child startup
  errors with/without a private group, assertion, unexpected exception,
  KeyboardInterrupt, SystemExit, timeout, SIGTERM resistance, output errors,
  output exceeding pipe capacity, eight launches within one test, descendant
  termination/reaping, and visible cleanup errors with/without an original
  exception. A controlled shared-source mutation still fails the original
  assertion; removing the boot guard still yields `DID NOT RAISE`.
- Full local suite: **4,664 passed, 704 skipped, zero failures or errors,
  468.52 s**. All lifecycle and negative-gate cases executed. Compared with
  #123, the sole extra skip is the unrelated Microsoft Windows Recovery
  Environment link check: `EOF occurred in violation of protocol (_ssl.c:997)`.
  The other 703 skip identities are unchanged; no new dependency skip hides
  lifecycle coverage.
- Prescribed compileall, Ruff (including security selections), developer-tool
  formatting, mypy (50 source files), ShellCheck, actionlint and diff checks
  passed. No production signing, ISO build or real disk command was run.

Detailed logs/JUnit remain disposable under `/private/tmp/beamo-wipe-124-*`.
The adjacent result receipt keeps their hashes, repeated-run measurements and
tested source hashes. Native Linux/Blacksmith execution for this source is
**NOT TESTED**; macOS exercised real POSIX subprocesses. Exact-source hosted
qualification remains the next separately authorized step. Prior task commits
and unrelated primary-checkout edits remain preserved.
