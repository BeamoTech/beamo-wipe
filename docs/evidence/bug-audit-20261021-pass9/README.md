# Beamo Wipe: ninth comprehensive local audit

One independently reproduced startup-ownership defect is repaired on baseline
`e28487d7595ee45a53d503fa1a76d8c22979f012`, branch
`fix/safety-audit-20261019`. The final complete local gate records **11,676 unique
Python passes** (11,675 main plus one separate Orca case), **28 unchanged
unverified skips**, zero failures/errors and zero Python warnings. Every one
of the prior 11,639 main test IDs remains; exactly 64 new regression/control
cases were added. Supporting subsets, models, browser and Go checks are not
added to this canonical total. [Machine summary](final-summary.json).

## Verified defect and repair

A transient error reading the kernel command line or mount table could make
public startup initially classify the machine as a desktop and skip opening
`SessionStore`. Later successful reads of the same live-session metadata could
clear preview flags and construct a real-mode wizard with no recovery store.
Both root and a reviewer reproduced actual public controller dispatch to that
unowned wizard using fake metadata and a fake interface. No erase was performed,
and this finding does not demonstrate a bypass of the separate owner/token/
countdown/Erase-now gates.

Startup now refuses an unowned live session before discovery. A second boundary
refuses any real-mode wizard without a session store before report recovery or
interface presentation, including classification that recovers during staged
construction. Both use the existing blocked return code 3. Normal owned live
startup and explicit desktop previews retain their behavior. Discovery, mount
reader compatibility, nwipe arguments, methods and consent rules are unchanged.

The exact 64 new cases cover both proc files, one/two/three transient failures,
four interface routes and two preview flags, with 16 stable-live/desktop positive
controls. Against archived baseline product bytes, **48 fail and 16 controls
pass**, with zero errors/skips. All 64 pass after repair. Root independently
replayed that exact archived module and confirmed all 48 failures/16 controls.
Root's separate original proof retains one failure/two controls; the reviewer's
independent proc-I/O proof
retains two failures/two controls. All seven original cases pass after repair.
The integrated adjacent group passes 210 unique cases with strict warnings.

## Source and assertion integrity

The product change adds 11 lines in `app.py`. One regression module is new.
Two existing test modules receive ownership fixture adaptations for three
logical scenarios (four executions): the two internal-entry reader tests now
receive the fake store normally acquired by public startup; the parameterized
poweroff recheck receives a quiescent fake owned store. Their expected results,
reader/engine counts and poweroff assertions remain unchanged. The reader file's
68 assertion syntax trees are identical. The poweroff file's four are identical
after normalizing its single `session_store=None` to fake-store input change.
Every other existing test file is byte-identical; all old test IDs remain.

All **818 frozen source, test, build and packaging inputs** verify. Root read
the complete product diff and new test module, independently reproduced the
failure before editing, checked positive controls, and reviewed every bounded
reviewer's evidence. No frozen source changed during final verification.

## Complete local checks and artifacts

Configured syntax, shell/security/full lint, developer-tool format checks,
default mypy (52 source files), preview and private negative safety mutation
pass. The lint script's existing literal-pattern TODO notice and default mypy
notes are unchanged; they are not Python test warnings. Test and desktop doctors
pass. Fresh uncached Go race coverage records 338 named pass events and two
explicit native skips; vet, 350,000 fuzz executions, Windows test cross-compilation
and Windows/Linux launcher cross-builds pass. No Go product tests changed.

Final phases ran serially inside one unprivileged development container. Root
independently checked the produced PE32+/ELF64 x86_64 headers, source identity,
bundle/source digest, file hashes and executable modes without executing native
launchers. The actual fake-disk Tk welcome screen was visually inspected at
72 DPI after its content painted, then closed using its registered
WM_DELETE_WINDOW callback with exit 0. The screenshot remains outside Git;
its hash and inspection receipt are retained. Nine unchanged supplemental
browser assertions pass under explicit system Chromium 155; this does not
qualify the unavailable pinned Playwright runtime.

## Five bounded reviews and independent model replays

Reviews covered discovery and safety; runner, progress and completion evidence;
wizard and all consent surfaces; recovery, logs, export and privacy; and desktop
readiness, boot/build and developer tooling. Root independently replayed all
five fresh models on frozen source, preserving the exact Python scripts and
changing only the Go model's metrics destination:

- Inventory: 512 contexts, 5,120 discovery calls, 4,096 tree/flat/order checks,
  5,976 positive selectable observations and 14,504 protected observations;
  512 ambiguous-boot and 512 contradictory-identity refusal controls.
- Completion: 480 ordered contradiction/method/log cases, including 96 positive
  and 384 refusal controls; 240 whole-log versus projected-log comparisons.
- Persistence: 360 regular-file cases, 124 successful operations, 236 injected
  refusals, 208 clean retries and 360 reopens. These model observable errors
  before/after syscall boundaries, not an atomic filesystem guarantee.
- Consent: 399 sequences, 4,233 blocked Erase calls, 396 explicit DryRunRunner
  starts and 117 nested-overlay checks; zero automatic starts.
- Firmware policy: 150 inventory states with 40 positive readable controls;
  6,048 fake restart transactions with nine success controls, 6,039 refusals
  and 288 foreign-request preservation controls. No actual firmware operation.

Every model completes with zero mismatches and native callbacks. They are
supporting evidence, not additional canonical tests or native qualification.
Fresh reviewer subsets record discovery 2,320 passes plus six exact historical
pinned-browser skips; runner/engine/evidence 1,643 disjoint passes; UI 310;
recovery 714; boot/developer 255. Root's lifecycle/audio/startup subset passes
358. These overlap the full suite and are never summed into unique coverage.
No additional selection, engine, UI, recovery or boot/build defect was promoted.

## Retained history and qualification limits

Root's initial mixed UI subset ran without X and retained 13 failures/335 passes/
10 skips; the correctly isolated 72-DPI rerun passes all 358. The first integrated
repair run retained two poweroff-fixture failures/208 passes; supplying fake
session ownership preserves the original recheck behavior and all 210 pass.
The first looser transient regression candidate retained 34 failures/30 passes;
the final test was strengthened to require refusal for every transient case,
then archived and replayed against unchanged baseline bytes (48 failures/16
controls) before editing product code. The recovery model's initial import-order
setup error and the runner model's slower all-green implementation remain
history. None is counted as a passing final check or extra product defect.

The 28 previous skips retain exact IDs and reasons: 14 image/artifact cases,
nine pinned-browser cases, four Microsoft-document reachability checks and one
legacy gcloud check. Go's two native inventory/platform skips remain open.
Pinned-browser/network checks, ISO/KVM, actual nwipe/device behavior, native
Windows execution, firmware and physical USB/reconnect acceptance remain
unverified. Local readiness does not establish complete release qualification.

Blacksmith remains the current hosted provider. No GCP or hosted gate, remote
write, PR, merge, release, actual engine/device/mount/firmware/power or guest
operation occurred. Publication remains pending the earlier automatic approval
review that rejected operational-backlog metadata export as internal data;
no remote-write retry or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass9/verify_retained.py` to verify
the source manifest, retained hashes, canonical/new/prior identities, unchanged
skip reasons, fixture assertions, exact baseline failures and separate Go/model
results. Baseline proof paths identify their original workspace; source hashes
and commit receipts bind the inputs. The retained candidate launcher receipt
has baseline HEAD and `source_dirty=true`. Clean development launchers are
rebuilt after the local commit; exact final commit/build identity is recorded
outside Git to avoid self-referential commit identity. Remaining qualification
and publication actions stay in the canonical backlog.
