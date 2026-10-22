# Beamo Wipe comprehensive bug audit — second pass

Five new reproducible defects are repaired with 319 regression/control cases.
The primary independently reproduced every finding before authorizing source
edits, reviewed the integrated changes, and ran all 319 new cases successfully.
The complete canonical local gate passed: **10,727 unique source/Orca passes,
28 unchanged unverified skips, zero failures/errors**. Main pytest passed 10,726
cases in 1053.08 seconds; independent Orca passed one case. Every previous main
test ID is retained, exactly 319 were added, and all skip IDs/reasons match.
[Exact results](final-summary.json), [delivery record](delivery.json), and
[retention verifier](verify_retained.py) bind the evidence to this source.

Baseline: `32819accc77f6ed1090c6f9f0e82800d9db7b7a2`, branch
`fix/safety-audit-20261019`, checkout `/workspace/beamo-wipe`.
Final implementation freeze covers 792 runtime, test and build inputs. The
source manifest SHA256 is
`84fc73f381a6381aa990b12217a8a06de650e2f1728cba3f0a6669061d98f9bf`.
The first audit remains separate historical evidence for its earlier source.

## Proven defects

| Trigger and original behavior | Repair and regression coverage |
| --- | --- |
| An unbound filesystem row with missing/unknown TYPE is omitted from target layout identity. Changing its UUID leaves the target selectable with an unchanged fingerprint. Root proof: 12 failures, 15 controls across three discovery routes. | Apply the existing unresolved-ancestry refusal to unknown types carrying filesystem evidence. Retain bound unknown volumes, whole-disk filesystems, harmless standalone inventory and anonymous label-only rows. Final 125 cases; original implementation fails 63 with 62 controls. Includes final guarded runner refusal before process spawn. |
| A 36-byte ATA model containing a short Error Summary and nonzero row falsely attributes an engine/media error. Root proof: 18 failures and six native/legacy controls. | Require the full pinned banner to attribute table errors in native-record logs. Ambiguous target errors prevent success; genuine errors retain precedence. Legacy short inputs and authentic zero/duplicate/malformed contracts remain. |
| Log growth between EOF-position and metadata capture authenticates a bounded prefix as complete, hiding an appended explicit failure. Root public-poll proof: successful result despite the failure, plus unchanged control. | Derive size and signature from one fstat snapshot. Eight regressions append across stable seek/snapshot boundaries and assert the injection actually occurred; both small and boundary-sized logs are covered. Unchanged complete/truncated controls still succeed. Together the two runner fixes add 143 cases. |
| Scrolling Method and opening Limits carries the old scroll offset, omitting opening support/SSD guidance. Root reproduced the actual Wizard on a fake 80x24 terminal with an unscrolled control. | Reset body scroll on every screen transition, preserving within-screen paging and final-review visibility/countdown rules. Seven natural Method/Limits/Keyboard transition and paging controls; four fail on original code. |
| Launcher output created/replaced while compilation runs is silently overwritten, for fresh output and valid prior bundles. Root independently reproduced two overwrites and two normal controls. | Retain verified prior digests and recheck all outputs after compilation and immediately before each replacement. Advance expectations only for the builder's own published bytes. Unexpected regular files, links, directories or missing outputs abort without a new success receipt. 44 cases across both output implementations; original fails 36 with eight controls. These checks do not claim an atomic operating-system compare-and-swap. |

No wipe method, argv, confirmation token, countdown, boot exclusion, approved
claim or pinned version changes. No original test assertion was weakened.

## Review and execution

Four bounded reviewers re-examined discovery/identity/classification;
runner/progress/logs/cancellation/evidence; Tk/GTK/curses/refresh/recovery;
and boot/kiosk/staging/build/desktop readiness. The primary independently
reviewed report/export/privacy and same-boot recovery, validated each original
failure, reviewed all product/test changes and owns the final gates.

Focused reviewer results are storage 965 passed, runner 1,462 passed,
console/review 90 passed and builder/development 113 passed. These overlap the
full suite and must not be summed as unique tests. The primary's separate
console/review check passed 82 cases; all 319 new cases also passed together.

Additional independent checks:

- Report/export/recovery baseline: 401 passed.
- Report/sharing/bundle matrix: 792 fixture cases across three languages and
  eleven outcomes, including malformed core fields, exact checksums, redaction
  and preservation of original evidence. Supplemental, outside canonical count.
- Whole-log versus bounded streaming projection: 1,500 seeded cases, no
  outcome/check discrepancy. Oversized numeric rows safely return conservative
  results without conversion exceptions; no numeric-code change needed.
- Full lint/types/security/shell, generated web/console/helper preview and the
  private safety mutation check passed. The pre-existing TODO regex warning is
  explained by the literal placeholder-detection pattern in release_manifest.py;
  mypy's untyped-body notices are unchanged informational output.
- Fresh Go race execution uses `-count=1`; vet and 350,000 fuzz executions pass.
  An earlier cached race result is excluded from fresh-execution evidence.
- Windows/Linux launcher cross-builds and Windows test cross-compilation pass;
  artifact hashes, PE/ELF headers and the build receipt are independently checked.
- Actual `./preview` inspected on private Xvfb :450 at 72 DPI, then closed through
  its registered WM_DELETE_WINDOW callback with exit 0. No forced termination
  was needed. The inspected fake-preview image remains in the workspace.
- Nine unchanged browser assertions pass with explicit system Chromium
  155.0.8059.79. This is supplemental; the pinned browser is still unavailable.
- Changed Python files parse using Python 3.10 grammar. This is not execution
  on a Python 3.10 interpreter. Primary review corrected test-only nested
  f-string quoting before the final source freeze.

A bounded Tk geometry probe found the destructive warning fully visible at
1600x1000 standard and 800x600 standard. At 800x600 with extra text, its last
six vertical pixels extend below the scroll viewport; scrolling is available.
This observation is retained without claiming a separate authorization defect.

The first discovery repair overblocked an existing positive null-row control;
the original assertion was preserved and the guard narrowed. A new production
null-row fixture then lacked mandatory mount metadata; completing that fixture
fixed the setup without weakening schema or assertions. Both failed candidates
are retained as history and excluded from final passing results. The original
tell-hook race proof would cease injecting when tell() is removed; final stable
snapshot/seek hooks explicitly prove injection still occurs after the repair.

## Qualification limits

The managed network still excludes cdn.playwright.dev, support.microsoft.com and
learn.microsoft.com. Review/apply the existing proposed allowlist through the
supported environment configuration UI, install the actual pinned Playwright
browser with normal proxy/CA settings and rerun the affected checks. System
Chromium is not represented as that pinned runtime.

Generated ISO artifacts, ISO/QEMU, native Windows/macOS execution, firmware,
physical disks/USB and physical reconnect acceptance remain unverified.
This worker has no KVM. Use separately authorized isolated workers for the
applicable final image/native qualification. The legacy gcloud check is outside
current local development requirements; current project Blacksmith guidance
supersedes the uploaded legacy GCP baseline.

No real nwipe or physical device action, host restart, firmware change, hosted
workflow, merge or release was performed. Routine source verification remains
local. The canonical unfinished-work record preserves open qualification and
the distinction between local, pushed and released state.
