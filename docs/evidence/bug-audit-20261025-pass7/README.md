# Comprehensive audit pass 7 — 2026-10-25

**Available source review and portable/static checks are finished. Required
Linux/full, native, artifact and physical acceptance remain BLOCKED/INCOMPLETE.**
This pass corrected one pre-existing P2 startup shutdown defect, hardened the
kiosk power check and corrected stale recovery documentation. No new completion
false-success or disk-target authorization finding emerged in the broad reviews.

Source: `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`, branch
`codex/wipe-audit-20261024`, HEAD/base `9764d93ac21273aa79ae4618629b0a30e3eda271`
plus dirty changes. App.py and the peer/default checkouts were not edited by this
pass. No staging, commit, push, hosted CI, publication, host power, device/media,
firmware, service, security, network, guest or real nwipe operation occurred.

Raw evidence: `C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261025-r7`.
[verification.json](verification.json) binds final source/checks and the packet;
[reviews.json](reviews.json) retains eight terminal tasks and parent validations.
[Pass6](../bug-audit-20261025-pass6/README.md) and earlier packets remain unchanged
at their original evidence levels. Bounded fakes do not qualify a release.

## Corrected P2: R7-POWER-2, live startup fallback

On failed live startup, app._blocked_wizard constructs an inert DryRunRunner but
sets dry_run=False. Wizard._live_pinned_engine_busy formerly skipped every runner
outside NwipeRunner. With a fresh valid quiescent session and an external manual/
legacy pinned engine lacking the current journal/lock/history, both the owner
shutdown action and final app power check omitted independent engine inspection.

Independent exact main/parser/live-startup/store/console/controller AST reached
the fake power callback in six red cases: busy, unknown or raising inspection;
report-discard consent; worker-start failure; and busy state after UI acceptance.
Twenty-eight controls matched. The full source call chain and base comparisons
establish a pre-existing code defect under explicit boundary contracts. No real
engine, actual Linux startup failure, native process observation or power event
was executed; no interrupted real erase or hardware damage is claimed.

The correction removes only the runner-type exemption, retaining dry-run/preview
exclusions, fresh inspection, explicit-False-only authorization and exception
refusal. Other Wizard method ASTs are identical. App.py is unchanged. Parent's
independent factory/full-constructor/shutdown model changed from3 red/7 controls
to10 matching cases. The new startup test defines28 live app/session/final-check/
report cases and2 preview controls; its actual Linux pytest remains UNRUN.

Fresh correction review R3 has no production objection and caught one P3 test
isolation regression: two old diagnostic-report tests set demo runners live
without faking engine absence. Parent reproduced the affected endpoint assertions,
then added an explicit clear-engine probe only in those tests. Every original
test statement/assertion and all production bytes are preserved. Fresh narrow R4
review clears that correction; both results and parent source/packet validations
retain their exact counts and failed/incomplete attempts. R3's checksum receipt
used LF-normalized text; parent additionally bound the actual Windows manifest
bytes. Ordinary previous/invalid
recovery, locks, active runner, report and finalization protections remain.

Parent then checked the shared live-mode completed-report fixture. Its external
engine dependency also falsified an existing eight-case report test under busy
fake state, with eight clear controls. The fixture now models external absence
only on its own inert controller; the production class is unchanged. A local
clear-probe fixture also makes live diagnostic-busy tests reach their intended
guard. Removing these declared fixture additions restores both entire original
test-module ASTs and assertions. Current sixteen report cases match without
ambient inspection; direct standalone live busy/unknown/error controls still
refuse. The diagnostic busy/clear transition and modeled patch undo are checked.
Fresh R5 review and parent source/packet validation clear this last narrow scope;
actual Linux fixture execution remains unrun. The instance-local report mock is
deliberately a unit-test boundary, not evidence about an actual external engine.

## Kiosk hardening: R7-POWER-1

The kiosk's name-only pgrep decision could disagree with the existing Python
executable-identity helper. Parent's inert model reproduced4 old mismatches and5
controls;18 current observations match. Power now additionally requires explicit
False from that helper through isolated Python under timeout. The existing
pgrep refusal, exact confirmation and final dispatch remain. Missing, broken,
timed-out or uncertain inspection blocks power; this does not atomically exclude
arbitrary concurrent privileged starts or prove universal timeout teardown.

Independent kiosk correction review found no concrete regression:370 observations
including8 historical-model expectations, plus8 memory-only staging cases.
Twenty functional inputs remained unchanged. Parent checked43 closing inputs
and21 sealed members. The backlog-only drift and failed whole-context stability
command(exit1) remain disclosed. Existing22 shell-test function ASTs and two
run/trace helper ASTs are preserved;11 new actual-shell cases are unrun.

Kernel/procps and all80 pinned engine C/header files support the descriptor-name
concern as source inference; blob hashes, lexical search and limitations remain
in KIOSK-FINDING.md and source receipts. This is not a demonstrated missed native
engine. Actual Debian isolated import, harmless descriptor-launched fixture/
proc/pgrep observation and kiosk execution with inert power recording remain
required before publication on a separately admitted disposable worker.

