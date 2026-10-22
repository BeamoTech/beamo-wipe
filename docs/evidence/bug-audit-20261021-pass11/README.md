# Beamo Wipe: eleventh comprehensive local audit

Three independently reproduced defects are repaired on baseline
`b46e5642d4c849d503b41d8bf562cfb1f9fad68b`, branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21, America/Chicago.
The completed local gate records **11,770 unique Python passes**
(11,769 main plus one separate Orca case), **28 unchanged unverified skips**,
zero failures/errors and zero Python warnings. Every prior main test ID is
retained; exactly 56 cases were added. Go, focused subsets, model states and
supplemental browser results are counted separately. [Machine summary](final-summary.json).

## Verified defects and repairs

| Trigger and observed baseline behavior | Result after repair | Independent proof |
| --- | --- | --- |
| A direct launcher helper exits or is canceled while a descendant retains stdout or stderr. `exec.Cmd.Run` waits for pipe-copy goroutines after the process deadline, potentially indefinitely; an exited parent can eventually return success after that deadline. | `boundedOutput` caps pipe draining at 100 ms after parent exit/context cancellation, preserving stricter positive caller limits. Incomplete captures return an error. This bounds capture, and does not claim process-tree termination. | Three inherited-pipe failures, two normal/direct-cancellation controls. A distinct reviewer probe also fails only its inherited-pipe case. |
| The output limiter embeds `bytes.Buffer`, inheriting `ReadFrom`. Go's optimized `io.Copy` uses that method and bypasses the limiter's `Write`. Actual commands return oversized bytes with no error. | A named buffer field removes the inherited fast path. Every copy goes through the existing byte-budget check. Empty, exact-limit, chunked and failed-command behavior remains tested. | Four oversized-capture failures and three at/below-limit controls, including 65,536 accepted bytes under a 1,024-byte cap before repair. |
| A diagnostic raises KeyboardInterrupt/SystemExit while the optional sleep inhibitor is unavailable or cannot stop. Logging interrupts required startup or confirmed engine retirement, leaving the terminal result and descriptor release unfinished. | Only the two optional diagnostic boundaries contain BaseException. Real process-control interruptions still propagate; an uncertain engine or helper remains owned. | Six independent failures/six controls across direct start, stop and actual runner cancellation. A separate reviewer terminal-poll proof has two failures/two controls. |

Root reproduced every original finding before authorizing its product edit,
read the complete final diffs and regression modules, then independently
replayed the exact final tests on archived baseline source. The 56 Python
cases produce **18 failures/38 passing controls** before repair and all pass
afterward. The 47 Go scenarios produce **17 failing leaves/30 passing controls**
before repair and all pass afterward, yielding 52 named pass events including
four scenario parents and one helper entry. All 16 original Python probes and
18 named original Go probe outcomes pass on the final freeze.

The Python cases cover unavailable-helper start, stop/recheck, poll/cancel
classification, real owned temporary lock/log descriptors, uncertain liveness,
replacement refusal, desktop/dry-run no-ops, normal cleanup and genuine control
interruptions. Go cases exercise stdout/stderr/both, cancellation and parent
exit, stricter caller delay, empty/exact/oversized output at zero, one-byte,
1 KiB and 1 MiB budgets, one-shot/37-byte writes, failed exit, absent executable,
pre-cancellation, direct cancellation and descendants that release their pipes.
Only finite owned helpers were run; completion receipts track the Go fixtures.

## Source and completed checks

Only `desktop/io.go` and `src/beamo_wipe/sleep_inhibit.py` change in product
code. One new Python and one new Go regression module are added.
**Every existing test file is byte-identical**, preserving all old assertions.
All **822 frozen source/test/build/packaging inputs** match their recorded
hashes. The 11,741 prior main Python IDs remain; exactly 56 new IDs are present.
The 28 skip IDs and reasons are unchanged. Source stayed frozen during checks.

Configured compilation, shell checks, blocking Ruff/security/format checks,
default mypy (52 source files), preview, private negative safety mutation and
test/desktop doctors pass. Existing mypy untyped-body notes and the literal
TODO-pattern notice are unchanged notices, not Python test warnings. Fresh
uncached Go race results contain **418 named passes** and two unchanged native
skips. All 368 prior named Go outcomes remain; exactly 52 pass events are new.
Vet, 350,000 fuzz executions, Windows test cross-compilation and Windows/Linux
launcher cross-builds pass.

