# Beamo Wipe bug audit — 2026-10-16, pass12

Six new defects are proved and fixed locally. **Final applicable local gates pass: 6618 unique passed tests,14 unchanged image-only skips, 0 failures/errors/xfails.** Nothing is staged, committed, pushed, published or deployed. Historical acceptance blockers and separate hardware/image qualification remain open.

## Exact source

- Repository/worktree: `BeamoTech/beamo-wipe`, `/root/dev/Beamo Wipe`.
- Branch: `fix/safety-audit-20261015`; HEAD: `35107a8d1a701093eac876a58ab4efd50e291673`.
- Final runtime source SHA256: `2033156897c47190995f47499a87c761e4d9c7bc7a1124d0bafd91722ab3ec31`.
- All 738 starting inputs matched pass11. Final 742 source/test/build inputs are frozen in [source-freeze.json](primary/source-freeze.json). Prior fixes and nine regression modules are preserved. This pass changes five application modules, adds four regression modules, and updates two existing test fixtures to supply native screen sizes and GTK APIs.
- [source-review.json](primary/source-review.json), compressed complete source patch, exact incremental pass12 patch, tracked fixture patch and all 13 uncommitted test-module bytes are retained. HEAD alone does not identify this dirty source.

## Proven fixes

| ID | Original behavior and proof | Minimal repair |
| --- | --- | --- |
| P12-1 | Timestamp/level-prefixed Error Summary target errors or malformed counts could be ignored, accepting a later Erased row despite explicit disk errors. Original runner101 cases:67 intended failures,34 controls. | Normalize negative row/column/delimiter classification consistently with its header. Raw records and exact positive completion provenance stay intact. |
| P12-2 | Refused remembered Headphones restore still selected Headphones although Speakers was the actual default; clicking Headphones again could not retry. | Resolve actual default/fallback after refusal, retain the saved preference until a choice succeeds. |
| P12-3 | Variable sound content grew below 800x600: with 8 outputs, WORKING dialog560x764; modal Stop y621 and Close y750. | Scroll variable content, bound initial placement to monitor workarea, keep Stop and Close outside scrolling content. |
| P12-4 | Bare-X11 Tk startup ignored native Escape with pointer outside the window. Inside-pointer controls worked. | Give the mapped startup window native input focus through its idle callback. |
| P12-5 | Tk PlaceWindow centered an empty requested200px window, overriding configured geometry. Fullscreen1600x1000 moved to+700+400; windowed640x440 at+300+200 overflowed800x600. | Place configured window dimensions explicitly; fullscreen stays at0,0 and windowed startup centers within the screen. |
| P12-6 | Tk and GTK cleared the stall notice one100ms frame after displaying it. | Request persistent graphical state while retaining default one-shot console/serial behavior; clear on new stage or terminal state. |

Product edits are confined to `nwipe_runner.py`, `startup_stages.py`, `ui/sound_dialog.py`, `ui/tk_wizard.py` and `ui/accessible_wizard.py`. Discovery, target selection, argv, method mapping, owner/token/countdown gates, engine pin, claims and publication configuration are unchanged by this pass.

## Independent reproduction and focused checks

The primary restored all 58 exact starting application/static files only in a private import tree and ran the final 200 new cases. Result: **135 intended failures /65 passing controls,0 errors/skips**,24.66s. Shared source was never reverted. [Independent proof](primary/original-independent-review.json) separates runner67/34, sound52/26, stall8/3 and Tk8/2. The initial runner proof also exists independently in the runner evidence.

| Check | Completed evidence |
| --- | --- |
| Discovery/authorization |461 PASS/0 skips plus 1455 fresh fake mutations, boot-source combinations, equivalent representations and token combinations; zero native acquisition attempts. |
| Runner/engine adjacency |372 PASS/0 skips, including 101 new cases; focused Ruff passes. |
| Primary report/export/power/audio baseline |328 PASS/0 skips. |
| Evidence/report integration |90 cases across 3 methods,3 languages,5 count variants and 2 log sizes.72 failed outcomes remain failures; checks, exact log bytes/hashes, owner/share views and 90 bundle manifests agree.70 representative generated files retained in an authenticated archive. |
| UI/startup |All 99 new cases pass in selected adjacency; actual 800x600 selection88 PASS. Initial adjacency348 PASS/2 fixture failures; corrected affected TK-GC module5 PASS. |
| Native visuals |Six unedited full-root captures at800x600/1600x1000,72DPI, independently viewed by primary and UI reviewer. Bounds, native focus, dimensions, bytes and teardown verified. |

Focused counts overlap the final gate and are not summed as unique test coverage. [Screenshot review](primary/screenshot-review.json), [UI details](ui/README.md), [runner details](runner/README.md), [discovery details](discovery/README.md), and independent exact-hash source reviews retain scope and proof. Reviewed peer-arrival and manual renamed-engine hypotheses did not establish supported-path defects; no speculative fixes were made.

