# Security audit checkpoint and resumption

Updated 2026-10-27 UTC by Codex. **Implementation checkpoint; acceptance and
merge pending. No release, image, physical USB or real erase is qualified.**

The owner requested that all available work be finished, committed and pushed
toward `main`, with enough context to resume on another machine. This checkpoint
preserves the accumulated audit fixes and regression tests. It does not waive
the current `AGENTS.md` review rules, required `CI gate`, device protections or
separate release authorization. Do not bypass protection to merge it.

## Source and integration

- Repository: `BeamoTech/beamo-wipe`; proposed branch:
  `fix/security-audit-handoff-20261027`, targeting `main`.
- Integration base: `58c677f7316b5e2fc0cbb3ee4b502681c80338c1`.
  Its production source matches `9764d93ac21273aa79ae4618629b0a30e3eda271`;
  the intervening change adds the current Greptile instructions.
- The October 24-26 audit overlay was retained in full: 151 task-owned paths,
  3,019,651 bytes at snapshot. Its baseline is `9764d93`. The newer security
  review started from older `b7c49d9`; its two new regression modules and
  historical evidence were added without overwriting the broader fixes.
- The broader runner/controller fixes subsume the four findings in the
  [October 26 security record](evidence/security-review-20261026/README.md).
  Those older receipts remain bound to their original source.
- The two original worktrees and their indices were left intact. This
  integration uses a separate checkout. Historical `docs/evidence` files from
  main were omitted locally through sparse checkout to conserve space;
  their Git entries are retained. Full acceptance must use a normal checkout.

Use `git rev-parse HEAD` on the pushed branch for its exact commit. The
[verification record](evidence/security-main-handoff-20261027/verification.json)
binds this checkpoint's functional inputs separately from documentation.
Neither a source hash nor a successful model run authenticates a live image.

## PR review follow-up

