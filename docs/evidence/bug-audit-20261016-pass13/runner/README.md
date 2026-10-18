# Pass13 runner, progress, engine-check and recovery review

2026-10-16 / Codex subagent `/root/pass13_runner`.
Repository `/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`,
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`. The shared starting
application source and prior uncommitted fixes were preserved.

## Outcome

No additional supported product defect was proved in this bounded review.
No application file or repository test was edited. This is a scoped review
result, not evidence that all possible defects are absent.

Source review covered runner startup/reset and duplicate-start ownership,
pinned-engine validation and concurrent-engine probes, method-bound arguments,
pre-exec identity/lock/log checks, uncertain fork ownership, progress read
ordering and partial records, terminal projection caps/context/order,
negative evidence versus positive Drive Status provenance, stop/poll races,
process status failures, cleanup failures and retry eligibility. It also
covered progress clocks/freshness/stages/estimates, advisory error/hidden-area
checks, and same-boot journal validation, locking, atomic saves, recovery
identity/time evidence, quiescence, new-session rotation and descriptor cleanup.

Seven source files were hashed before and after the review. All seven match;
the exact hashes are in `source-review-start.json` and the unchanged result in
`summary.json`.

## Completed fake-only runtime checks

All runtime campaigns were serialized with the primary agent's explicit slot.

- `focused-selection.txt` identifies 58 existing runner/nwipe/progress/engine
  and session/recovery modules. `run-focused.py` used the existing pinned
  audit virtualenv with dry-run set, live mode removed and native inventory
  unset. JUnit records **686 passed, zero failures/errors/skips**, exit 0;
  exact elapsed time 67.652598 seconds. Logs/XML/status are `focused.txt`,
  `focused.xml`, `focused-status.json` and `summary.json`.
- `projection-matrix.py` generated 216 ordinary temporary fake logs, each
  greater than the 1 MiB terminal-scan threshold, with bounded filler records.
  It varied three device/status-column shapes, three record prefixes, six
  clean/error/malformed/overflow count forms, and four complete/shortfall/
  malformed/conflicting Erasure Summary forms. Full-log and projected
  completion decisions agree for all three methods; all advisory payloads
  agree. **648 actual terminal fake-process polls agree** with their full-log
  decisions and checks. Every fixture remained byte-identical after reading.
  `projection-matrix.json` retains all 216 fixture SHA256 values, lengths,
  inputs, statuses and decisions; `projection-matrix.txt` records zero defects.
- `numeric-format-probe.py` records ten tiny formatting controls. Exact ASCII
  terminal evidence succeeds; Unicode percentage/ETA, unterminated records,
  mismatched pass counts, truncated phase and numeric suffixes do not succeed.
  Arabic-Indic round/pass digits with the same numerical values are accepted.
  That permissiveness was not classified as a supported product bug: the
  pinned C logger emits ASCII counters and this review established no actual
  supported path that emits those records or circumvents existing provenance.
  No source change was made on the hypothesis. The exact outcomes and
  disposition are retained in `numeric-format-probe.json` and `.txt`.

No failed test or harness correction occurred in this review. The broader
58-module selection took longer than the initial estimated duration; the
primary agent was informed while the process was still actively CPU-bound,
and all owned jobs exited normally before the runtime slot was released.

## Reviewed conservative boundaries

- Recovery independently rechecks the exact authenticated log suffix. A
  successful whole-log assessment whose positive evidence is absent from
  that suffix can recover as indeterminate; this is the explicit conservative
  recovery contract, not a proved defect or an excuse to reconstruct success.
- Missing or incomplete completion evidence, uncertain process ownership,
  replaced locks/logs and unsuccessful cleanup remain blocked rather than
  being converted into completion or a retry.

No pinned engine, native discovery/inventory, physical disk/USB, firmware,
host power operation, VM, network service, hosted CI or publication was
invoked. Fake device paths were inert strings; all log files were ordinary
private temporary files. No staging, commit, push or canonical project
memory/report modification was performed by this subagent.

The primary agent owns independent validation, the final full local gate,
durable project evidence and the historical acceptance blockers. Prior
SIGTERM/timing attribution and separate ISO/native/hardware qualification
remain outside the proof provided here.
