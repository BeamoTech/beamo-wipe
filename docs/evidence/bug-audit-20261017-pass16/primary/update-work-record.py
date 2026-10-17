"""Checkpoint final local results while preserving blocked acceptance/history."""
import json
from pathlib import Path

root=Path.cwd();out=Path('/tmp/pass16-primary')
assert json.loads((out/'retention-verification.json').read_text())['frozen_inputs_match']==754
s=json.loads((out/'final-summary.json').read_text())
p=root/'.ai/memory/unfinished-work.md';old=p.read_text()
start=old.index('## BW-BUG-AUDIT-20261017-PASS16')
end=old.index('\n## BW-BUG-AUDIT-20261016-PASS15',start)
entry=f'''## BW-BUG-AUDIT-20261017-PASS16 — BLOCKED (four bugs fixed locally; gates pass; incident and historical acceptance review pending)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive audit pass.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD
  `35107a8d1a701093eac876a58ab4efd50e291673`.
- Outcome: four independently proved bug classes fixed in discover.py and
  ui/tk_wizard.py / ui/accessible_wizard.py: filtered physical duplicates could
  manufacture target uniqueness; optical cmdline fallback omitted physical
  competition; modal held Escape became a fresh parent action; destroyed Tk
  widgets left queued Tcl callback commands. Three new modules add 398 cases.
  Preserve all 27 prior local fixes, 22 prior modules / 1,365 cases and earlier
  evidence. Retained/new regressions: 1,763 cases in 25 untracked modules.
- Four existing fixtures corrected without deleting any assertion: mapped-draw
  readiness retains the 140 ms interval; two AST fixtures bind the actual shared
  guard; Tcl-only picker models its leaf hierarchy. Original assertion counts
  38 / 19 / 9 / 11 preserved, one readiness assertion added. New native fixtures
  set geometry before mapping and distinguish real fresh key timestamps.
- Source: 754 inputs frozen, 744 of 751 starting inputs unchanged. Only three
  runtime files and four existing fixtures changed; three new test inputs.
  Runtime SHA256 `{s['runtime_source_sha256']}`.
  Exact source/fixture patches, starting archive, 25-module test archive and
  original/final receipts retained. Three source peers approved exact assigned
  final bytes; primary independently verified all 58 source/static hashes.
- Proof: exact private starting-source replay of final 398 cases gives
  203 AssertionError failures / 195 controls, zero errors/skips: discovery159,
  modal18, explicit Tcl-bgerror26. Shared source never restored. Native Escape
  and callback/default-bgerror traces independently support the defects.
- Completed final local gate: nine phase exits 0, 7,966 unique passes / 14 same
  image-only skips, no failure/error/xfail/duplicate IDs; every 398 new and 1,365
  prior regression passes. Fresh main/Orca reports, pinned Go1.26.8 uncached
  race/vet/350,000 fuzz executions, preview/negative and actual Windows PE32+
  AMD64 cross-build verified. Native Windows acceptance remains NOT RUN.
- Fresh final campaigns: 153 short and 153 actual >1MiB fake polls, 90 authenticated
  evidence/export-readiness/recovery roundtrips, 144 cancellation/retry cases,
  270 Tk/GTK layouts, 90 report cases all pass. Zero campaign native acquisitions
  or callback errors. All 153 large logs / 90 evidence-sidecar pairs (333 files),
  70 report files and five actual PNGs independently authenticated/viewed;
  27 critical Tk inputs fully visible. Exact readback/retention verification passes.
- Failed/corrected history is preserved in evidence and checkpoint-history.md:
  initial baseline 1,676PASS/7focusFAIL; initial adjacency2,073PASS/8new-fixtureFAIL;
  type gate2errors; private-display/observer setup corrections; full space-bearing
  interpreter run23FAIL/7,942PASS/14skips plus1OrcaPASS. Same existing interpreter
  through a no-space alias fixes Linux shebang execution; 23 exact failed cases
  pass after that and the accurate Tcl leaf fixture. No assertion weakened.
- Boundary incident: invalid fake executable shebangs fell through to real tools.
  Public metadata reads and ordinary-file xorriso work occurred. Three native
  regular-file loop probes returned0 and reported attachments/ownership-checked
  cleanup. Empty fake bookkeeping was initially misread as zero real loops; that
  statement is corrected. Original loop IDs were not retained. Read-only follow-up
  found no matching fixture backings or remaining probe-prefix directories; no
  detach performed. This crossed the allowed loop-test boundary. No wipe engine
  or physical disk target was invoked. Review incident before acceptance.
- Final test orchestration rejects remote/privileged fallback. The single allowed
  actual SDK call only lists local files under a canonical private pytest tree
  with fresh config; credentials/telemetry/update checks disabled. Installed SDK
  source and independent peer confirm this; 12 intercepted guard cases and the
  actual offline test pass. Final forbidden fallback attempts: zero. No hosted
  CI, login, credential entry, external messages, commit, push, PR or release.
- One overstrict guard run was intentionally canceled: exact owned pytestPID36787
  ignored SIGINT03:21:42.296955UTC (inherited background disposition); root sent
  SIGTERM03:22:25.187569UTC. Wrapperexit1, no fresh main JUnit; stale prior report
  rejected. Tracked pytest/child exited. This is fully attributed and distinct
  from historical pass8. No auxiliary runtime campaign overlapped final gate.
- Remaining acceptance: review this incident/guard evidence; obtain attributable
  platform execution/signal evidence for pass8's06:29UTC SIGTERM/exit143 and the
  unavailable original pass9 failed timing trace. Later passes cannot explain
  those historical events. Exact next action: obtain/reconcile those records,
  review the incident, revalidate acceptance, then make a `safety:` commit/push
  only when every required acceptance criterion passes. Source remains local,
  uncommitted, index empty. No release authorization.
- Separate final-public ISO/QEMU/native Windows/hardware/firmware/physical
  reconnect qualification remains NOT RUN/BLOCKED. Follow existing qualification
  records and current AGENTS; an isolated authorized worker is required.
- Evidence/result: `docs/evidence/bug-audit-20261017-pass16/README.md`.
  All intermediate checkpoints preserved in `primary/checkpoint-history.md`.

'''
p.write_text(old[:start]+entry+old[end:])
print('updated canonical pass16 result; acceptance remains BLOCKED')
