# Beamo Wipe: tenth comprehensive local audit

Two independently reproduced lifecycle defects are repaired on baseline
`7047dfb8c22d0b17faad2d5de1ec470b2debfaac`, branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21, America/Chicago.
The final complete local gate records **11,714 unique Python passes**
(11,713 main plus one separate Orca case), **28 unchanged unverified skips**,
zero failures/errors and zero Python warnings. Every one of the prior 11,703
main test IDs remains; exactly 38 new cases were added. Separate Go, models,
focused subsets and supplemental browser results are not added to that total.
[Machine summary](final-summary.json).

## Verified defects and repairs

| Trigger and observed baseline consequence | Result after repair | Exact new baseline proof |
| --- | --- | --- |
| An initial proc read fails with OSError, so public startup takes the unowned path. A later command-line or mount-table read raises UnicodeDecodeError outside the initial-only refusal handler. Startup exits with an uncaught exception instead of its existing blocked exit and message. | The existing UnicodeError handler also covers dispatch on the unowned path. Initial and later undecodable metadata return blocked status 3 without dispatching a session. Owned-store cleanup, informational exits and ordinary readable metadata preserve their behavior. | 16 failures, 22 passing controls |
| Desktop Close acknowledges closure without revoking the plan or request admission. An already-decoding request can still invoke a restart/check callback using the old revision. The idle ticker likewise caches a decision after unlocking, leaving an admission window before exit. | Session authority retires under the same mutex used for action admission: the plan is consumed, revision advances, readiness is withdrawn and later API requests are refused. Close retires before unlocking or writing/flushing its response; idle expiry checks age/busy state and retires atomically. Busy actions retain ownership. | 18 failing Go scenarios, six passing controls |

Root independently reproduced both defects before editing. The startup proof
uses real public controller/classifier code with owned proc-file substitutes;
the reviewer independently uses a read() I/O failure followed by actual
TextIOWrapper UTF-8 decoding. Both retain two failures/two owned-live controls.
All eight original Python cases pass after repair. The 38 exact new cases
cover later override/admission reads, two malformed byte sequences, command-line
and unrelated mountpoint decoding, preview/web flags, owned-live controls,
readable Unicode metadata, and help/version/invalid-argument exits. The strict
integrated startup/recovery/interface subset passes 249 unique cases.

The launcher defect is reproduced by actual HTTP handlers with fake callbacks,
including a request paused at final JSON EOF and a close response paused during
Flush. Root separately reproduced post-close restart/check admission. Exact
final Go regression bytes were archived and independently replayed against
unchanged baseline main.go: 18 failing leaves/six controls, zero data races.
All 24 leaves and four parent tests pass after repair, adding 28 named Go pass
events. All original external handler probes pass as well. The idle baseline
trace replays the exact old ticker statements and demonstrates its unlocked
admission window, retaining one failure/one busy control; it is clearly marked
as a historical scheduling trace rather than a final-source model.

No real firmware, restart, device or engine action was performed. These findings
do not demonstrate a bypass of the separate owner/token/countdown/Erase-now
gates. Launchers continue to perform no erasure. Disk selection, nwipe flags,
methods, Windows manual restart policy and pinned versions are unchanged.

## Source and verification integrity

Only two product files change: the public startup exception boundary in app.py,
and terminal launcher admission/idle retirement in desktop/main.go. One Python
and one Go regression module are new. **Every existing test file is byte-identical**,
preserving all old assertions. All **820 frozen source, test, build and packaging
inputs** verify. Root read the complete product diffs, both new modules, proof
traces and all reviewer models before final checks. No frozen source changed
during final verification.

Configured syntax, shell/security/full lint, developer-tool formatting,
default mypy (52 source files), preview and private negative safety mutation
pass. The existing literal-pattern TODO notice and mypy untyped-body notes are
unchanged notices, not Python test warnings. Test and desktop doctors pass.
Fresh uncached Go race results contain **366 named passes**, including the 28
new events, and two explicit native skips. All 340 prior named Go outcomes
(338 passes/two skips) remain unchanged. Vet, 350,000 fuzz executions, Windows
test cross-compilation and Windows/Linux launcher cross-builds pass.

Final phases run serially inside one unprivileged development container, with
child-only umask 022 and private 72-DPI display/session contexts. Root inspected
the generated PE32+/ELF64 x86_64 headers, source identity, bundle/source digest,
hashes and executable modes without executing native launchers. The actual
fake-disk Tk welcome screen was visually inspected after painting and closed
through its registered WM_DELETE_WINDOW callback with exit 0. Its screenshot
stays outside Git; hash and inspection receipt are retained. Nine unchanged
supplemental browser assertions pass under explicit system Chromium 155;
this does not qualify the missing pinned Playwright runtime.

