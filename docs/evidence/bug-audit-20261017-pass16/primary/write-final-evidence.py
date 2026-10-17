"""Write the durable outcome only after authenticated final receipts exist."""
import json
from pathlib import Path

root=Path.cwd(); out=Path('/tmp/pass16-primary')
dest=root/'docs/evidence/bug-audit-20261017-pass16'
s=json.loads((out/'final-summary.json').read_text())
c=json.loads((out/'campaign-verification.json').read_text())
a=json.loads((out/'artifact-review.json').read_text())
assert s['combined_passed']==7966 and s['combined_skipped']==14
assert c['geometry_cases']==270 and c['runner_actual_large']==153
assert a['native_gui_captures_independently_viewed']==5
runtime=s['runtime_source_sha256']
text=f'''# Beamo Wipe bug audit — 2026-10-17, pass16

Four independently proved bugs are fixed locally, with398 new regression cases.
All applicable local gates pass. Overall acceptance remains **BLOCKED** pending
review of the failed test-launch boundary incident and historical pass8
signal/pass9 failed-timing attribution; later passing checks
cannot explain those original events. Separate image/native/physical release
qualification remains NOT RUN/BLOCKED. No commit, push, PR, hosted job or release.

Repository: BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`.
Branch: `fix/safety-audit-20261015`.
HEAD: `35107a8d1a701093eac876a58ab4efd50e291673`.
Final runtimeSHA256: `{runtime}`.
Freeze of 754 inputs: [source-freeze.json](primary/source-freeze.json).
744of751starting inputs remain unchanged; only three runtime files and four
existing fixtures changed. The27prior local bug fixes,22prior modules/1365cases
and earlier evidence are preserved; retained/new regressions total1763cases in
25untracked modules. The index remains empty. Eventual commit requires`safety:`.

## Verified defects and repairs

| ID/status | Original evidence and resulting repair |
| --- | --- |
| P16-1 / locally fixed | A malformed duplicate physical observation could be filtered away, leaving one apparently unique target despite contrary valid display/layout metadata. Track repeated canonical physical paths before filtering and refuse when exactly one selectable row survives. Complete identical target duplicates stay two; boot/RO duplicates and unrelated malformed rows retain their contracts. |
| P16-2 / locally fixed | Kernel-command-line optical boot identity bypassed competition with other physical media; disk hits also omitted competing ROMs. Both hit and competition checks now include whole disk/ROM observations. Authoritative live mounts still precede fallback; zero-size competitors stay noncompeting. |
| P16-3 / locally fixed | A modal Escape key-down was absent from parent hold tracking, so auto-repeat after dialog closure became a separate parent navigation/Stop action. Modal and parent presses share the original guard bookkeeping; modal presses never dispatch parent navigation. Release and same-timestamp repeat semantics remain conservative. |
| P16-4 / locally fixed | Redraw or teardown deleted widget-owned Tcl callback commands while their after/idle events stayed queued, producing invalid-command errors. Cancel only exact Python callback scripts owned by the retiring subtree, through the actual owner. Persistent container/root jobs survive redraw; full root jobs retire on teardown; peer interpreters remain untouched. |

Incremental repairs: [pass16-source.diff](primary/pass16-source.diff).
Accumulated source patch: [source.diff.gz](primary/source.diff.gz).
Exact archive of 25 test modules: [new-tests.tar.gz](primary/new-tests.tar.gz).
Four fixture corrections and preserved assertions:
[pass16-fixture.diff](primary/pass16-fixture.diff).
No method/argv/owner/token/countdown/engine pin/claims/launcher/build/publication
input changed this pass. No wipe engine was added or executed.

## Original proof and controlled corrections

Root independently replayed the final398tests against58exact starting
source/static files in a private copy; shared source was never reverted.
**203 intended AssertionError failures /195 controls /0errors /0skips**:
159discovery refusals,18modal key cases,26explicit Tcl-bgerror cases.
All26final Tk failures explicitly identify invalid Tcl callbacks, rather than
an unrelated focus assertion. See [original-summary.json](primary/original-summary.json),
[original.xml](primary/original.xml), [original.txt](primary/original.txt) and
[original-proof.py](primary/original-proof.py). Original native6case Escape and
3case callback replays are separately retained. The default-bgerror trace maps
the exact callback registration, old Entry owner, pending after ID, redraw,
deleted command and eventual default Tcl error; no error-modal focus claim.

Fresh49module baseline:1676PASS/7existing140ms startup-focusFAIL,0error/skip.
The mapped-frame diagnostic reproduced two140ms races and settled by300ms;
it does not individually attribute all seven initial frames. Existing fixture
now starts the same140ms observation after the actual mapped startup redraw,
retains every focus/state/countdown assertion, and fails a missing-draw watchdog.
Two AST-only GTK fixtures bind the extracted actual shared guard; every prior
assertion is unchanged. No safety assertion or test was removed or skipped.

Retained failed/corrected history:

- Initial new Tk fixtures forced root focus after an update and later resized
  after preparing callbacks. These setup artifacts obscured13then3failures;
  native focus/geometry now precedes callback preparation, every assertion stays.
- First combined adjacency:2073PASS/8FAIL. Five new fresh-key controls sent
  release/press in the same server millisecond. The new fixture keeps the
  conservative guard, adds a20ms release gap and asserts distinct observed
  timestamps. Synthetic equal-timestamp cases remain unchanged. Three remaining
  Tk navigate-idle fixtures now set final geometry before mapping. Final affected
  UI119cases PASS,0error/skip.
- One private replay setup selected default Xvfb:99;47new fixtures refused it
  before effects. Corrected to a new owned display starting150. No shared X11
  display was changed. Initial setup receipts are retained, not counted as passes.
- Initial full lint stopped on two type errors in the new helper. Runtime Tk's
  private registry is obtained withgetattr and an optional lookup uses its own
  variable. No type ignore or behavior relaxation; re-frozen full gate rerun.
- One full suite run used a space-bearing venv executable path. CI fake tools
  generated invalid Linux shebangs. Exact failures, harmless interpreter/shebang
  probe and final no-space alias receipts distinguish this environment issue
  from a product defect. The alias uses the same existing interpreter, packages
  and venv; no install, product change or assertion relaxation. The full failed
  run was23FAIL/7942PASS/14skips, plus1OrcaPASS.22cases were launch setup; the
  remaining Tcl-only picker fixture needed an accurate leaf winfo_children
  method. All23exact failed IDs pass with the corrected interpreter, fixture and
  rejecting fallback guards before the full rerun.
- A guard then blocked the legitimate local gcloud file-list test. Its exact
  failure is retained. Root intentionally stopped only owned pytestPID36787:
  SIGINT03:21:42.296955UTC was ignored by the inherited background disposition;
  SIGTERM03:22:25.187569UTC ended it. Wrapper exit1; no fresh main JUnit, and the
  stale older report is explicitly rejected. Tracked child and pytest both
  exited. This attributed interruption is distinct from historical pass8.
  The final guard permits only canonical owned private pytest upload trees with
  fresh matching configuration and disables credentials/telemetry/update checks.
  Installed SDK source and an independent peer confirm the command is local
  file listing. Twelve intercepted authority cases and the actual local test
  pass. Final gate starts with deleted old owned JUnit reports and verifies
  freshness; denied remote/privileged fallback attempts remain zero.

A derived receipt verifier initially assumed a JUnit failure type attribute;
Pytest9 omits it. The corrected observer authenticates each traceback ending
with AssertionError. Source, tests and passing gate are unchanged. Prepared
diagnostic scripts without an execution receipt were not run.

All initial/intermediate scripts, logs, JUnit and freezes are retained with
explicit prefixes. Setup-observer corrections (Tcl empty interpreter path and
callit code-name registration) are distinct from product/gate passes. No80ms
deliberate product timer exists. No unexplained stop/kill/termination occurred
this pass. Historical pass8/pass9 blockers are separately preserved.

## Final verification and actual artifacts

All nine local phase exits0 on the exact final freeze/config. Commands, UTC
times and logs: [local-gate-status.json](primary/local-gate-status.json),
[run-gates.py](primary/run-gates.py), [final-summary.json](primary/final-summary.json).

| Check | Result |
| --- | --- |
| Syntax, full lint, types, security and shell checks | PASS;52typed source files. Existing TODO scanner's regex-constant match and annotation-unchecked notes are informational, not missing tests or product warnings. |
| Fake preview and negative boot-exclusion mutant | PASS; generated HTML, all-language JavaScript, console/helper checks; required missing-exception mutant failure confirmed. |
| Go1.26.8 uncached race, vet,350000fuzz executions | PASS; fake firmware only. |
| Windows AMD64 test cross-build | PE32+AMD64, {s['windows_crossbuild']['size_bytes']}bytes, SHA256`{s['windows_crossbuild']['sha256']}`. Cross-compilation only; native acceptance NOT RUN. Binary remains outside git at`/tmp/pass16-primary/desktop-windows.test.exe`. |
| Canonical separate main/Orca private72DPI sessions | **7966uniquePASS/14same image-only skips**,0failure/error/xfail/duplicate IDs. Every398new and1365prior regression passes. Unchanged sound timing test passes. |
| Final fresh runner matrix |153short semantic/projection cases,153actual>1MiB fake polls,90evidence/export-readiness/recovery roundtrips with authenticated suffix-tamper refusal;0mismatches/semantic errors/native acquisitions.54mixed-advisory traces are explicitly nonfindings. |
| Final cancellation/retry matrix |144cases across3paths/3methods/2completion states/8stop modes. Real ordinary-file flock/log FDs retained during uncertain stop; released only after confirmed terminal state. Fake process operations only; no OS PID signals. |
| Final native geometry |270Tk/GTK cases across3languages/3text sizes/15screens; all pass,0effects/callback errors.27critical Tk keyboard/owner/token controls fully visible. Five actual PNGs independently viewed. |
| Final reports/export/privacy |90cases across3methods/3languages/5count states/2log sizes.70actual bundle files/manifests authenticated; five owner/share/result/HTML bundles inspected. Preview{a['preview_size_bytes']}bytes, SHA256`{a['preview_sha256']}`. |

The exact14skip IDs/reasons match pass15: two generated live-build config checks
and12manufacturing-ISO checks. They remain skips, not image/native passes.
No auxiliary runtime campaign overlapped the canonical main/Orca gate.
Fresh final campaigns ran sequentially afterward; exact commands/exits:
[final-campaign-status.json](primary/final-campaign-status.json).
All153large logs and90evidence/sidecar pairs (333files) are authenticated and
compressed in [runner-final-fixtures.tar.gz](primary/runner-final-fixtures.tar.gz).
Original pre-fix fixtures remain in a separate archive. Actual report bundles:
[report-artifacts.tar.gz](primary/report-artifacts.tar.gz).
Artifact checks: [campaign-verification.json](primary/campaign-verification.json),
[artifact-review.json](primary/artifact-review.json).

Three bounded source reviewers approved their exact final assignments. Root
independently reviewed the union, all original failures, full accumulated diff,
source/test/fixture preservation, actual artifacts, JUnit uniqueness/skips,
checksums and empty index. Reviews: [discovery](discovery/final-source-review.md),
[runner/evidence](runner/final-source-review.md), [UI/boot](ui/final-source-review.md).
These source reviews do not replace the runtime receipts or platform acceptance.

## Boundaries, remaining acceptance and next action

Final verification uses fake metadata/processes, ordinary temporary files and
owned private72DPI X11/DBus, plus rejecting child-PATH fallback guards with zero
attempts. The failed space-interpreter run escaped its fake executable stubs:
public metadata was downloaded (eight temporary fixtures), system xorriso ran
on an ordinary temporary file, and three unmocked loop probes reported successful regular-file attachments
and ownership-checked cleanup. Empty fake bookkeeping was initially misread as
zero attachments; that statement is corrected. Exact original loop IDs were not
retained. Follow-up read-only losetup inventory found no matching fixture
backings or remaining fixture-prefix directories; it did not detach anything. See
[failed-environment-boundary-audit.json](primary/failed-environment-boundary-audit.json).
No physical device was supplied as a wipe target and no erasure occurred. No
hosted job, login, external message, physical media/firmware/power
change, guest or passthrough operation was performed. No
Companion or USB Easy Use change. Current AGENTS/remote-host constraints apply;
the absent shared guide is recorded with the existing owner continuation.

Still required for audit acceptance: review the recorded failed-run boundary
incident and corrected guard evidence, plus attributable platform execution/signal
evidence for pass8's06:29UTC SIGTERM/exit143, and the unavailable original pass9
failed timing trace. Obtain those records and reconcile them; later passes do
not supply their cause. Revalidate exact source/config after any further change,
then commit/push with`safety:`only when required acceptance is satisfied.
The canonical record is [BW-BUG-AUDIT-20261017-PASS16](../../../.ai/memory/unfinished-work.md).

ISO/QEMU, native Windows, actual hardware/firmware/boot media and physical
reconnect qualification remain **NOT RUN/BLOCKED** here. Use the separately
authorized disposable isolated worker and existing qualification records when
those prerequisites exist. No publication was requested or performed.

Every flat original/intermediate/final receipt has an exact copy in
`original-transcripts.tar.gz` and a checksum index. Final retained-file hashes
are in`artifacts-sha256.txt`; exact source/test/patch/archive readback and index
verification are in`primary/retention-verification.json`. These records prove
the stated local checks, not missing platform acceptance or deployment.
'''
# Format narrative counts without touching paths, code spans or hashes.
import re
def spaced(part):
    part=part.replace('uniquePASS','unique PASS').replace('Go1.26.8','Go 1.26.8')
    part=re.sub(r'\b(with|against|All|all|The|the|Every|every|Final|final|Fresh|fresh|Exact|exact|total|across|plus|and|two|three|No|UI|Preview|starting|SIGINT|SIGTERM|pytestPID)(?=\d)',r'\1 ',part)
    part=re.sub(r'(?<=\d)(?=(?:new|prior|explicit|unique|same|existing|exact|starting|final|controls|control|refusals|cases|case|tests|test|modules|module|inputs|input|untracked|typed|languages|language|methods|method|screens|screen|logs|log|files|file|pairs|errors|error|skips|skip|failures|failure|FAIL|PASS|effects|mismatches|evidence|manufacturing|bytes|fuzz|ms|UTC|Tk|Orca|discovery|modal|paths|completion|stop|count|text|native|MiB)\b)',' ',part)
    part=re.sub(r'(?<=\d)then(?=\d)',' then ',part)
    part=re.sub(r'(?<=,)\s*(?=\d)',' ',part)
    part=re.sub(r'/(?=\d)','/ ',part)
    for value in ('7966','1365','1763','1676','2073','7942','350000','9021440','185540'):
        part=re.sub(r'\b'+value+r'\b',format(int(value),','),part)
    return part
