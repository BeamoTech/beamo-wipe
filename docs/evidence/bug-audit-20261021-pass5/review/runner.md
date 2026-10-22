# Fifth-pass runner/evidence review

Baseline: e4871239f02e46137fb6d8df64b5880ae2ea4b4d.
Outcome: no new verified defect; no tracked edit.

Reviewed nwipe_runner.py process start, locked final identity recheck, command
construction and validation, inherited flock, log descriptor/inode retention,
ambiguous Popen ownership, active-request binding, poll ownership and stale
completion suppression; progress ordering and monotonic cap; cancellation,
failed signals, kill/wait escalation, natural-exit evidence and retry semantics.
Also reviewed whole-log scan/read size/identity/truncation and record context,
method completion counters, engine_checks hidden/media summaries, progress.py
stage/ETA/freshness logic, methods.py and sleep_inhibit.py lifecycle, plus the
wizard evidence snapshot handoff and failure settlement boundary.

Focused baseline:165 PASS. Expanded66-module adjacent gate:1380 PASS,
0failures/errors/skips;62.29s. Module list, log and JUnit retained. These overlap
each other and the root full gate; do not add as unique cases.

New seeded comparison:2000 fake logs, each classified through all3methods,
compared full versus actual runner scan projection and exact structured media
check payloads. Components include malformed/zero/nonzero native summaries,
header/close prefixes, target/foreign failure markers, skip reports, hidden
capacity warnings and final/nonfinal/counter-contradicting progress. Every log
starts with a real-shaped native context record; unlike the earlier bare-input
probe, an empty projection cannot erase native provenance.0differences.
Script and JSON are retained in this directory. Only ordinary temporary log
files are opened; no engine/device action is invoked.

Read-only pinned source review fetched nwipe6082bde060091e66365d852a1877f2ee80c67105
through the normal proxy/CA. Exact URL/hash receipts retained. context.h99 and
device.c637-690 confirm serial20-byte cap/control normalization; logging.c1098-
1116 confirms status model17/serial20 caps. This supports existing full-banner
provenance boundaries. No binary was compiled or executed.

Rejected speculation: main's quoted Device '/dev/...' busy-seatbelt sentence is
not an exact parser match. Source inspection shows the same context already
logged its early busy warning and was excluded at initial selection; no new
reachable contradictory-success route was proved. The earlier warning is
retained by large-log projection. No speculative parser edit was made.
Likewise normally returning terminate remains ambiguous by an explicit existing
regression contract; only failed delivery proves that a signal was not sent.
The current code preserves that contract and the prior PASS3 delivery repair.

Reviewed source hashes in report.json still match baseline. Parent owns source
integration, independent confirmation, final complete gates, backlog and any
publication decision. Native/platform/physical qualification remains separate.