## Five bounded reviews and independent model replays

Reviews covered discovery/safety, runner/progress/verification, wizard and all
consent interfaces, recovery/logs/export/privacy, and launcher/boot/build/developer
tooling. Root independently replayed all five fresh models on frozen source;
Python scripts are exact copies and the Go model changes only its metrics path:

- Typed boot-source identity: 3,360 states, strict resolver results, parsed
  results and public fake discoveries. Strict policy has 1,488 positive/1,872
  refusal controls; injected preview policy has 1,584 positive/1,776 refusals.
  Includes 96 missing-link policy distinctions and 3,072 selectable observations.
- Completion log snapshots: 384 states, 36 positive completions/348 refusals,
  240 cut-head controls and 48 concurrent append scans bounded to the original
  snapshot. Replacement, truncation, symlink/FIFO and record-size boundaries
  are exercised only on owned regular fixtures.
- Refresh/authorization generations: 405 scenarios, 720 refresh claims, 225
  invalid refusals, 855 stale and 135 duplicate completions ignored, 45 empty
  controls, 315 clean retries, 5,715 blocked Erase calls and 405 explicit
  DryRunRunner starts after fresh owner/token/countdown authorization.
- Report bundle readback: 24 positive bundles/content manifests, 1,680 tamper
  refusals with 1,680 restored positive rechecks, 24 duplicate-session refusals
  and 24 extra-file refusals. All COMPLETE content markers retain
  safe_to_remove=false; this is not physical FAT32/remount qualification.
- Launcher retirement: 216 fake-clock/API states, 24 new idle retirements,
  72 busy-preservation controls, 72 preclosed idempotence controls, 96 post-
  retirement API refusals and 96 repeat retirements. Positive controls include
  12 ordinary checks, 12 closes, four fake restarts and four previews.

All models retain positive controls and finish with zero mismatches/native
callbacks. They are supporting evidence, not extra canonical tests or native
qualification. Fresh focused reviewer results are discovery 2,401 passes/six
historical browser skips; runner/engine/evidence 1,643; UI 272; recovery 1,063;
boot/developer 255. These overlap the full gate and are never summed into a
larger unique coverage number. No additional verified defect was promoted.

## Retained history and qualification limits

The discovery review first ran a mixed GUI subset without X, retaining one
GTK failure/two Tk skips. Its unchanged tests pass under private 72-DPI Xvfb.
The recovery subset first inherited host umask 0077: a fixture's requested
0755 directory was already 0700 before product code. That record retains
1,062 passes/one fixture failure. The same assertions pass all 1,063 cases
under child-only umask 022. Neither is a product defect or passing final gate.

The runner model's first all-green aligned-tail implementation is retained;
its final version strengthens coverage with 240 cut-head controls. The Go
candidate histories retain formatting, direct retirement-assertion and
Windows manual-policy fixture refinements. Exact final bytes are replayed on
archived baseline source and pass after repair. Every old test stays intact.
No failed/canceled setup is counted as final coverage. The full canonical
sequence completes once on the final source freeze.

All 28 previous skips retain exact IDs/reasons: 14 image/artifact cases,
nine pinned-browser cases, four Microsoft-document reachability checks and
one legacy gcloud check. Go's two native inventory/platform skips remain open.
Pinned browser/network checks, ISO/KVM, actual nwipe/device behavior, native
Windows execution, firmware and physical USB/reconnect acceptance remain
unverified. Local development readiness does not establish complete release
qualification.

Blacksmith remains the current hosted provider. No GCP/hosted gate, remote
write, PR, merge, release, actual engine/device/mount/firmware/power or guest
operation occurred. Publication remains pending the earlier automatic approval
review that rejected operational-backlog metadata export as internal data;
no remote-write retry or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass10/verify_retained.py` to verify
the frozen inputs, every retained hash, unique current/prior Python and Go
outcomes, unchanged skip reasons and old test bytes, exact baseline failures,
new regressions and separate model results. Original workspace paths are
bound by commit/hash receipts. The retained candidate launcher receipt has
baseline HEAD/source_dirty=true. Clean launchers are rebuilt after the local
commit; exact commit/build identity remains outside Git to avoid self-reference.
Remaining qualification and publication actions stay in the canonical backlog.