pieces=re.split(r'(`[^`]+`|\]\([^)]+\))',text)
text=''.join(part if i%2 else spaced(part) for i,part in enumerate(pieces))
for old,new in {'runtimeSHA256':'runtime SHA-256','withgetattr':'with `getattr`','requires`':'requires `','at`':'at `','in`':'in `','with`':'with `','SHA256`':'SHA-256 `','PE32+AMD64':'PE32+ AMD64','Pytest9':'Pytest 9','pass8\'s06':'pass8\'s 06','startup-focusFAIL':'startup focus FAIL'}.items():
    text=text.replace(old,new)

for old,new in {'744of751 starting': '744 of 751 starting', 'modules/ 1,365': 'modules / 1,365', 'Original native6 case Escape and\n3 case callback replays are separately retained.': 'The independent native replays cover six Escape cases and three callback cases.', 'Fresh 49 module baseline:1,676 PASS/ 7existing140 ms startup focus FAIL, 0 error/skip.': 'The fresh 49-module baseline ended with 1,676 passes, seven existing 140 ms startup focus failures and zero errors/skips.', 'by300 ms': 'by 300 ms', 'same140 ms': 'same 140 ms', 'obscured13 then': 'obscured 13 then', 'adjacency:2,073 PASS/ 8 FAIL': 'adjacency: 2,073 PASS / 8 FAIL', 'a20 ms': 'a 20 ms', 'Xvfb:99;47': 'Xvfb :99; 47', 'was23 FAIL/ 7,942 PASS/ 14 skips, plus 1OrcaPASS.22': 'was 23 FAIL / 7,942 PASS / 14 skips, plus one Orca PASS. 22', 'pytestPID 36787': 'pytest PID 36787', 'Wrapper exit1': 'Wrapper exit 1', 'phase exits0': 'phase exits 0', 'PASS;52': 'PASS; 52', 'private72DPI': 'private 72 DPI', 'unique PASS/ 14': 'unique PASS / 14', '|153short': '| 153 short', '153actual>1': '153 actual >1', 'refusal;0': 'refusal; 0', 'acquisitions.54mixed-advisory': 'acquisitions. 54 mixed-advisory', '|144 cases': '| 144 cases', 'paths/ 3 methods/ 2 completion states/ 8': 'paths / 3 methods / 2 completion states / 8', '|270 Tk': '| 270 Tk', 'languages/ 3 text sizes/ 15': 'languages / 3 text sizes / 15', 'errors.27critical': 'errors. 27 critical', '|90 cases': '| 90 cases', 'methods/ 3 languages/ 5 count states/ 2': 'methods / 3 languages / 5 count states / 2', 'sizes.70actual': 'sizes. 70 actual', 'Every 398 new and 1,365 prior regression passes.': 'All 398 new and 1,365 prior regression cases pass.', 'All 153large': 'All 153 large', 'and 90evidence': 'and 90 evidence', '(333files)': '(333 files)', 'SIGTERM/exit143': 'SIGTERM/exit 143', '`safety:`only': '`safety:` only', 'owned private 72 DPI X11/DBus': 'owned private 72 DPI X11/DBus', 'system xorriso ran\non an ordinary temporary file, and three unmocked loop probes reported successful regular-file attachments': 'system xorriso ran on an ordinary temporary file, and three unmocked\nloop probes reported successful regular-file attachments'}.items():
    text=text.replace(old,new)
(dest/'README.md').write_text(text)
print('wrote',dest/'README.md')