Checks run serially in one unprivileged development container, with child-only
umask 022 and private 72-DPI display/session contexts. Independent artifact
inspection checks PE32+/ELF64 x86_64 headers, bundle/source identity, hashes and
executable modes without executing native launchers. The actual fake-device Tk
welcome screen was visually inspected after painting and closed through its
registered WM_DELETE_WINDOW callback with exit 0. The screenshot stays outside
Git; its hash and inspection receipt are retained. Nine unchanged supplemental
browser cases pass under explicit system Chromium 155; this does not qualify
the missing pinned Playwright runtime.

## Five bounded reviews and independent replays

Root read and independently replayed all five fresh models on frozen source.
The four Python scripts are exact copies; the Go model changes only its metrics
output path. Every model retains positive controls and zero mismatches/native
callbacks:

- Protected aliases/capacity: 2,880 states through three actual parser/discovery
  routes, 8,640 calls; 2,592 positive leaf observations, 4,320 protected-alias
  refusals and 1,728 read-only/capacity refusals. Covers ineligible bridge rows,
  mount ancestry, contrary WWNs, placeholders and half-up decimal size edges.
- Runner cancellation: 216 states across methods, terminal evidence and fake
  process outcomes; 24 initial positive completions, 78 negative terminal
  results, 66 cancellations, 48 uncertain-ownership retentions with 48 recovery
  classifications, and 216 duplicate terminal-call controls.
- Consent/layout detours: 360 review plus 63 layout scenarios, 720 composed
  detours, 975 fresh countdown checks, 3,132 blocked Erase calls, 423 explicit
  DryRunRunner starts and 423 expiry ticks without automatic start.
- Volatile persistence: 240 actual-store transactions, 30 positive/210 injected
  refusals, 120 precommit byte-preservation checks, 90 retained postcommit
  records, 54 uncertain-journal write refusals, 240 reopens/retries and 144
  quiescent controls. Owned regular files establish content behavior only.
- Launcher plans: 162 positive states, 162 partition-order and 162 unrelated-
  entry invariance controls, 161 fingerprint distinctions, 1,620 refusal
  transitions and 1,620 restored positive checks using fake EFI snapshots.

Focused reviewer results: discovery 2,598 passes/six unchanged browser skips;
runner 1,744; UI 444; recovery 1,512 disjoint passes (1,063 focused/449 adjacent);
boot/developer 464 passes/one historical gcloud skip. These overlap the complete
gate and are never added to canonical unique coverage. Other suspicions did
not establish an additional defect and were not promoted into product edits.

## History and remaining qualification

Histories are retained separately: the first runner model had incorrect
no-signal expectations for a duplicate fake mode; its final 216 distinct states
preserve controls. Recovery first ran an adjacent subset without X and retained
447 passes/two Tk skips; unchanged tests pass all 449 cases at private 72 DPI.
The UI first passed 444 cases with a shared AT-SPI cache diagnostic; an unchanged
isolated runtime/cache run is clean. UI model histories retain later expiry-tick
and fake-metadata coverage improvements. Go histories retain formatting,
expanded boundary fixtures and the intermediate WaitDelay-only repair with the
still-failing output-size case. No history is counted as final passing coverage.
The complete canonical final sequence finishes once on the final source freeze.

All 28 prior Python skips remain unverified: 14 generated image/artifact cases,
nine pinned-browser cases, four Microsoft-document reachability checks and one
legacy gcloud check. Go's two native inventory/platform skips also remain open.
Pinned-browser/network, ISO/KVM, actual nwipe/device behavior, native Windows,
firmware and physical USB/reconnect qualification remain unverified. Local
development checks do not establish complete release qualification.

Blacksmith remains the current hosted provider. No GCP/hosted gate, remote
write, PR, merge, release, real engine/device/mount/firmware/power or guest action
occurred. Publication remains pending the earlier automatic approval review
that rejected operational-backlog metadata export as internal data; no retry
or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass11/verify_retained.py` to verify
frozen inputs, every retained hash, old test bytes, current/prior unique Python
and Go outcomes, unchanged skip reasons, exact baseline failures, regressions
and separate models. Original workspace paths are bound by hash/commit receipts.
The retained candidate launcher receipt has baseline HEAD/source_dirty=true.
Clean launchers are rebuilt after the local commit; exact commit/build identity
stays outside Git to avoid self-reference. Remaining actions are recorded in
the canonical unfinished-work backlog.
