"""Write the final task handoff only from validated completed receipts."""
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

root = Path.cwd()
out = Path('/tmp/pass15-primary')
dest = root / 'docs/evidence/bug-audit-20261016-pass15'
read = lambda name: json.loads((out / name).read_text())
summary = read('final-summary.json')
source = read('source-review.json')
focused = read('focused-independent-review.json')
artifacts = read('artifact-review.json')
assert summary['combined_passed'] == 7568 and summary['combined_skipped'] == 14
assert summary['new_regression_cases_passed'] == 578 and summary['retained_prior_regressions_passed'] == 787
assert focused['native_application_effects'] == focused['callback_errors'] == 0
assert artifacts['report_files_hashed'] == 70 and artifacts['native_gui_captures_independently_viewed'] == 5
main = summary['reports']['final.xml']
orca = summary['reports']['final.xml.orca.xml']
runtime = source['runtime_source_sha256']
main_log = (out / 'final.txt').read_text()
timing = re.search(r'7567 passed, 14 skipped in ([0-9.]+)s', main_log)
assert timing
orca_time = ET.parse(out / 'final.xml.orca.xml').find('.//testsuite').get('time')
exe = summary['windows_crossbuild']
text = f'''# Beamo Wipe bug audit — 2026-10-16/17, pass15

Five additional bug classes are proved and fixed locally. **Final applicable local gates pass:7568 unique passed tests,14 unchanged image-only skips,0 failures/errors/xfails/duplicate IDs.** Final-source boundary checks, peer source reviews and generated artifacts pass. Changes remain local and uncommitted. Historical acceptance blockers and separate image/native/hardware qualification remain open.

## Source and scope

- Repository/worktree:`BeamoTech/beamo-wipe`, `/root/dev/Beamo Wipe`.
- Branch:`{source['branch']}`; HEAD:`{source['head']}`.
- Final aggregate runtime SHA256:`{runtime}`.
- Complete source patch SHA256:`{source['source_diff_sha256']}`; incremental pass15 patch:`{source['pass15_source_diff_sha256']}`.
- All747 starting inputs match pass14 evidence. Final751 inputs are frozen in [source-freeze.json](primary/source-freeze.json);740 starting inputs are byte-for-byte unchanged. Seven runtime files changed and four new modules add578 cases. All22 prior fixes,18 prior modules/787 cases, three existing fixture updates and earlier evidence are preserved. Total retained/new regressions:1365 in22 untracked modules.

HEAD alone does not identify these dirty bytes. [Source identity](primary/source-review.json), complete/incremental source patches, tracked fixture patch and exact22-module archive retain final inputs. No staging, commit, push, PR, hosted job or release occurred. Future discovery/safety commit must use `safety:` after acceptance.

Fresh bounded reviews covered discovery/classification/boot exclusion; selection/identity/authorization/countdown/method/argv; runner/progress/cancellation/recovery/logs; Tk/GTK/curses/startup/kiosk/build/desktop boundaries; report/export/privacy/evidence and power/audio. Three delegates supplied bounded reviews, controlled original proofs, prepared tests and exact final source approvals. Primary independently reproduced findings, chose repairs, inspected the complete diff and verified final hashes. Discovery's [final path-API review](discovery/final-source-review-path-api.md) supersedes its earlier approvals; [Tk approval](ui/exact-tk-review.md) and [runner/evidence/advisory approval](runner/patch-review.md) retain exact hashes. The runner review's older global discovery snapshot is not claimed as final approval; the latest discovery review covers that path. [Final code review](primary/final-code-review.json) authenticates the union.

All substantial auxiliary runtime campaigns were serialized. The canonical main/Orca gate uses its prescribed separate private72DPI displays, DBus and runtime directories. Shared displays:1/:99 were not modified. Fake devices/processes and ordinary fixture files only.

## Proven defects and repairs

| ID | Original behavior and proof | Repair and controls |
| --- | --- | --- |
| P15-1 | Hardware closure lost unmounted physical rows omitted by picker/display filtering. A protected serial-only path reaches an omitted serial+WWN bridge then a different-serial same-WWN target; reverse mixed chains also lose protection. Delegate240cases96violations/144controls; primary expanded288cases120violations/168controls including optical, hidden names/eMMC boot areas, overlong model/layout and all orders. Unsafe leaves pass identity/token and boot guard. | Retain safety-only physical facts before presentation filtering and include them in boot/mount closure and final boot guard. Never use context as selectable disks or token peers. Valid contrary anchor WWNs and unrelated controls remain eligible. Existing mounted full validation and malformed target omission are preserved.288 alias and72 final-guard regression cases cover visibility/order/anchor variants. |
| P15-2 | Malformed model/layout filtering hides a conflicting same-path RO,serial,WWN,size or bus observation. Primary36case trace20violations/16controls; original valid and mounted conflicts already refuse. A usable row remains selectable after the malformed conflicting row disappears. | Reconcile canonical same-path physical facts before display filtering, with tri-state RO and explicit invalid-ID bits. Refuse contradiction; invalid and missing IDs cannot compare equal. Existing parsed duplicate/unique-identity checks remain.36 duplicate,4 invalid-vs-missing, clean retry/pathless/child-fallback tests complete the404-case physical module. |
| P15-3 | Empty-screen recursive wheel binding replaces nested inventory Text/custom-scrollbar handlers, consumes the event and moves outer prose. Primary native XTest Button4/5 plus MouseWheel reproduces4empty failures/4picker controls; visible hit targets, unchanged focus/state and zero effects/errors. | Exactly six lines in empty-screen traversal preserve native/custom reader wheel ownership while ordinary prose keeps outer scrolling.64 regressions cover three layout/type profiles, both directions, native buttons vs synthetic MouseWheel, redraw, immutable read-only text, focus/state/request and custom scrollbar routing. Picker implementation remains unchanged this pass. |
| P15-4 | A valid original UTF8 log over1MiB can be cut inside a codepoint; replacement decoding makes its normalized snapshot exceed the raw1MiB bound. Runner/evidence says verified/completed but presentation/recovery says indeterminate and export readiness refuses. Independent30case trace18violations/12whole-codepoint controls. | Distinguish finite raw capture bytes from finite normalized UTF8 bytes:at most3×raw. Capture/assessment/hash/readback algorithms unchanged.38 tests include30valid boundary roundtrips,3actual near3×invalid UTF8 captures,5strict type/nonpositive/over-cap refusals, atomic evidence/checksum, recovery and authenticated export readiness. Quick zero remains unverified. |
| P15-5 | Timestamped positive hidden-storage regex accepts target prefix plus uncertainty,NUL or Unicode junk; slash+later target mention can also misattribute. Agent54parser traces and original72tests40intended failures/32controls prove the module-contract violation. Actual engine reachability is weaker; no erasure vulnerability is alleged. | Require the complete positive target record with ASCII horizontal spacing only. Negative/unknown/contradictory precedence remains.72 tests span three device families,42positive variants,12separate-negative controls and18actual small/large fake runner/evidence paths. Advisory status never rewrites completion or verification. |

No engine, method/argv, token, countdown, owner checkbox, explicit Erase action, claims, pins, launchers, build/publication or real power boundary changed this pass. No native inventory or engine was started and no real target was opened.

## Proof and focused verification

Primary privately restored58 exact starting source/static files, checked each hash and ran all final578 new tests:**298 intended failures/280 passing controls,0 errors/skips**. Physical205failures/199controls; UI32/32; hidden40/32; UTF821/17. Every failure is independently attributed:60 exact missing SafetyError failures and238 intended AssertionErrors. Shared source was never reverted. [Original review](primary/original-independent-review.json) records exact assertion provenance. Original intentionally failing proof is not counted as a gate pass.

| Check | Completed evidence |
| --- | --- |
| Fresh baseline |45modules1105PASS/0skip, including retained regressions, before edits. |
| Adjacent behavior |106modules2275PASS/0skip on the refined discovery design; later direct malformed-path correction is covered by473focused and final full gate. Exact paths/commands/JUnit/logs retained. |
| Malformed-path correction |Five existing/new modules473PASS/0skip, including the original failing direct parser case, all404physical cases and overlong/layout/control metadata. |
| Final fake discovery |288alias +36duplicate cases PASS,0native attempts; source hashes match final freeze. Contradictory and unrelated controls retained. |
| Final native wheel |8original trace cases allPASS with XTest buttons and synthetic MouseWheel, visible hit tests and no state/focus/native effects/callback errors. All64regressions also pass in the full gate. |
| Final UTF8 roundtrip |30valid original log cases preserve runner/presentation/recovery/export agreement.10exact raw fixtures authenticated; raw bytes remain unchanged. Final ordinary logs/evidence/sidecars archived. |
| Final runner projection/Stop |432short full/projection cases +324actual >1MiB natural-poll/late-Stop/running-Stop cases PASS.108exact large fixtures authenticated; terminal reasons and retired fake process/lock/log handles checked,0mismatches/native acquisitions. |
| Final native geometry |270PASS:Tk+GTK×3languages×3text sizes×15screens at800×600/72DPI.27critical Tk typing/owner/confirmation controls fully visible, state unchanged,0effects/callback errors/Traceback/bgerror. Five final native PNGs independently viewed. |
| Final report/artifact integration |90cases across3methods/3languages/5count variants/2log sizes. Owner/share/check/outcome/log bytes and COMPLETE manifests agree;70actual bundle files authenticated; five representative JSON/result-text/HTML/share bundles independently inspected. |

Counts overlap full tests and are not summed as unique coverage. [Primary review](primary/review-notes.md), [focused review](primary/focused-independent-review.json) and delegated notes retain bounded scope and rejected speculative candidates. Exit0 alone never substitutes for checked outcomes.

## Failed and corrected history

- Initial final new modules574cases on exact original source:294intendedFAIL/280controls. Four missing-vs-invalid duplicate controls were added after adjacency refinement; final578original replay has298/280. Tests never import the new bound constant, avoiding missing-symbol proof failures.
- First repair574check542PASS/32UIFAIL exposed patch placed in the similarly named picker helper. Restored picker bytes and moved only the guard into empty helper; corrected574PASS. Initial source/script/log/XML and placement note retained.
- First106module adjacency2271cases2264PASS/7FAIL exposed whole-inventory early refusal for malformed unmounted serial/WWN, changing existing recognized-boot/per-row-skip contracts. Safety-only fieldwise extraction keeps valid other ID plus explicit invalidity, while full target/mounted validation remains. Added4meaningful duplicate invalid-ID controls; final2275PASS. Initial mypy also caught tuple/Disk local-name collision; renamed previous_physical. No ignore or assertion relaxation.
- First full final gate main7566PASS/1FAIL/14unchanged skips, Orca1PASS. Existing direct malformed-path parse case caught early node_path ValueError. Narrow catch now returns a fresh empty unidentified DiscoveryResult/IDENTIFY_ERROR, never repairs a path or drops ambiguous facts while authorizing peers. Mounted full validation remains before that catch.473focusedPASS, fresh final boundary campaigns and all9gate phases rerun; latest source approval covers exact correction. All original failed gate/freezes/logs/XML preserved under before-path-api-fix names. This introduced-and-corrected regression is not a sixth original finding.
- Initial baseline selection glob included an unrelated tracked pass15-suffix module; manifest-based selection corrected before tests started. First duplicate probe lacked its sibling fixture import; stopped before product code, exact dependency copied. Initial path-focused command named a nonexistent module (exit4,no tests); corrected selection then473PASS. Setup failures are not test passes.
- First fresh driver incorrectly demanded read status complete for >1MiB source logs. Product campaign had exit0 and exact successful outcomes; correct status is tail. Corrected only the receipt assertion and revalidated existing outputs. Final repeated campaign also passes. No source/test/gate change.
- Configured lint/security/type checks pass. Existing annotation-unchecked notes remain. TODO warning matches the deliberate PLACEHOLDER_RE validation regex in unchanged release_manifest.py, not unfinished work; no suppression added. No stop/kill or unexplained process termination occurred this pass.

## Final gate and actual artifacts

All9 phases exit0 on final751 frozen inputs:lint/types/security/shell; fake preview; negative safety; pinnedGo1.26.8 version, uncached race, vet, WindowsAMD64 test cross-build and350000counted fuzz executions; canonical full main/Orca pytest on separate private72DPI sessions. No installations, hosted jobs or auxiliary runtime campaign alongside full pytest.

- Main:{main['passed']}PASS/14expected image-only skips;{timing.group(1)}s in console. Separate Orca:{orca['passed']}PASS/0skip;{orca_time}s JUnit.
- Combined:7568uniquePASS,0failure/error/xfail/duplicateID. All578new and787retained regressions pass. The unchanged sound timing case passes; this does not explain the historical failed timing.
- Exact14skip IDs/reasons match pass14:two generated live-build config checks and twelve absent manufacturing-ISO checks. They remain unpassed and provide no image/native acceptance.
-751final hashes match;740otherstartinginputs unchanged. Complete/incremental source and tracked fixture patches match,22untracked modules retained exactly,index empty,diff whitespace check passes.

[Final summary](primary/final-summary.json), [phase commands/exits](primary/local-gate-status.json), exact main/Orca JUnit and logs retain proof. No pending, canceled, stopped or failed check is labeled passed.

The Windows artifact is actual {exe['format']},{exe['size_bytes']:,}bytes,SHA256`{exe['sha256']}`. It is a test cross-build,native acceptancefalse,binary outsidegit. Generated fake-preview HTML is{artifacts['preview_size_bytes']:,}bytes,SHA256`{artifacts['preview_sha256']}`, retained compressed. Preview gate checks supported-language JavaScript syntax.90report cases use the exact final runtime hash;70actual bundle files/COMPLETE hashes authenticate. [Artifact review](primary/artifact-review.json) and focused review retain proof.

## Remaining acceptance and next action

Historical pass8 SIGTERM at06:29UTC/exit143 lacks attributable sender/cause; owner answered “No, not knowingly” to cancellation. Pass9 failed timing attribution remains unavailable. Later passing tests cannot establish either cause. **Acceptance/commit/push remain blocked.** Next action:obtain platform execution/signal evidence and an attributable failed timing trace, then revalidate acceptance before a `safety:` commit/push. This audit does not invent attribution or turn unavailable evidence into a pass.

Separate public-candidate ISO/QEMU/nativeWindows/real-device/firmware/physical reconnect qualification remains **NOT RUN / BLOCKED** in existing records. Current AGENTS reserves hosted qualification for a final public candidate; no hosted run or production publication was requested or performed. No physical disk/USB,power/firmware,guest/loop/passthrough,credential or external-message operation. Shared ~/dev/AGENTS.md remains absent; recorded owner continuation applies. The [canonical unfinished record](../../../.ai/memory/unfinished-work.md) owns remaining acceptance/publication steps. Notes grant no authority.

Final exact originals and their SHA256 records are retained in original-transcripts.tar.gz. Readable transcripts normalize trailing whitespace only; PNG/JSON/XML/Python/source snapshots preserve exact bytes. Final artifacts-sha256.txt authenticates retained files excluding itself. Retention counts and source/index/diff verification are recorded in primary/retention-verification.json; that initial receipt necessarily predates its own retention. Final retention verification is reported separately with actual counts.
'''
(dest / 'README.md').write_text(text)