## Recovery procedure and broad review

R7-LIFE-DOC-1 corrected docs/session-recovery.md to describe fresh owner consent
after a proven unstarted preflight, actual TemporaryFileSystem service storage,
and independent pinned-engine inspection alongside the wipe lock. Parent checked
the exact store/wizard/service code and existing owner-flow regression. No
behavior changed for this documentation correction. It postdates the lifecycle
packet; the earlier packet is preserved at its original bytes.

| Broad scope | Bounded observations | Disposition |
| --- | --- | --- |
| Completion, progress, evidence and recovery authentication | 355;8 modules | No new actionable finding |
| Wizard, UI, recovery, report and ownership lifecycle | 149+21 preflight;36 inputs | No production finding;stale recovery docs corrected |
| Build, manifest, checksum and publication/handoff transactions | 100;40 inputs | No new concrete finding |

Parent read the reports and relevant oracle/probe scope and independently
verified sealed packets and scoped source. Those matrices were not rerun by
parent or aggregated as pytest passes. The later narrow Wizard correction is
covered by its new review and preserved-method AST comparison; old Wizard-byte
reviews are not relabelled as final whole-source acceptance. Supplemental parent
launcher request/revision/browser/boot source inspection found no concrete new
defect; no native execution follows. All setup failures,
withdrawn/unproved hypotheses and prior incomplete gates remain retained.

## Available verification

- Fresh portable pytest after the Wizard change: **254 tests+37 subtests**, three
  exits0, no failures/errors/skips. These execute exact selected AST with fake
  OS/process boundaries in Windows CPython; no actual-Linux product imports.
  The established26 reader groups are complete/disjoint. Original45s per-process
  limits and assertions remain unchanged; old receipts are not overwritten.
  These exact 18 inputs and all 52 type inputs stayed unchanged after the later
  report-test-only fixture edit; they were rebound, not blindly rerun.
- Kiosk inline-guard portable pytest: **2 tests+10 subtests**, exit0, exact code
  with inert imports. Rebound to unchanged current inputs after startup edit.
  Prior sound2+14 subtests reused only at its unchanged source/current-test bytes
  and preserved tested/current AST; not a new run or native audio proof.
- Four current Ruff commands pass. Fresh Windows-hosted mypy with Linux/Python3.11
  stubs passes52 source files. Five pre-existing annotation-unchecked notes remain;
  configured untyped bodies are outside default analysis. Static checks are not
  Linux/native execution. Python syntax and generator embedded Python parse.
- Final census: **934 functional inputs**, identity
  `25ff560c06cbba0ce405603e71a735af452c13a0afb81f77d23ecdf5a191dc9e`. Eight paths differ from entry: kiosk, Wizard,
  four existing test modules and two new regression modules. Docs/backlog are bound
  separately. Overlay:88 paths, SHA256
  `92d62cc727f14153dfcedff626cfdc54ee51f7a0db409ccc8cb9b400dadc8510`; full-byte readback passed. Guides, captured peer
  inputs, index and whitespace observations match; source is still uncommitted.

One checkpoint attempt caught unintended historical backlog newline translation
with its preservation assertion. Failed bytes and driver are retained; parent
restored the original R6-and-earlier suffix as bytes and verified it against the
R7 entry backup. Product source and check receipts were unaffected. Final report
generation preserves that suffix using byte writes.

## Remaining acceptance

Actual-Linux/full admission remains blocked: C: observed free bytes
**2,150,330,368**, below the unchanged8GiB floor. Capacity
loss cause remains unknown. No WSL gate/admission retry, cleanup, peer/cache
deletion or lowered threshold occurred. Adequate capacity and current peer
admission are required before a reviewed final-identity controller chain runs.

Full main/Orca containment remains unimplemented/unqualified: reaping PID-init,
lifelines/private proc, service/Windows-interop exclusion, aggregate resource
limits, bounded writable storage/log transport and ten finite selftests remain
required. Earlier timeouts/cancellations/incomplete gates remain incomplete.

The30 new startup Linux cases,11 new kiosk shell cases, existing full shell/
Linux gates, actual Debian isolated import, native descriptor/pgrep/kiosk checks,
GTK/audio, Go/startup/platform/artifact and separately authorized final public
ISO/QEMU/hosted verification remain unrun or pending. Publication still requires
the original applicable gates and authority; no release qualification follows.

Fresh Lab doctor/sync/Wipe-plan/report preparation exited0 with integrity VALID
at Lab commit d3d0959bb26b17531464dbd1ba233d4d842ad581. The report header/outcomes
were visually inspected in an owned browser tab without network/server startup;
this is Lab preparation, not product UI/native acceptance. Old configured
adapters do not qualify this dirty source; empty worker observation grants no
guest admission. Existing Lab notes are preserved.

Physical Task119 cold reconnect/readback, valuable-disk disconnection, firmware
boot, trust/revocation/SBAT/enforcement cases remain **NOT TESTED/BLOCKED** until
an explicit owner physical-session update and original recovery prerequisites.
A successful boot alone remains insufficient. Commit/merge/release steps await
the required checks and authorization. Unfinished-work retains the next actions.
