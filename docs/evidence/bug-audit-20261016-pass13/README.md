# Beamo Wipe bug audit — 2026-10-16, pass13

Three new defects are proved and fixed locally. **Final applicable local gates pass:6783 unique passed tests,14 unchanged image-only skips,0 failures/errors/xfails.** Final-source report/bundle checks pass. Changes remain local and uncommitted; historical acceptance blockers and separate image/native/hardware qualification remain open. Durable retention verification passes below.

## Exact source and scope

- Repository/worktree: `BeamoTech/beamo-wipe`, `/root/dev/Beamo Wipe`.
- Branch: `fix/safety-audit-20261015`; HEAD: `35107a8d1a701093eac876a58ab4efd50e291673`.
- Final aggregate runtime source SHA256: `e7efbba20755ff7496533504259adb4ef63eb8fafc43b52fa6fabe148cf1297d`.
- All742 pass12 final starting inputs matched. Final744 source/test/build inputs are frozen in [source-freeze.json](primary/source-freeze.json). Sixteen prior fixes,415 regression cases, two fixture updates and earlier evidence are preserved. This pass changes only `discover.py` and `ui/tk_wizard.py`, adding two modules/165 regression cases.
- [source-review.json](primary/source-review.json) records the aggregate identity; exact complete and incremental source patches, unchanged prior tracked-test fixture patch and all15 uncommitted regression modules are retained. HEAD alone does not identify this dirty source.

Fresh bounded reviews covered discovery/classification/boot ownership and exclusion, hardware identity, selection/authorization/countdown/method/argv, runner/progress/log projection/cancellation/recovery, Tk/GTK/curses/startup/kiosk/build/desktop boundaries, reports/export/privacy/evidence and power/audio ownership. Three delegated reviewers and primary independently validated findings; substantial auxiliary runtime campaigns were serialized. Candidate dispositions are retained, without speculative product changes.

## Proven fixes

| ID | Original behavior and proof | Minimal repair |
| --- | --- | --- |
| P13-1 | PARTLABEL/PARTTYPENAME such as Benefits or Definitions contains `efi` and falsely gives NTFS data disks Windows-removal guidance, or ext4 data disks system-removal guidance. The initial16-case trace has8 false classifications and8 genuine controls; final104 original-source cases have32 intended failures/72 controls. | Recognize EFI/UEFI name tokens, retaining exact firmware labels, ESP/type GUIDs and independent Windows/BitLocker evidence. Every case verifies unchanged boot exclusion, target identity and token128. |
| P13-2 | Windowed bare-X11 Tk ignores the first native key when the pointer is outside. Initial child-focus requests occur before root mapping and are ignored. | Claim native input once after actual root Map, then let the existing renderer restore screen-specific focus. Remove the one-shot binding before posting the claim; already-mapped run uses one idle claim. Later redraws retain existing focus behavior. |
| P13-3 | Mouse wheel over general body prose never reaches canvas/inner bindings. Actual hit-tested XTest input leaves yview unchanged; canvas controls work. | Route through the root bindtag only for current body descendants. Preserve native readers/nested scroll surfaces/custom scrollbars, footer, picker, focus and consent state; remove old bindings to prevent double movement. |

No eligibility, boot exclusion, hardware identity, token, countdown, owner authorization, method/argv, engine pin, claims or publication behavior changes. The discovery edit requires a future `safety:` commit under AGENTS; no commit is made while acceptance is blocked.

## Independent proof and focused checks

Primary privately restored all58 exact starting source/static files, checked every hash and ran the final165 new cases: **60 intended failures/105 passing controls,0 errors/skips**,15.252s. Classification32/72; UI28/33. Every failure is an intended product assertion, including actual native keys/wheel and initial screen focus. Shared source was never reverted. [Independent original review](primary/original-independent-review.json) retains IDs and failure provenance.

| Check | Completed evidence |
| --- | --- |
| Primary report/export/power/audio baseline |733PASS/0skips across40modules. |
| Classifier and discovery/safety adjacency |104newPASS;644adjacentPASS/0skips across54modules.156 fresh fake namespace/mount/RO/duplicate/identity mutations pass, zero native acquisition attempts. |
| Runner/progress/recovery |686PASS/0skips across58modules.216 fresh large-log cases,648 actual fake-process terminal polls: full/projection outcomes and advisory checks agree, exact log bytes unchanged. |
| UI/startup/console/kiosk |61newPASS/0skips,17.195s;630adjacentPASS/0skips across27modules,120.512s. New controls cover actual first key, mapped/unmapped initial screens, held Return, exact review deadline, prose scroll direction, nested native scrollers, redraw/picker, focus and consent. |
| Evidence/report integration |90final-source cases across3methods/3languages/5count variants/2log sizes; outcome/check/owner/share/log-hash/bundle-manifest agreement.70representative generated files authenticated; five actual JSON/result-text/HTML/share bundles independently inspected. |
| Native artifacts |Two unedited private72DPI full-root captures independently viewed; bytes/dimensions/geometry/focus/native hit/yview/owner false/token empty/no request/owned teardown verified.800x600 root has800x600 window at0,0;1600x1000 root has800x600 window at400,200. |

Counts overlap the final gate and must not be summed as unique coverage. [Focused receipts](primary/focused-receipts.json), [primary review](primary/review-notes.md), [discovery review](discovery/review-notes.md), [runner review](runner/README.md), [UI review](ui/README.md), [independent final Tk review](discovery/ui-independent-review-round2.md), [primary source review](primary/independent-source-review.json) and [screenshot review](primary/screenshot-review.json) retain exact scope and hashes.