record = root / '.ai/memory/unfinished-work.md'
old = record.read_text()
(out / 'unfinished-work-before-final-handoff.md').write_text(old)
start = old.index('## BW-BUG-AUDIT-20261016-PASS15')
end = old.index('## BW-BUG-AUDIT-20261016-PASS14')
entry = f'''## BW-BUG-AUDIT-20261016-PASS15 — BLOCKED (five new bugs fixed; final local gates pass; historical acceptance evidence pending)

- Date/author:2026-10-16/17 / Codex. Request:another comprehensive pass.
- Repo/worktree:BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  branch `{source['branch']}`; HEAD `{source['head']}`.
- Outcome:five proved classes fixed in7runtime files:omitted physical alias
  bridges, filtered same-path contradictions, empty-screen nested wheel routing,
  normalizedUTF8snapshot cap, exact positive hidden-storage advisory records.
 578newcases in4modules;787priorcases/22priorfixes/threefixtures preserved.
 1365retained/newregressions in22untrackedmodules. Safety-only context never
  selectable or a confirmation peer; no method/argv/token/countdown/owner/pins/
  claims/launcher/build/publication change. Future commit requires safety:.
- Final source:751frozeninputs,740otherstartinginputs unchanged; runtimeSHA256
  `{runtime}`. Complete/incremental patches,
  exact22testmodulearchive, original58sourcearchive and receipts retained.
  Three source peers approved assigned final bytes; latest discovery path-API
  review supersedes earlier snapshots. Primary independently inspected union.
- Proof:private original578cases298intendedFAIL/280controls,0errors/skips,
  all58startinghashesverified;60missingSafetyError/238AssertionErrors individually
  attributed. Fresh baseline1105PASS; adjacency2275PASS; malformed-path focused
 473PASS. Final alias288,duplicate36,wheel8,UTF8roundtrip30,runner432short+
 324large,geometry270,report90PASS;0nativeeffects/callbackerrors,27critical
  controlsfullyvisible,5nativePNGviewed,108large+10UTF8fixturesauthenticated.
- Failed/corrected history retained:initial UI guard placed in picker (542/574),
  moved to empty; early malformedID refusal(2264/2271), refined per-field safety
  context+4controls; first full main7566PASS/1FAIL/14skips caught direct invalid
  path exception, now returns fully empty unidentified result.473focused and
  allfinalcampaigns/gates repeated on newfreeze. Setup/import/selection and
  tail-vs-complete receipt mistakes distinguished; no relaxed tests/gates,
  stop/kill or unexplained termination this pass.
- Final applicable local gate:9phasesexit0,7568uniquePASS/14sameimage-onlyskips,
 0fail/error/xfail/duplicateID;578new+787priorPASS. PinnedGo1.26.8race/vet/
 350000fuzzPASS,actualWindowsPEcrossbuild inspected(nativenotrun),preview and
 70actualbundlefilesauthenticated. No auxiliaryruntimecampaignoverlap.
- State:local/uncommitted/indexempty;no commit/push/PR/hostedCI/release. All
  actualeffects fake/regularfiles/ownedprivateX11DBus. Evidence:
  `docs/evidence/bug-audit-20261016-pass15/README.md`; exactdetail/checkpointhistory
  retained there. Retention verification must pass before ending.
- Remaining acceptance:pass8 SIGTERM sender/cause and pass9 failed timing
  attribution still unavailable; laterPASS cannot explain. Exact next action:
  obtain platformexecution/signal evidence and attributable failedtimingtrace,
  revalidate acceptance,then safety:commit/push when allrequiredgates satisfied.
  Separate final-public ISO/QEMU/nativeWindows/hardware/firmware/reconnect
  qualification NOT RUN/BLOCKED; follow existing qualification record and
  currentAGENTS;productionrelease requires separate explicitauthorization.

'''
record.write_text(old[:start] + entry + old[end:])
print('Final evidence and canonical handoff written from validated receipts.')
