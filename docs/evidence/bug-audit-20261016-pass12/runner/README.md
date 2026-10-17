# Pass12 runner review

Scope: nwipe_runner.py, progress.py, engine_checks.py, session_recovery.py and relevant evidence/recovery call paths. Source-only review covered launch ownership, duplicate starts, pre-exec lock/log identity, status polling, progress reads, stop/cancel state transitions, scanner caps/order, full/projection parsing, report checks and recovery lifecycle. One new root cause was proved; no claim that bounded review proves all bugs absent.

## Proven negative-error parsing defect

`_target_error_summary_conflict` normalized Error Summary headers but read target columns, count rows and closing delimiters from raw records. A timestamp/level-prefixed nonzero or malformed target error row could therefore be ignored; a later genuine Erased row was accepted as completion. Advisory parsing already recognized marked prefixed count rows. The proof shows a completed verdict alongside `io_media=fail`. Headerless errors, no-erase claims, shared status cells and prefixed closing delimiters exposed the same classification inconsistency.

- Exact starting source: `nwipe_runner-before.py`, SHA256 `10dddb6380568da269e2a773f0c2250e947d206985ac6cbb275456ef6c587943`.
- Initial pure-parser trace: `parser-original-proof.json` uses normal blank-leading rows; prefixed advisory rows are unavailable because prefix normalization consumes the marker blank. `prefixed-error-original-proof.json` uses the engine error-row `!` marker and shows explicit completed/fail disagreement.
- Initial system Python probe failed before app import: `ModuleNotFoundError: No module named 'beamo_wipe'`. Corrected invocation used `PYTHONPATH=src`; no product source had changed.
- Regression module: `tests/test_runner_prefixed_error_context_pass12.py` (101 cases). Before product edits: 67 intended failures, 34 passing controls, 0 errors/skips, 1.425s (`original.txt`, `original.xml`). Cases cover all methods/count categories, malformed rows, zero/foreign controls, small/large actual fake-process poll and late Stop, headerless/shared contexts, no-erase contradictions, prefixed close, model phrases, exact 1MiB boundary ±1 and CR Drive Status provenance.
- Approved minimal source edit normalizes negative-error record bodies for column/count/delimiter classification only. Raw records, exact positive Drive Status provenance, launch command, methods, parser caps and old pass8/pass10/pass11 fixes remain intact.
- Fixed verification: 372 passed, 0 failures/errors/skips in 11.582s across the exact 16-module `fixed-selection.txt`, including all 101 new cases (`fixed-adjacent.txt`, `.xml`, `.exit`; `fixed-summary.json`). Ruff source/new-test check passed (`ruff.txt`, `.exit`). Final runner SHA256 `7672c9c0646aa9679b87d9b729c3f9228f0cf1b7f9bb4b1c162a7e37e16dbf9b`; new regression SHA256 `a115e79460175e0697c3f95ea1713aa4f64bdd5ae090b8f4126671a2ef1f7d9e`. Primary independent review/full gate remain separate.

All device paths are inert strings and all logs ordinary temporary files. No pinned engine, discovery, physical media, firmware/power operation, hosted CI, network or VM was invoked. No staging, commit, push or canonical memory/report edit by this subagent.

## Additional build/startup review

Read-only review covered live entrypoint environment clearing, startx/curses recovery, kiosk power guard, systemd tmpfs/network/sleep boundaries, pinned nwipe hook, tracked-source/asset staging, ISO output ownership and rollback, Go launcher manual-Windows/direct-Linux boundaries, CI phase/required-job semantics and separate protected publication/transfer/source pinning. No additional defect was proved; no build, workflow, launcher or kiosk file was edited.

Kiosk source `packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk` uses `pgrep -x nwipe` to guard power requests. Primary reviewed the alternate-hardlink-basename candidate: the supported entrypoint always invokes `/usr/lib/beamo-wipe/nwipe`; the current guide forbids renaming nwipe. This is a reviewed scope boundary, not a proved product bug. Existing recovery tests require pgrep rc0/uncertain/missing to block power and rc1 only to permit the confirmed request. The shell recovery surface cannot identify disks or start an erase. No extra kiosk/native process was executed here.
