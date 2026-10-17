# Superseded pass17 checkpoints

Retained verbatim before the final result entry. Pending statements below describe earlier states; final README and receipts supersede them.

## BW-BUG-AUDIT-20261017-PASS17 — IN PROGRESS (fresh audit; previous acceptance blockers retained)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive pass.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Baseline: 754 source/test/build inputs exactly match final pass16 freeze;
  all previous uncommitted fixes/tests preserved; index empty.
- Work: three bounded source audits (discovery/safety, runner/recovery,
  UI/boot/build), primary harness isolation and reports/audio/power review.
- Checkpoint: baseline1,943PASS/0skips. Three proved fixes implemented locally
  (inherited identity ambiguity, model-LF no-erase log origin, startup Tcl timer
  retirement); final stable826 new regressions pass. Original proof discovery
  176FAIL/186controls, runner250FAIL/198controls, startup10FAIL/6controls; zero
  errors/skips. Earlier396-case runner proof preserved separately from final448.
- Fourth bug fixed: canonical PTY ERASE queued while disabled started fake
  runner at5.2s without fresh action. Corrected proof9FAIL/9controls; original
  fixture15FAIL/3PASS retained (12method-reauthorization setup failures). No
  assertion weakened. Four modules now859cases;859new+2adjacentPASS. TTY must
  be canonical and flush successfully; real nonTTY refuses, fake inputs retained.
- First758-input candidate runtimeSHA256
  `1124345bbf564a4613012c659133ae49fc918278b9e72d86380d7a981f42f931`: first8
  phasesPASS; full main8,821PASS/3FAIL/14skips plus1OrcaPASS. Three old runner
  regressions expose changed contradictory-evidence reason(engine_failed vs
  requiredindeterminate); fix negative-only raw-guard handling, preserve tests.
  This candidate is FAILED, all exactlogs/manifests retained in candidate-one/.
- Final-review bridge defect proved:200-case injected probe48FAIL/152controls
  noerrors/skips; unresolved physical candidate facts can hide a protected alias
  bridge. Proposed parser-local targeted refusal retains valid candidates without
  repairing target identity or changing WWN alias policy. Product patch pending.
  Extra32 duplicate probe had24fixture/controlFAIL/8PASS because ancestor shape
  was rejected before intended boundary; investigate/correct fixture, retain raw.
- Further source review found lost malformed-WWN uncertainty:48-case proof
  16FAIL/32controls. Private context now preserves malformedWWN as an unknown
  alternative; valid contrary candidates cannot erase it. Explicit parent
  WWN authority remains. Source-only peers approved exact corrected bytes.
- Final source:762 frozen inputs; runtimeSHA256
  `b4e76a50ff6e9d376b6a56f7d1b469192dd4284347923ac1aca02254664bf423`.
  Eight newmodules1,247cases; previous25modules1,763cases preserved.
  All32then-existing auditmodules+5adjacent2,967cases passed before last48-case correction;
  final642discovery cases pass. Private starting-source replay of final1,235
  high-level cases gives496AssertionErrorFAIL/739controls,0errors/skips;12
  newhelper-only controls omitted from oldsource replay, required in finalgate.
  Corrected duplicate32 all pass on original source, proving initial candidate
  introduced that regression; failed candidate and raw fixtures retained.
- Exact next action: finalninephase gate running, then serial fresh fake
  runner/cancellation/report/geometry campaigns, artifactreadback and finalreview.
  No substantive auxiliary runtime overlaps canonical main/Orca phase.
- Finalization checkpoint: final lint first reported two F811 imported-fixture
  annotations in the new duplicate/WWN modules. Exact failed lint and pre-comment
  inputs retained. Standard inline fixture comments correct only those notices;
  peer AST/assertion equivalence verified. Runtime bytes unchanged. Refrozen
  source and repeated private original replay again496FAIL/739controls. The
  restarted first8 phases pass; full main/Orca is active, not yet a pass.
- Gate completion: all9 local phases exit0; authenticated9,213PASS/14same
  image-onlyskips,0errors/failures/duplicates. All3,010 retained regressions in
  33modules pass, includingall1,247newcases. Source762unchanged. Go1.26.8
  race/vet/350,000fuzz and actualPE32+AMD64crossbuild pass; nativeWindows unrun.
  Result review initially caught one trailing documentation space; removed,
  failed review saved, exact same runtime inputs reauthenticated successfully.
  Zero forbiddenfallbacks;3 actual permittedSDKcalls only list owned localfiles.
  Serial fresh runner/cancel/geometry/report campaigns are now active.
- Remaining local acceptance: full applicable local gate, serial final fake
  campaigns and source/artifact readback. All four fixes and focused checks are
  complete. Use no-space interpreter
  and rejecting child-PATH guards; current forbidden fallbacks zero.
- Blockers retained: pass16 loop-test boundary incident review, pass8 original
  unexplained SIGTERM and pass9 original timing trace. ISO/QEMU/native Windows/
  physical/firmware acceptance remain NOT RUN/BLOCKED on this host.
- Interpreter/guard probes already pass; no forbidden fallback so far. No
  commit/push/hosted job/release has occurred; historical acceptance remains open.
- Evidence/result in progress: `docs/evidence/bug-audit-20261017-pass17/`;
  `/tmp/pass17-primary/` is working staging, retained before handoff.