## Retained failed/setup history

- The first full gate completed 6611 PASS/6 FAIL/14 expected skips (592.36s), plus separate Orca1 PASS (68.21s). All 200 new cases passed and all 742 frozen hashes matched. Every failure came from missing display/monitor/scroller APIs in the headless FakeGtk test double. Only fake API behavior was updated, retaining widget-thread checks and every timing/cancellation/outcome assertion; affected full audio module19 PASS/0 skips. Independent review confirms all 18 test/helper function ASTs are identical and the thread guard is preserved. Complete first-gate evidence is retained under `primary/initial-gate-*`. The later frozen full gate passes separately; this first run remains a failed gate.
- Initial UI adjacent campaign had two TypeErrors in an existing MagicMock cleanup fixture, before its deliberately injected startup exception. Tk returns integer screen dimensions; only 1600/1000 mock inputs were added. Both original exception/destroy assertions remain unchanged; affected module subsequently 5 PASS. Initial failure logs/JUnit and exact original fixture are retained.
- Initial primary matrix incorrectly expected a passing zero-error advisory under a prefixed positive banner. The existing raw exact 80-character banner guard correctly returned unavailable. Matrix expectation was corrected, product guard unchanged; final 90-case checks and generated bundle assertions pass.
- Discovery's initial postprocessing dimension estimate was wrong; all 1455 matrix assertions had passed. Exact corrected Cartesian counts510+180+36+729 and the failed auxiliary count assumption are retained. No test assertion or product code was weakened.
- Initial Tk pointer labels and wall-timer stall captures were imprecise. Corrected native rectangles/pointer booleans and deterministic post-render frames supersede them; original artifacts remain available.

## Final applicable local gate

All 9 phases pass against frozen 742 inputs: lint/types/security/shell, fake preview, negative safety, Go1.26.8 version/race/vet, Windows AMD64 test cross-compilation,350000 counted fuzz cases, and full pytest in canonical separate private Orca/main 72DPI sessions. Existing pinned tools were used without installations or hosted jobs.

- Main:6617 PASS/14 unchanged expected image-only skips,512.33s.
- Separate Orca:1 PASS,61.02s.
- Combined:6618 uniquePASS,0 failures/errors/xfails/duplicate IDs. All 200 new and 215 retained pass8/pass10/pass11 cases pass. The unchanged sound timing case passes.
- All 742 frozen hashes match; every prior input except the five authorized source files and two fixture updates is unchanged. Source patch, tracked fixture patch and 13 uncommitted test-module archive match live bytes; index empty.
- Windows test artifact is an actual8,974,848-byte PE32+ AMD64 binary; SHA256 `6f58501de27f93649fe59e6ff2a84b4a089639a9b9ecb12fa2951ec8297f5089`. Cross-compilation is not native Windows acceptance; binary stays outside git.
- Final-source 90-case report/bundle matrix rerun passes with runtime SHA matching the final freeze.70 generated files and manifests were independently authenticated. Earlier pre-final-source outputs remain labeled separately. Generated fake preview HTML is retained compressed and hashed.

[Final summary](primary/final-summary.json), [phase commands/exits](primary/local-gate-status.json), [artifact review](primary/artifact-review.json), main/Orca JUnit and exact logs are retained. The14 skips are the same two generated live-build config checks and twelve image/manufacturing-dependent checks as pass11, with exact IDs/reasons compared. No pending/canceled/timed-out check is counted as a pass.

## Remaining acceptance and authority

Historical pass8 SIGTERM at06:29UTC (exit143) still lacks attributable sender/cause; the owner answered “No, not knowingly” to cancellation. Pass9 timing misses still lack attributable failing traces. Passing later runs cannot establish either historical cause. Acceptance/commit/push remain pending under the original exhaustive task requirement; next action is platform execution/signal evidence and an attributable timing trace. No new unresolved product finding is claimed from the bounded reviews.

ISO/QEMU, native Windows, real-device, firmware and physical reconnect acceptance remain **NOT RUN / BLOCKED** in the existing separate qualification record. No host disks, physical USBs, host power/firmware settings, real engine, native inventory, VM, hosted CI, external messages or release were used. Current AGENTS.md governs; shared `/root/dev/AGENTS.md` is still absent and the existing recorded owner continuation applies. [Canonical unfinished work](../../../.ai/memory/unfinished-work.md) owns pending acceptance and publication steps. Notes and evidence grant no additional authority.

Exact original transcripts are retained in `original-transcripts.tar.gz` with hashes; readable copies normalize only trailing transcript whitespace. Native PNGs, JSON, XML and source snapshots retain exact bytes. `artifacts-sha256.txt` authenticates the retained final set.

Final retention validation passes:742 frozen inputs,13 exact uncommitted test modules,194 exact original artifacts, matching source/fixture patches, empty git index and clean diff whitespace. The final manifest authenticates198 retained artifacts (excluding itself). The initial validation receipt is retained; the final manifest includes that receipt.
