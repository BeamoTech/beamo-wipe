# Optional audio launch interruption candidate

2026-10-17 / Codex child `/root/pass20_runner_boot`; source-only, UNPROVED.
No product/test source was edited and this child did not execute the probe.

`src/beamo_wipe/audio_jobs.py:93` registers a Thread before calling start.
Its RuntimeError branch clears the queue and `_thread`, but KeyboardInterrupt
or SystemExit skips that branch. The `finally` still releases the launch gate
without allowing the worker to run. A later submit sees the registered dead
or rejected worker and does not create a replacement. Interruption propagation
is intended; retaining an unusable worker slot appears unintended.

The adjacent six-case `audio-launch-interruption-probe.py` models only Thread
handoff using synchronous Python objects. Two RuntimeError controls exercise
the current returned-error-ticket behavior; four control-interruption cases
require the original exception and then a fresh replacement slot. The probe
creates no OS threads, processes, native UI, inventory or device operation.
Its fake second target deliberately does not execute; assertions concern the
product's real registration and launch decision only. Root must independently
review and run it before labeling any defect proved or editing source.

This candidate is unrelated to evidence of the earlier native Tk abort and
does not establish that optional audio caused it. It cannot authorize a
product change, relax a test timing bound, or replace a full gate.
