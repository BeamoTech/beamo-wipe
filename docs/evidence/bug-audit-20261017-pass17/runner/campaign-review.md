# Prepared pass17 runner campaigns

2026-10-17 / Codex `pass17_runner`. Source-only preparation while the primary
serial full gate runs. Neither campaign was executed by this child. Product and
test sources were not changed during this preparation.

The two retained pass16 campaign programs were read in full and adapted into
`fresh-boundaries.py` and `cancel-boundaries.py`. `campaign-prepared-sha256.txt`
authenticates the prepared bytes. The primary must execute them serially, after
the canonical full gate, through `/tmp/beamo-pass17-python/bin/python3`, with the
root's fallback-guard directory on PATH. Each script verifies that interpreter
spelling and all eight guard bytes against the root's current manifest before
any product call.

The first campaign exclusively creates `/tmp/pass17-runner` with mode0700; an
existing path is an admission error, not something to remove or overwrite. It
preserves all153 short semantic/projection comparisons,153 actual >1MiB
ordinary-file polls,90 successful evidence/export-readiness/recovery/tamper
roundtrips and54 mixed advisory traces. Its native process handle is an inert
Python class. The genuine busy diagnostic was already timestamped in pass16;
no expected outcome or fixture shape was changed to hide new origin behavior.
The fixed448-case module separately tests mixed model/native log origins.

The cancellation campaign requires that same owned mode0700 base, then creates
a new mode0700 `cancellation` directory and144 unique case directories. It
preserves three paths × three methods × two completion states × eight modes:
already exited, natural exit on status probe, natural exit during terminate,
lookup gone, one status error, timeout/kill, one wait error, and never exits.
Those names refer only to fake method calls, never OS process operations.

Each cancellation case now retains its own ordinary log and lock fixture. An
independently opened descriptor attempts nonblocking flock: it must fail while
ownership is held, including both wait-error and never-exits uncertainty, then
succeed only after the explicit retry confirms terminal state. Both retained
log/lock descriptors must remain valid during uncertainty and be retired after
the terminal result. Raw log bytes must stay unchanged. Unique144 log and144
lock files should be retained by the primary in addition to the previous333
runner/evidence fixtures; final source-file counts are verification results,
not assumed from this preparation.

Both programs reject Popen/run, os.system, OS PID signals, socket creation and
connections, real engine lookup and rediscovery. Native /dev,/sys,/proc opens
are rejected through os.open, builtins.open and io.open; device realpaths stay
fictional strings. No GUI, process, namespace, loop, mount, disk operation,
network request or CLI invocation is part of the programs. Flock acts only on
their positively identified private regular files. The scripts read repository
source hashes and write only owned campaign fixtures/results. Before/after
assigned source hashes and the guard/interpreter receipts are emitted in their
summaries. Missing summaries, nonzero exit, mismatches or forbidden acquisitions
are failures requiring review; no cleanup or blind rerun is authorized here.