[PR #93](https://github.com/BeamoTech/beamo-wipe/pull/93) received Greptile's
first review at `7f2f2a4`: 4/5, with one P2 finding. The finding was confirmed:
CI handoff cleanup could stop at its first failed close and replace an earlier
copy, binding or cancellation failure. The correction independently closes
every owned handle, preserves the primary error, protects acquisition and
applies the same rule to member writes and directory-binding checks. Exclusive
creation, no-follow opens, readback, permissions and no-replace publication
remain required. Member writes now explicitly handle partial and stalled
writes through the owned descriptor.

The [review follow-up evidence](evidence/security-main-handoff-20261027/greptile-r1.json)
binds that correction separately from the original checkpoint. The original
192-case regression matrix failed 148 cases; the corrected matrix and 48
additional boundary cases pass, 240/240. These are exact-AST/fake-descriptor
controls, not native close/signal or filesystem-race assurance. The final head
still requires its own CI and Greptile review; older-head results are historical.

## What changed

The combined diff hardens these existing boundaries:

- Completion parsing rejects stale success after damaged target updates,
  requires exact terminal percentages, retains activity uncertainty and
  bounds normalized/deferred completion evidence. Independent validated
  Erased-table proof retains its separate rules; Quick zero is never verified.
- Launch ordering completes inhibitor setup before final rediscovery and
  rechecks the external engine before execution. Raw disks with contradictory
  ancestry are ineligible; uncertain boot ancestry leaves no selectable target.
  NVMe failover checks actual surviving subsystem/controller associations and
  requires proven local PCIe transports.
- Report, journal, diagnostic, identity and manifest helpers retain descriptor
  ownership across interruptions and preserve primary failures during cleanup.
  Export mount acquisition is covered by owned cleanup. Cleanup failure cannot
  publish a trusted success receipt.
- Terminal evidence preserves actual cancellation exit codes and resists a late
  STARTED save replacing a terminal result. Report preference and recovery
  restrictions remain separate from safe, explicitly confirmed shutdown.
- The live startup fallback and kiosk power paths must prove engine absence.
  The kiosk also checks executable identity because descriptor execution may
  not give the process the name `nwipe`.
- Manifest/checksum publication binds accepted bytes and prior-output snapshots;
  build rollback and receipt/launcher handoff refuse replacement collisions.
  QEMU evidence is rebound before finalization. Producer failures propagate.
- UI changes cover French UTF-8 shutdown confirmation, method-consistent ETA,
  partial-volume mute state, causal accessibility checks and owned reader/audio
  cleanup. Windows fixtures distinguish native denial from a performed mutation.

Focused regressions accompany these changes. No engine, method mapping,
approved claim, release version, dependency pin or workflow trigger is changed.
The boot exclusion, owner/token/countdown and separate Erase now gates remain.
Companion and USB Easy Use are outside this change.

## Verification performed on this integration

All checks below used the combined source, not the older review worktrees:

| Check | Actual result and limit |
| --- | --- |
| Ruff plus prescribed production/test security selections | Exit 0 for each; static Python checks. |
| Prescribed developer-tool formatting | Exit 0, 20 files already formatted. |
| Mypy, Linux 3.11 typing target | Exit 0, 52 source files. Existing untyped-body notes remain for audio jobs and recovery initialization; this is not Linux execution. |
| Python compilation without executing modules | Exit 0, 747 files at the initial integrated scan. |
| Windows portable developer suite | Exit 0: **473 passed, 4 skipped**, 477 collected. The Linux launcher fixture, two POSIX descriptor cases and legacy POSIX shell case remain unavailable on Windows. |
| New security regression-body replay | Final exit 0, **41/41** fake-boundary cases. Initial integration replay found two failures because its new idle fixture omitted journal state required by the newer controller. The fixture now sets `_session_store=None`; no assertion was weakened. The original failed receipt is retained. |
| JavaScript syntax and diff whitespace | Exit 0 for each. No browser restart, firmware or power action exercised. |
| Lab doctor, sync, plan, report and receipt verification | Exit 0, preparation/receipt integrity only at Lab `d3d0959`. No dirty-source adapter qualification. |
| Publication hygiene | Selected files inspected for private-key/token/worker-access patterns. No hits in that bounded scan. No media, generated binaries, environments, credentials or raw device inventories are included. This is not a universal secret-detection guarantee. |

No aggregate count combines overlapping model runs. The Windows suite executes
developer fixtures and exact-AST controls; it does not execute the installed
Linux product or qualify native syscalls, GTK/Orca, the ISO or QEMU. Earlier
advisory and pure signing/privacy probes remain at their recorded source and
scope; the complete installed Linux dependency/image scan is still required.

The [portable replay](evidence/security-main-handoff-20261027/probes/run.py)
reads exact checked-out source/test AST and uses fake OS, descriptor, process
and power boundaries. On an ordinary development machine, choose a **new
internal regular-directory output**, outside the checkout:

```bash
python3 -B docs/evidence/security-main-handoff-20261027/probes/run.py \
  --output /path/to/new-internal-evidence-directory
```

On Windows use `py -3 -B` and an internal Windows path. Reusing an output
directory is refused. The receipt binds source and harness bytes and retains
the actual exit; it is explicitly source/model evidence.

## Resume on another machine

1. Fetch the proposed branch from GitHub, use a clean **normal checkout**, read
   its current `AGENTS.md` and the canonical [unfinished work](../.ai/memory/unfinished-work.md).
   Record `git rev-parse HEAD`, current main, status and the PR's exact head.
   Do not use the old Windows root checkout as the source of this checkpoint.
2. Read every PR summary, review, inline comment and earlier round. Resolve
   valid findings and document disputes with evidence. No final combined-diff
   independent approval is supplied by this checkpoint. Read the final-head
   Greptile review; if it cannot complete, follow the explicit independent
   review fallback in `AGENTS.md`. An unavailable review is a blocker.
3. Inspect the PR's existing `ci.yml` run first. Opening/updating the PR runs
   full Blacksmith Linux/ISO/QEMU and native Windows gates; do not dispatch
   duplicate jobs. `CI gate` must pass with every required phase and receipt.
   Preserve the PR merge SHA and its base/head parents. Fix actual failures,
   then rerun affected gates without changing assertions, skips or timeouts.
4. Local full acceptance requires an admitted isolated x86_64 Linux worker
   with no host-disk passthrough. Follow [CI](ci.md), [development](development.md)
   and [remote development](remote-development.md), including display 72 DPI,
   GTK/ATK, Orca containment, source/security/negative/launcher tests and pinned
   tools. Use `python3 -m pytest` and `./scripts/test-all.sh` only after reviewing
   their complete environment/child/cleanup requirements. ISO/QEMU additionally
   require disposable-worker admission, private file-backed fixtures, sufficient
   capacity and actual KVM; no software-emulation substitute or host devices.
5. Merge through the protected PR path only after required checks and current
   review/safety gates pass. Then verify main and its exact main-push run. Do
   not call a PR run or cross-build main/release acceptance. Do not invoke
   legacy GCP CI, dispatch `release.yml`, tag, publish or alter signed artifacts.

## Remaining blockers and next actions

- **SECURITY-MAIN-01 / pending:** final-head review, full applicable gates and
  protected merge. Source push is a resumable checkpoint, not completion of
  the security task. The PR/check state is authoritative after this note.
- **SECURITY-WORKER-01 / blocked:** the owner-selected Hostinger KVM2 has no
  confirmed usable key/agent in this Windows session. A proposed public key was
  presented privately for owner installation; installation was not confirmed.
  Do not retry authentication or publish access material. Reported low disk
  space and unsupported nested virtualization also prevent treating it as a
  qualified disposable ISO/QEMU worker. It hosts other work, which must remain
  intact. Existing Mac access does not establish worker isolation or capacity.
- **SECURITY-LOCAL-01 / blocked:** this unattended Windows host must preserve
  its running session, remote access and every physical disk/USB. Falling free
  space has no established cause. No guest, shared cleanup, service change or
  virtualization workaround was attempted for this checkpoint. The first Git
  staging attempt failed with exit 128, `No space left on device`, before an
  index update. Source snapshots remained intact. Automatic approval review
  rejected removal of this pass's disposable mypy cache as blocked by policy;
  no files were removed. A later read reported about 48 MB available. Capacity
  remains unstable and must be rechecked before further local work.
- **TASK119 / NOT TESTED / BLOCKED:** physical reconnect/readback, valuable-disk
  disconnection, firmware trust/revocation inspection and physical Secure Boot
  matrix remain under their original prerequisites. A boot, warm read, model or
  guest result cannot qualify them. No flash/reconnect/firmware step was done.

Original private raw receipts and snapshot bytes remain in the Windows evidence
directory `beamo-release-evidence/security-main-handoff-20261027`, alongside the
older audit packets. Only selected credential-free summaries, source bindings
and reproducible model harnesses are committed here. A different machine can
resume source work from GitHub; unavailable private receipts must be reported
as unavailable or obtained through an approved private transfer, not invented.
