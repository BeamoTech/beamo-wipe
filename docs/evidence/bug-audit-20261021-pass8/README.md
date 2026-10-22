# Beamo Wipe: eighth comprehensive local audit

Three independently reproduced defects are repaired on baseline
`d8a941adc16cf0650d482f512e4b921d702373c5`, branch
`fix/safety-audit-20261019`. The complete final gate records **11,612 unique
Python passes** (11,611 main plus one separate Orca case), **28 unchanged
unverified skips**, zero failures/errors and zero Python warnings. All 11,552
prior main IDs remain; exactly 87 regression/control cases were added. Focused,
model, supplemental browser and Go results are not added to this canonical
total. [Machine summary](final-summary.json).

## Verified defects and repairs

| Trigger and consequence before repair | Result after repair | Exact new baseline proof |
| --- | --- | --- |
| Power-worker acceptance sets its flag, then an interruption escapes. The rejected worker can queue an old reading that a later in-flight request accepts as fresh AC status. | Acceptance is revoked before the rejected worker's decision gate opens. Its reading cannot contaminate a retry; accepted readings and stale-driver behavior remain covered. This is reported telemetry, not an erase authorization gate. | 12 failures, 16 passing controls |
| Invalid UTF-8 in the kernel command line or an unrelated mountpoint raises before public startup's refusal handler. | Initial classification returns existing blocked status 3 before recovery, preview, web or engine dispatch. Unknown live state never becomes a desktop fallback. Help/version/invalid-argument exits still avoid metadata reads. | 16 failures, 18 controls |
| Optional runner diagnostic logging or its stderr fallback raises KeyboardInterrupt/SystemExit. A requested Stop can exit before signaling, or completed-process ownership can remain stranded. | Both optional diagnostic boundaries consume interruptions. Stop, conservative liveness checks and terminal ownership retirement continue; actual cancellation and signal receipt logic are unchanged. | 18 failures, 7 controls |

Root independently replayed all three original proofs before edits: 12 cases,
seven failures and five passing controls, zero errors/skips/native callbacks.
All 12 original cases pass after repair. The 87 exact new cases retain 46
baseline failures and 41 passing controls. An independent UI reviewer also
reproduced the power defect and confirmed the actual Wizard timer/text consumer.
No unsafe erasure was demonstrated by these findings.

## Source and verification integrity

Three product files and three new test modules changed. **Every existing test
file is byte-identical**, preserving all old assertions. All 817 frozen source,
test, build and packaging inputs verify. Root reviewed complete product diffs,
all new test modules, proof traces and supported callers before final checks.

Configured syntax, shell/security/full lint, default mypy (52 source files),
preview and the private negative safety mutation pass. The lint script retains
its existing literal-pattern TODO notice and default mypy notes; these are
unchanged notices, not Python warnings or failed gates. Test and desktop doctors
pass. Fresh uncached Go race coverage has 338 named pass events and two explicit
native skips; vet, 350,000 fuzz executions, Windows test cross-compilation and
Windows/Linux launcher cross-builds pass. No Go product test was added.

All final phases ran serially inside one unprivileged development container,
with host-side artifact byte inspection. No source changed during verification.
Root checked PE32+/ELF64 x86_64 headers, current bundle identity/source digest,
file hashes and executable modes. The actual fake-disk Tk welcome screen was
visually inspected at 72 DPI after its content painted, then closed through the
registered WM_DELETE_WINDOW callback with exit 0. Its screenshot stays outside
Git, with hash and inspection receipt retained. Nine unchanged supplemental
assertions pass under explicit system Chromium 155; this does not qualify the
unavailable pinned Playwright runtime.

## Independent model replays and broader review

Five bounded reviewers covered discovery/safety, runner/progress, UI/consent,
recovery/evidence/export and boot/build/developer tooling. Root independently
replayed each fresh model on the final source:

- Discovery: 256 fake inventory contexts, 3,528 public discovery calls, 3,072
  representation/order checks and 456 layout mutations; zero mismatches or
  native callbacks.
- Completion: 5,832 method/counter/phase/percentage/newline/exit combinations,
  including 24 positive and 5,808 refusal controls; zero mismatches/native
  callbacks.
- Evidence/export: 16,200 same-language states, 54 positive outcomes and 2,025
  actual bundle constructions; zero semantic mismatches/native callbacks.
- Desktop readiness: 200 sessions and 16,000 public handler actions plus normal
  closes, 278 authorized fake restart callbacks, 7,013 refusals, 1,405 malformed
  duplicate requests and 1,000 Windows manual-policy controls. All providers
  and firmware/restart callbacks are fake. This is one external Go overlay
  test, separate from canonical product Go and Python totals.

Scoped supporting tests include discovery2,200, app-adjacent326, runner2,600,
UI266 plus137 native UI and91 power-adjacent, recovery715, boot/developer325
and root lifecycle/audio/diagnostics197 (229 after power regressions/original
probe). They overlap the full suite and are never summed into unique coverage.
No additional verified UI, export or boot/build defect was promoted.

## History and qualification limits

The first new startup fixture inherited an existing autouse stub that forced
non-live classification. Its failing candidate record was retained. The final
fixture explicitly restores the real classifier while routing proc reads and
all native boundaries to fakes; every assertion stays intact. Exact final
module bytes were replayed against unchanged baseline source, retaining 16
failures/18 controls. The product repair did not change during that correction.

The first recovery model used log names for a different fake disk, producing
only refusal outcomes and failing the required positive-control assertion.
That script, data, log and exit status remain history. Corrected target-bound
inputs retain the foreign-target case and the original minimum-positive
assertion, then pass 54 successful controls. Root's independent replay uses the
exact final Python scripts; its Go overlay changes only the metrics output
path. Historical setup failures are not counted as product defects or passing
final coverage. The canonical full run completed once on the final freeze.

All 28 previous skips retain exact IDs and reasons: 14 image/artifact cases,
nine pinned-browser cases, four Microsoft-document reachability checks and
one legacy gcloud check. Go's two native inventory/platform skips remain open.
Pinned-browser/network, ISO/KVM, actual nwipe/device behavior, native Windows
execution, firmware and physical USB/reconnect acceptance remain unverified.
Blacksmith is the current hosted provider; no GCP gate was invoked. No hosted
CI, remote write, PR, merge, release, actual engine/device/mount/firmware/power
or guest operation occurred. Publication remains pending the earlier automatic
approval review that rejected operational-backlog metadata export as internal
data; no remote-write retry or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass8/verify_retained.py` to verify
all frozen inputs and retained artifact hashes, unique new/prior IDs, unchanged
skip reasons, old test bytes, exact original failures and separate Go/model
results. Baseline proof paths identify their original workspace; commit and
hash receipts bind inputs. The retained candidate launcher receipt has baseline
HEAD and `source_dirty=true`. Clean development launchers are rebuilt after the
local commit; exact final commit/build delivery identity stays outside Git to
avoid a self-referential commit identity. Qualification gaps and next actions
remain in the canonical backlog.
