# Beamo Wipe comprehensive bug audit, sixth pass

This fresh pass starts from `0547f9124a6841cf074fdfb553a1e1fcde4f3da2`
on `fix/safety-audit-20261019`. It repairs five independently proved root
causes. Four bounded reviewers covered discovery/safety, runner/progress,
UI/consent and boot/build/developer tooling; root independently reproduced
failures before approving edits and reviewed recovery/report/export.
Defect proofs use fake inventory, device, engine, firmware and signal inputs.
Native Tk and GTK use owned private displays; storage fixtures are ordinary
files. Owned build/test/accessibility helpers run without device passthrough.

The complete final gate records **11,354 main Python passes, 28 unchanged
unverified skips, and one separate Orca pass**: **11,355 unique Python passes**,
zero failures/errors and zero Python warnings. All 11,182 prior main test IDs
remain; exactly 200 were added and skip IDs/reasons match exactly. Focused,
model, supplemental and Go results are not added to this canonical total.

Configured syntax/shell/security/full lint, default mypy (52 source files),
preview and private negative safety mutation pass. Fresh uncached Go race
coverage has 338 named pass events and two explicit native skips; vet,
350,000 fuzz executions, launcher cross-builds and Windows test cross-compilation
pass. Development test and desktop doctors pass. Root independently verifies
PE32+/ELF64 x86_64 headers, launcher hashes/current build identity/source digest
and executable entrypoint modes. The actual fake preview was visually inspected
at 72 DPI and closed via its registered WM_DELETE_WINDOW callback with exit 0.
Its screenshot remains outside Git with a retained hash. Nine unchanged
supplemental assertions pass under explicit system Chromium 155.

| Trigger and previous behavior | Result after repair | New coverage |
| --- | --- | ---: |
| Mountinfo retains an old child after a shorter ancestor mount hides it. A hidden live medium or tmpfs row could still qualify safety evidence. | Prove visibility from mount-ID parent relationships before accepting live media, boot-source or tmpfs log evidence. Preserve namespace roots, row reordering and visible children above covers. | 63 Python cases |
| Standard POSIX Popen stop methods silently return after an internal exit poll or suppressed ESRCH. An actual engine failure could become “cancelled” although no signal was delivered. | Retain a delivery receipt at the standard signal boundary, preserving its normal poll/PID protection. Customized processes remain conservative and a later no-op cannot erase earlier delivery. | 111 Python cases |
| Tk swallows a callback interruption or a redraw error after removing Stop controls. The window can remain open without useful monitoring or Stop. | Route errors on the owned root and timer through idempotent interface settlement and teardown. Diagnostic failures cannot skip recovery; peer interpreters remain owned separately. | 8 Python cases |
| Curses swallows a failed warning write or loses rows during resize, yet credits the final review as displayed. | Native writes report success; review credits no explicit failure. Clipped output also earns no complete-line credit. Successful retry, blank rows and existing synthetic paint boundaries retain their contracts. | 18 Python cases |
| A launcher identity contains `source_dirty:null`. Go's boolean decoder leaves false, potentially claiming a manufactured production build. | Reject null in the existing complete-field scan before typed decoding. Valid true/false identity behavior remains covered. | 1 Go parent with 12 named scenarios |

Root's independent original Python proofs recorded hidden mounts 2 failures/2
controls, Tk callbacks 2/2, curses 1/1 and cancellation 12/33. The independent
Go overlay recorded one failing null scenario and two normal controls, with
parent status separate. Exact expanded regressions on archived baseline give
mounts 30 failures/33 controls, cancellation 48/63 and UI 21/5. The UI failures
include eleven behavior failures and ten assertions of the new native-write
return contract; they are not 21 distinct defects. Go's expanded module gives
three failing null scenarios and nine boolean/type/status controls.
No existing test file or assertion changed. The new coverage is 200 Python
cases plus the separate Go module; Go scenarios are not Python passes.

The source freeze contains 809 runtime/test/build inputs. Its manifest SHA256 is
`f7c98a059747973265ff37ce7e146833aef5e5c22a4123d551ea4a9c84f2e582`.
The root mount model independently simulates 2,000 mount sequences, with 6,106
unique-path visibility checks and 11,894 absent/ambiguous refusals, and finds
zero mismatches. IDs are nonmonotonic and rows reordered. No actual mount runs.
A native-origin log matrix compares 1,500 seeded sequences across 19,500
full/projection comparisons with zero mismatches. Bare-log exploratory metadata
source differences remain historical and were not verified outcome defects.

