# Unfinished work

## BW-BUG-AUDIT-20261016-PASS11 — IN PROGRESS

- Date/author: 2026-10-16 / Codex. Request: another comprehensive bug audit.
- Repo/worktree/branch: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`;
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Starting source includes six verified pass8/pass10 fixes and six regression
  modules, all uncommitted, plus prior evidence. Preserve all. Acceptance:
  fresh bounded review, original failure proof before any minimal fix,
  independent validation, final applicable local gates and exact artifacts.
- Scope: three bounded discovery/safety, runner/recovery and UI/boot/build
  reviewers; primary report/export/privacy/diagnostic/integration review.
  Source reviews may overlap; substantial tests/GUI/CPU jobs run sequentially.
- Exact next action: verify current735-input baseline against pass10 receipt,
  establish a focused local baseline, inspect new edge cases, prove findings.
- Checkpoint: all735 starting hashes match pass10; empty index. Primary
  report/export/diagnostic baseline173PASS. Discovery461PASS/0skip on private
  72DPI Xvfb plus588 fake inventory matrix cases; no new discovery bug. Initial
  discovery selection lacked DISPLAY (458PASS/1setupFAIL/2skips); identical
  selection corrected461PASS, original retained. Reviewers' substantial jobs
  remain serialized; UI owns current native-input proof slot.
- New UI defect proved by native XTest on private display: parent Return press
  opens sound modal, release is received by modal but parent held set remains;
  first fresh Return after close is swallowed, its release rearms, next works.
  Trace `/tmp/pass11-ui/native-modal-release-trace.json`; no fix yet. Exact next
  action: original regressions, independent validation, observe actual release
  through existing handler without weakening held-key/autorepeat safeguards.
- Runner candidate awaiting proof: prefixed Erasure Summary rows are normalized
  by engine_checks but dropped by large-log projection, potentially losing a
  hidden-capacity warning. Startup native focus also under investigation.
- Three findings now proved: UI final14 original cases6intendedFAIL/8controls;
  native Return/KPEnter release/freshpress failures and startup Escape ignored
  with pointer outside mapped window (windowed/fullscreen). Minimal UI fix:
  connect only modal key releases to existing handler; present/nativefocus
  startup before childfocus. Held/repeat/countdown logic unchanged.
  Runner10 actualpoll traces prove three large-only advisory mismatches;
  original81 regressions25intendedFAIL/56controls,0errors/skips. Approved fix
  normalizes relevance/context decisions only, preserving exact raw records
  and terminal proof rules. Runner owns current focused-test slot; UI waits.
- Next: finish affected checks, independent exact-start-source reproduction
  and source review, freeze final source, run applicable full local gates.
- Three-fix checkpoint: runner268PASS/0skip (81new included), UI114PASS/0skip
  (14new included), Ruff/diff checks PASS; all jobs retired. Primary independent
  exact-starting58source-hash proof95cases31intendedFAIL/64controls,0errors/skips.
  Fixed native input traces show real release reaches ledger, first fresh Enter
  works, startup nativefocus matches window and Escape closes without rescue.
- Fourth finding: native fullscreen flag True but actual main900x700/startup
  640x420 allocations stay identical to windowed controls on1600x1000 bareX11.
  Kiosk has no WM to honor request. Exact geometry trace retained under UI;
  minimal explicit monitor geometry sizing/positioning approved only after new
  failing regressions. Preserve windowed workarea behavior. UI owns current
  bounded geometry/test/artifact slot; final full gate has not started.
- Four-fix checkpoint: original geometry8 at1600:4FAIL/4controls; at800:
  3FAIL/5controls. Fixed UI final122PASS/0skip plus geometry8PASS at800.
  Four actual72DPI root screenshots inspected independently by primary/reviewer;
  full monitor filled, Owner footer and startup status inside viewport. Geometry
  fix changes only fullscreen requested sizing/origin; windowed paths preserved.
  All reviewers approve exact final source/tests; no agent jobs/writes pending.
- Primary final original-source proof:58source/static hashes match starting
  snapshot,103newcases35intendedFAIL/68controls,0errors/skips (14.15s).
  Private source copy only; shared source never reverted. Report/evidence
  integration72-case matrix running; next freeze738inputs and full local gate.
- Matrix72PASS: actual fake-process runner→evidence→owner HTML/text/sharing
  outcome checks across3methods/3languages/four summary variants/both log sizes;
  full advisory payloads, exact log-tail hashes and unchanged log bytes match.
  Source738 inputs frozen; runtimeSHA
  `70382edd3f47fba150187014901200bb35c1f76f46a74b4fc35f4fd327a8fb01`.
  Final8-phase local gate active under owned execsession17630; no auxiliary
  test/GUI/CPU jobs alongside. Exact next action: await every phase, parse
  JUnit/expected14 skips/new103+retained112 cases, verify hashes/artifacts and
  save durable evidence. No further source changes planned.
- Existing blockers: historical pass8 SIGTERM sender/cause and pass9 timing
  attribution remain unavailable. New passes cannot establish their causes.
  Shared `/root/dev/AGENTS.md` still absent; prior owner continue resolution
  recorded, current local audit proceeds within project guide boundaries.
- State: local only; no staging/commit/push/PR/hosted CI/merge/release or real
  engine/device/USB/power/firmware/guest operation. Native/ISO/physical
  qualification remains the separate NOT RUN record. Evidence destination:
  `docs/evidence/bug-audit-20261016-pass11/README.md`.
