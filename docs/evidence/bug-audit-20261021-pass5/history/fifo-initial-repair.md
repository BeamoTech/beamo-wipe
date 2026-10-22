# Late FIFO log-open repair

Root independently reproduced the exact failing actual-runner case before
approval. A private log pathname changed from regular file to FIFO after its
first safety guard. The blocking write-only open waited indefinitely before
fstat could enforce the existing nonregular-file refusal. Runner start already
owned the wipe slot; no engine launched. This is a narrow availability bug under
the existing same-owner replacement-race scope, not an unprivileged attack or
unsafe erase. Root superseded the prior in-progress canonical gate before repair.

Minimal product change: safety.truncate_log_file opens the log nonblocking.
No-reader FIFO opens now fail promptly; reader-present FIFOs still reach the
existing fstat refusal before truncation. Regular-file creation/truncation and
retained descriptor transfer keep their prior behavior.

New regression module tests all9 combinations of runner/direct-close/direct-retain
and regular/FIFO-alone/FIFO-with-reader paths. It checks refusal without waiting,
no engine callback on invalid files, released wipe/log descriptors, unchanged
prior bytes and corrected retry. It does not assert a specific flag spelling.
Owned helpers use only temporary ordinary logs/FIFOs; no real engine, disk,
inventory or mount callback runs. Failed old-code helpers are unblocked through
only their owned FIFO readers for clean exit; emergency teardown targets only
the owned helper. The test is POSIX, matching the supported wizard runtime.

Exact final formatted new module replay on archived safety-original.py:
3FAIL/6controlsPASS, noerrors/skips. All3 failures are FIFO-without-reader hangs.
Final affected adjacency207PASS, including all9 new cases; unchanged original
proof2PASS. Ruff/check-format, both changed files'3.10 grammar, git diff check PASS.
Full source/runtime qualification remains root-owned. Hashes in final-sha256.json.

Draft/setup history is retained: initial test FD accounting mistook fdopen-managed
reader closure for a leak and was corrected before recording the genuine red
baseline. One nonexistent adjacent module path caused a collection-only setup
error; explicit corrected selection passed. No original assertion was altered.

Product source and new tests are frozen and released to root. No further edits,
staging, backlog, commit, remote operation or delegated task was performed here.