Recovery/report/export review found no additional proved defect. Twenty
unchanged modules pass 401 cases in an isolated baseline archive. A 792-case
sharing matrix spans three saved/report languages, 11 outcomes and eight
identifier forms: zero semantic/redaction failures, original evidence mutations
or native callbacks. These are supporting checks and overlap full coverage.
Reviewer adjacency records mounts 834 passes, runner 324, UI 258 plus 49 focused
Tk controls, and boot/developer 285. These totals are not added together or to
the canonical full-suite count.

Intermediate failures remain distinct from passes. A first mount repair
passed existing controls but refused valid new children above an ancestor
cover. Two external controls and four expanded controls exposed that
related overblocking; branch comparison was corrected with no old assertion
changes. UI proof history preserves omitted fake dry-run setup, wrong Canvas
text lookup and an unmapped Stop fixture correction. The final exact UI
modules also replay against baseline after the import correction.
The private report archive first omitted helper HTML assets, causing three
FileNotFoundError setup failures; adding exact baseline assets lets all 401
unchanged cases pass. The Go proof initially used a nonexistent private working
directory; no command ran.

Root integration found six E402 lint errors from placing importorskip before
imports in the new Tk test. An ordinary tkinter import fixes the ordering;
the tested UI module already requires tkinter. No assertions changed. The
early full run was canceled before this test-source correction and is not a
pass. A first external proof run passed its 55 assertions but could not write
pytest's cache outside the mounted checkout; the corrected invocation disables
that optional cache. An initial Go proof filter matched no tests, so its empty
success is not proof; the corrected actual three named scenarios execute.
Concurrent Docker vfs containers copied the development image and exhausted
temporary storage, causing preview/browser/proof setup failures. Final container
checks run sequentially. Every failed/incomplete receipt stays in history.

Root final review then found an incomplete part of the curses repair: the loop
clamps logical width to 20, so actual widths 5 or 18 still clipped text while
returning True. Root and the UI reviewer independently reproduced two behavior
failures with width-19/200 controls. Four new cases fail on the incomplete
repair, including ASCII/Unicode clipping, and 14 controls pass. Native drawing
now returns complete-string equality after writing, retaining clipped display
but refusing full-review credit. The expanded module plus original probes
passes 22 cases under strict warnings. The prior run was canceled before this
source change and is not a pass; a new full gate uses the corrected source.
A focused native UI invocation omitted the explicit isolated-display flag and
skipped 78 guarded native cases. That run is not 263 passes. The corrected
invocation executes all 263 cases successfully, with zero skips. The complete
canonical gate already enables that flag explicitly.

The 28 historical Python skips remain qualification gaps: 14 generated-image/
artifact checks, nine pinned-browser checks, four Microsoft documentation
network checks and one legacy gcloud check. The Go suite separately retains
two native skips: inventory opt-in remains unset and native Windows PowerShell
is absent. Explicit system Chromium is supplemental, not pinned acceptance.
Current managed networking is restricted/enforced; required browser/document
hosts remain unavailable. No network policy or proxy bypass was attempted.

Remaining work requires the supported allowlist/pinned-browser checks and
separately authorized isolated ISO/KVM and native Windows/macOS qualification.
Firmware, physical media and reconnect/readback remain unverified. Cross-builds,
fake inputs and Python 3.10 grammar parsing do not qualify those platforms.
Named filesystem checks do not claim atomic compare-and-swap.

No actual nwipe, native inventory/mount/device write, guest, power/firmware
change, hosted workflow, PR, merge or release occurred. Remote publication
remains pending the prior approval review; no remote mutation was attempted.
The canonical backlog links this report. Full operational checkpoints and
final local commit/build identity remain outside Git under
`/workspace/beamo-tools/audit-pass6-20261021/root/`.

Run `python3 docs/evidence/bug-audit-20261021-pass6/verify_retained.py` to verify
all 809 source inputs, retained artifact hashes, exact new/prior test IDs,
unchanged skips and separate Go results. Baseline proofs retain their original
workspace paths; the baseline commit and source hashes identify their inputs.
The retained build receipt describes baseline HEAD with source_dirty=true
during frozen-source testing. Clean development launchers are rebuilt after
the local commit; final identity is recorded outside Git. This does not replace
native platform, image or hardware qualification.