Nested whole-disk topology did not establish a violated supported contract; mounted ancestry closures worked, and no speculative blanket rejection was added. Authenticated-suffix recovery remains deliberately conservative. Semantically equivalent Unicode round/pass digits did not establish a supported logger/provenance defect; malformed controls and method contradictions remain refusals. Other bounded reviews found no additional proved defect.

## Failed/setup history retained separately

- Original native UI campaign10cases had4 intended failures,5 passing controls and1 incorrect test setup assuming an uncovered canvas gutter. Hit-testing showed a label covers it. Corrected9-case original proof has4 intended failures/5 controls,0 errors/skips. Exact variants and both logs/XML remain retained.
- First fixed UI53:42PASS/11FAIL,12.707s. Nine failures exposed an incomplete idle-before-map focus repair. Constructor/firstidle/nestedidle trace mapped0/focusNone/lastroot; actual Map occurs later. Corrected Map→idle→native claim→renderer trace restores intended child. Two failures were new footer fixtures mixing pack/grid; only their parent changed, assertions preserved. Corrected53PASS, then expanded61PASS. The earlier source-only approval is explicitly superseded by exact-hash round2 approval.
- Primary auxiliary original-review parser first assumed optional JUnit `type`, then a fixed error-message prefix. The actual pytest traceback identifies AssertionError in its last line. Both parser versions/failure explanations remain retained; final review checks that explicit exception type and intended IDs. Original XML, product source and test assertions were unchanged.
- Auxiliary artifact review assumed SUMMARY.txt; the actual authenticated bundle uses RESULT.txt. Archive entries/schema were inspected and the review corrected, without changing generated bytes or product behavior. The failure explanation remains retained.
- UI handoff originally labeled a Tk file hash as runtime source hash; the label now distinguishes per-file from aggregate digest. Original note retained. Native images remain untouched.

## Final local gate and artifacts

All9phases pass against the744 frozen inputs: lint/types/security/shell, fake preview, negative safety, pinnedGo1.26.8 version/uncached race/vet, WindowsAMD64 test cross-build,350000 counted fuzz executions, and full pytest in canonical separate private Orca/main72DPI sessions. Existing tools were used without installations or hosted jobs; no auxiliary runtime campaign overlapped final pytest.

- Main:6782PASS/14expected image-only skips,551.25s. Separate Orca:1PASS,60.06s.
- Combined:6783uniquePASS,0failures/errors/xfails/duplicateIDs. All165new+415retained regressions pass; the unchanged sound timing case passes.
- Exact14skipIDs/reasons matchpass12: two generated live-build config checks, twelve absent manufacturing-ISO checks. Skips are not passes or native/image acceptance.
- All744frozenhashes match; every prior input except the two authorized source files is unchanged. Complete/incremental source and prior fixture patches match; all15uncommitted test modules retained with exact bytes. Index empty.
- Actual Windows test artifact:PE32+AMD64,8,974,848bytes,SHA256`6f58501de27f93649fe59e6ff2a84b4a089639a9b9ecb12fa2951ec8297f5089`. Cross-compilation only; native acceptancefalse, binary outsidegit.
- Final-source90case report matrix passes with aggregate runtime hash matching freeze.70files/manifests authenticated. Generated fakepreview HTML185,540bytes,SHA256`5492d76fb06bee55066b55cc305c66bd6149514d3367456337f045032f752880`, retained compressed; supported-language JavaScript syntax checked by preview gate.

[Final summary](primary/final-summary.json), [phase commands/exits](primary/local-gate-status.json), [artifact review](primary/artifact-review.json), exact main/Orca JUnit and logs retain proof. No pending/canceled/timed-out check is counted passing. No required applicable local check remains unrun; historical acceptance remains blocked.

## Remaining acceptance and boundaries

Historical pass8 SIGTERM at06:29UTC (exit143) still lacks attributable sender/cause; owner answered “No, not knowingly” to cancellation. Pass9 failed timing attribution remains unavailable. Later passing checks cannot establish either cause. Acceptance/commit/push remain pending; next action is platform execution/signal evidence and an attributable failed timing trace, then acceptance revalidation.

ISO/QEMU/nativeWindows/real-device/firmware/physical reconnect qualification remains separately **NOT RUN / BLOCKED** in the existing qualification record. No native engine/inventory/device/USB, power/firmware, VM/loop/passthrough, hostedCI, credential access, external-network/container work or external messaging was used. Controlled local test servers are fixture-only. Current AGENTS governs; shared `/root/dev/AGENTS.md` remains absent and recorded owner continuation applies. [Canonical unfinished work](../../../.ai/memory/unfinished-work.md) owns acceptance and pending source/publication steps; notes grant no additional authority.

Final retention verification passes:744 frozen inputs,15exact uncommitted test modules,137exact original artifacts, matching source/fixture patches, empty index and clean diff whitespace. Exact originals are retained in `original-transcripts.tar.gz` with hashes. Readable transcript copies normalize only trailing text whitespace; PNG/JSON/XML/Python/source snapshots preserve exact bytes. The final `artifacts-sha256.txt` authenticates141retained artifacts, excluding itself. The initial verification receipt is retained at [retention-verification.json](primary/retention-verification.json); the final manifest includes that receipt.
