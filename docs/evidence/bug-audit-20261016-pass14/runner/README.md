# Pass14 runner, progress, engine checks and recovery review

2026-10-16 / Codex subagent `/root/pass14_runner`.
Repository `/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`,
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.

Status: source review complete; corrected fake differential and focused suite
prepared, awaiting the primary agent's serialized runtime slot. No application
or repository test file was edited by this subagent. No supported new runner
bug has been established.

The source review covered runner preflight and duplicate-start state, method
and target binding, pinned engine and already-running probes, inherited-lock
and log inode ownership through uncertain spawn, progress snapshot ordering,
complete records, terminal scans and evidence caps, summary context/order and
positive/negative provenance, cancel/poll/late Stop races, failed process-status
checks, cleanup uncertainty and retries. It also covered progress stage/clock/
freshness/estimate gates; hidden-capacity and I/O advisory parsing; evidence
completion consistency; same-boot journal schema, directory/lock/file identity,
atomic writes, quiescence, terminal authentication, recovery and session rotation.
Seven exact source hashes are retained in `source-review-start.json`.

## Candidate disposition and initial campaign

The whitespace-prefixed Error Summary delimiter hypothesis did not establish
a product bug during source review: the exact raw malformed delimiter is
retained in the projection and itself prevents an advisory pass. Full runtime
comparison remains to be recorded by the corrected campaign.

`differential-matrix-v1.py` is the exact first campaign source. Its run ended
naturally with exit 1 at line 108 (`differential-run.txt`). It incorrectly
expected an unlimited direct completion parser and an actual bounded poll to
agree even after an unclosed Error Summary made more than 1 MiB of padding
parser-relevant. The production evidence cap correctly refused completion as
indeterminate. This is a conservative documented refusal, not a product defect.
The exact 1,048,849-byte fixture is `initial-cap-case.log`, SHA256
`88901330334a18ab2c4eeb818b4ebb2ad365f718c3bfd5f1e210b925cd08e872`.
`initial-campaign-disposition.json` records the failed auxiliary assumption.
No preceding in-memory comparisons from that interrupted campaign are counted
as passing evidence. No test assertion, production cap or safety gate was
weakened. No signal or cancellation was sent to this campaign.

The corrected `differential-matrix.py` uses 65,536-byte records including LF,
retains all short raw/projected records, authenticates exact large fixtures,
and tests the intentional evidence-cap refusal separately. All source versions
and the failed run are preserved. The broader existing runner suite uses
`run-focused.py` and will record its exact selected module list/JUnit/status.

## Adjacent independent source review

The primary agent requested a source-only second opinion on its AudioWorker
launch-error candidate and event-only probe. `audio_jobs.py` explicitly promises
one bounded worker. A RuntimeError after a thread has started currently drops
`self._thread`, allowing the surviving rejected target to enter `_run` and
compete with a subsequent accepted worker. The proposed probe uses the same
accepted fault model as existing `test_power_monitor_launch_pass8.py` and
`test_sound_reaper_pass8.py`. No independent runtime probe was run here; the
primary agent owns proof, any repair and its regression module. A launch
accepted/decided gate must prevent the rejected target from entering `_run`,
including idle retirement that could otherwise clear a newer worker handle.

All runtime work is fake-only and serialized by the primary agent. No native
engine/inventory, physical device/USB, power/firmware, VM/loop/passthrough,
external network/service, hosted CI, staging, commit, push or publication is
part of this review. Prior SIGTERM/timing attribution and separate ISO/native/
hardware qualification remain unresolved outside this bounded review.
