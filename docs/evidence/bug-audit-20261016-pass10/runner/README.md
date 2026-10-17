# Pass10 runner and recovery audit

2026-10-16 / Codex runner subagent. Repository BeamoTech/beamo-wipe;
worktree `/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, base HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. All exercise uses fake process
objects, device strings, and regular temporary files. No real engine, device,
guest, hosted job, commit, push or release.

Read project AGENTS.md, relevant current unfinished-work records, prior pass9
runner evidence and current source. Shared `/root/dev/AGENTS.md` remains absent;
prior owner resolution in the canonical record applies. Parent owns repository
evidence integration and unfinished-work edits; other agents' files preserved.

## Proven finding: completion projection changes record contents

`NwipeRunner._scan_completion_log` used `rstrip("\r\n")` on newline-terminated
binary records. It silently removed carriage returns that remain present in the
normal byte-decoded completion tail. A Drive Status banner suffixed with CR is
not the exact trusted engine banner used by `_target_reported_success`; removing
CR created a matching banner. This made the same malformed status evidence fail
as `completion_missing` below 1 MiB but succeed as `completed` above 1 MiB.
The late-Stop natural-exit path also converted this malformed evidence to success.

This is a malformed-log consistency/provenance bug; it does not establish that
pinned nwipe naturally emits CRLF. The parser's preexisting exact-banner
provenance rule is preserved. No claim of actual hardware/erase impact is made.

Concrete pre-fix proof: `record-ending-proof.py`, `record-ending-before.txt`.
Six actual `runner.poll` cases use 128–130 byte or 1,113,917–1,113,919 byte regular
files. Genuine LF completes at either size. CRLF and double-CRLF fail when small
but falsely complete when large. Every file remains byte-identical.

Regressions: `tests/test_runner_projection_record_endings_pass10.py` has 45
cases across three methods, polling and Stop race, CRLF/double-CRLF/LF,
carriage returns inside models, and exact 1MiB−1/1MiB/1MiB+1 boundaries.
Original `record-ending-original.{txt,xml}`: **13 intended failures, 32 passing
controls, 0 errors/skips**, 1.038 seconds. Exact pre-fix runner snapshot is
`nwipe_runner-before.py` (includes the retained pass8 projection-order fix).

Approved minimal source change removes exactly the single final LF before
UTF-8 decoding. It retains CR and every other record character. Existing pass8
progress-order changes are preserved. Post-fix six-case trace in
`record-ending-fixed.txt` matches direct completion assessment at every size.

## Source review

Revisited runner preflight/request binding, locked launch and log identities,
inherited flock and descriptor lifetime, Popen uncertain ownership, SIGUSR1
readiness, concurrent progress ordering, poll/cancel result publication,
natural completion during Stop, failure/no-erase contradictions, method/round/
pass evidence, exact decimal terminal percent, bounded whole-log projection,
error-table context, checks and terminal recovery. Reviewed SessionStore
directory and named-lock identities, saved record validation, partial atomic
publication, quiescent ownership, session rotation and terminal digest/log
revalidation. No additional proven defect in this review so far.

## Completed focused verification and handoff

`runner-fixed-adjacent.{txt,xml}`: **412 passed, 0 failures/errors/skips**, in
70.365 seconds. Includes all 45 new regressions and runner/completion/
engine-check/session/recovery-lock/large-assessment adjacency. The preexisting
pass8 progress-order regressions are included. All five hashes in
`source.sha256` still match after verification. The owned pytest exited 0 and
the test slot was released to the parent.

No additional verified finding or incomplete reviewer-owned implementation
remains. Parent owns independent review, final full local gates, durable
repository evidence and canonical backlog updates. No hosted/platform/native/
physical acceptance claimed. No source/config changes outside the approved
scanner delimiter fix and the new 45-case regression module by this reviewer.
