# Remote-only development on the unattended PC

The owner confirmed on 2026-10-13 that the Windows development PC will have
no physical access for an extended period. Keep Windows, remote access and all
connected USBs available. This is an operating constraint for development,
not a new product-support claim. [AGENTS.md](../AGENTS.md#unattended-development-host)
is the canonical agent policy. Do not infer that general task permission or
the previous permission to flash a particular USB authorizes another write.

## Protect the host before running a command

Review the selected command, all called helpers, environment overrides and
cleanup. Do not run an opaque administrator installer or test the production
restart/wipe path on this computer. Read-only disk inventory is allowed;
the disks it finds remain protected, regardless of drive letter or disk number.

| Resource | Rule while unattended |
| --- | --- |
| Windows and its remote session | No restart, shutdown, logoff, sleep, hibernation, firmware boot or deliberate network/remote-service interruption. Do not change recovery, boot or security settings. |
| Connected physical disks and USBs | Keep connected and mounted as they are. No eject, offline/dismount, PnP disable/reset, USB controller reset, USB/IP export, passthrough, formatting, partition changes, raw writes or copier apply. |
| Elevation and dependencies | Use existing tools or installation confined to a new user-owned directory when no reboot, driver, service, security-policy change or inaccessible approval is needed. An unreachable UAC prompt blocks that step; never disable UAC or its secure desktop. |
| Existing WSL2 | Use its normal shell and regular files; do not run `wsl --shutdown`, `wsl --terminate`, `wsl --unregister`, `wsl --mount` or host virtualization setup. Linux `/mnt` access does not make a Windows USB disposable. |
| Local VM/container | Only an already configured environment with new file-backed disks and no physical device bindings. Do not install a hypervisor or alter network adapters on this host as a workaround. Containers share their kernel; a privileged container on the development host is not sufficient isolation for destructive acceptance. |
| Processes and cleanup | Track the exact owned process, unique directory and fixture identity. Terminate/reap only owned test children with bounded waits. Never kill by name, detach all loops, unmount all volumes or delete a shared output/cache. |

The dual-USB workstream uses the common Windows OS byte-locked slot
`%USERPROFILE%\beamo-release-evidence\coordination\vm-slot.lock` for local
guests. Cooperating callers must hold the same byte lock throughout guest
lifetime and teardown, with at most one owned guest, 2 vCPU, 6 GB RAM and
100 GB newly allocated internal storage. Lock contention or an unknown active
VM worker blocks admission. A stale-looking file is not a lease to delete;
never kill a peer or claim an existing VM. On October 13 the other agent's
admission evidence reported an unidentified active Hyper-V worker, so a new
local guest remains blocked. This finding does not prove the worker belongs
to either agent. These local limits do not authorize any new hosted resource.

These instructions do not control unrelated Windows updates, hardware faults
or another operator. Do not promise guaranteed uptime. Preserve work and evidence
outside the host as described below without changing its update/power policies.

## Available development routes

Use [development.md](development.md) for setup and the selected checkout's
pins. A dependency check is not a passing suite. Run commands in a separate
worktree when another agent is editing; do not change that agent's checkout.

| Work | Route | What it proves |
| --- | --- | --- |
| Python developer tools on Windows | `py -3 dev.py doctor --for test-native`, then `py -3 dev.py test --native` | Portable developer-tool behavior, with reported failures/skips; not the POSIX wizard. |
| Python wizard and full local suite | Existing WSL2 Linux checkout, `python3 dev.py doctor --for test`, then `python3 dev.py test` | Local Linux source tests and explicit environment skips. The wrapper enforces fake mode and uses a separate 72-DPI Xvfb when available. |
| Wizard presentation | `python3 dev.py preview --web` in WSL2; `BEAMO_WIPE_NO_OPEN=1` prints the generated file path | Fake-disk flow. Review the generated HTML through the existing remote session; no raw device is opened or wipe engine executed. |
| Launcher presentation | Inside `desktop/`, `go run . --preview` with the selected checkout's Go pin | Inert snapshots and UI behavior; no restart. Do not launch the real prepared-USB executable for this check. |
| Windows launcher unit tests and cross-builds | `py -3 dev.py doctor --for desktop`, `py -3 dev.py desktop-test`, `py -3 dev.py desktop-build` | Native Windows unit behavior and recorded executable hashes. Cross-built Linux bytes are not Linux execution. No native-inventory override on this personal host. |
| Download/signature/component inspection | [Authenticated regular-file USB walkthrough](release-verification.md#usb-image-download-verification) and [component receipt](evidence/secure-boot-119/README.md) | Authenticated downloaded bytes and inspected signatures; not bytes retained on a physical stick or firmware trust. Use fresh regular-file staging. |
| ISO and QEMU acceptance | [Existing full gate](ci.md) on a separately authorized isolated x86_64/KVM worker | Exact-source image and virtual policy/erase-path results. Keep every required phase and receipt; never attach this host's disks. |
| macOS-native, hardware, UAC and real firmware acceptance | An independently available supported platform/lab, with its required recovery and authorization | Unavailable environments remain pending or NOT TESTED. Windows/WSL cannot supply macOS or physical evidence. |

The Windows doctor does not verify Linux wizard prerequisites; run it inside
the existing WSL distribution. A fresh worktree needs its own environment;
do not reuse a venv from another OS. Git Bash is not a replacement for the
Linux runtime. Do not install WSL or reboot to fix its absence during this period.

The inspected WSL distribution is running Linux x86_64, but has no `/mnt/c`
checkout mount and no Go on PATH. Therefore Windows `dev.py` delegation is
not currently a verified route to this checkout. Do not repair that by mounting
host devices or changing shared WSL configuration. When existing repository
access is available, clone the selected source into a new directory on WSL's
own filesystem, check out its exact full SHA, and create a Linux venv there.
Alternatively use an authorized regular-file source transfer with verified
identity. Keep the received source/dirty diff bound to the tests; do not use
an old Linux copy as evidence for a newer Windows checkout. If source access
or dependencies are unavailable, retain that local Linux gate as blocked and
continue Windows tooling/source work. Merely listing a WSL distribution does
not establish its checkout, dependencies or mandatory coverage.

From a Windows checkout at the usual user-profile location:

```powershell
Set-Location -LiteralPath (Join-Path $env:USERPROFILE 'beamo-wipe')
py -3 dev.py doctor --for test-native
if ($LASTEXITCODE -ne 0) { throw 'STOP: repair the reported local prerequisites safely' }
py -3 dev.py test --native
if ($LASTEXITCODE -ne 0) { throw 'STOP: local developer-tool tests failed' }
```

Adjust the checkout path explicitly for a worktree. For Linux wizard tests,
open the already running WSL distribution, select its Linux checkout, and use
the commands in [development.md](development.md). That guide's `setup` creates
a checkout-local venv; OS/WSLg installation instructions do not authorize
host reconfiguration during unattended operation.

## Simulate interruption without interrupting the PC

| Case to exercise | Safe development method | Evidence limit |
| --- | --- | --- |
| USB disappears or is replaced | Inject missing, replaced, short-read or changed inventory/file identities in the existing unit-test fixtures. In an isolated VM, hot-unplug only a new virtual USB backed by a run-owned regular file. | Tests the software refusal/recovery; not electrical unplug/reconnect or a physical controller. |
| Copy/readback mismatch | New temporary directories/files; corrupt a fixture and require refusal. Never direct the test at a mounted real USB, even for an add-only operation. | Tests comparison and collision handling; not cold media durability. |
| BootNext, db/dbx, shim/SBAT policy or permission errors | Existing fake firmware, read failures and controlled OVMF variable-file copies on the isolated worker. Never edit this host's variables or validation state. | Establishes the modeled policy only; the actual firmware database remains unknown when unreadable. |
| Boot, reboot and recovery | Guest-only reboot with file-backed guest disks and recorded console/serial/QMP output on the isolated worker. Windows remote desktop is not a firmware or live-USB console. | Virtual boot evidence; no physical acceptance. |
| Timeout, failure, cancellation, descendants and cleanup | Harmless owned children with synchronization, bounded termination/reaping and an unrelated sentinel; scoped fixture ownership checks for cleanup. | Demonstrates tested ownership and bounds, not universal provider teardown. |
| Space exhaustion, read-only access and stale evidence | Fault-injected files/API responses, bounded disposable storage and new run IDs/directories. Do not fill the system disk or change physical-disk configuration. | Tests the intended failure; stale/partial outputs cannot qualify the current source. |

The test suite already contains these kinds of fixtures. Reuse the established
helpers and preserve the negative safety assertions. Do not convert a failing
assertion or a mandatory native test into a skip to keep remote development green.
If a proposed test cannot be made harmless, leave it unexecuted with its exact
reason; do not run it against this host to obtain a receipt.

## Physical work stays deferred

The [physical safety and post-flash procedure](evidence/physical-acceptance-111/README.md)
requires a spare machine, physical removal of valuable disks, and a real
reconnect after flashing. It explicitly excludes this development host. Keep
that procedure intact. Do not substitute software eject/re-enumeration,
filesystem cache flushing, disk offlining or a warm read for those prerequisites.

The prior Q12 image authentication, writer completion and verification-screen
observations remain separate evidence. They do not supply the still-missing
independent post-flash readback. This host's currently visible volume letters
do not establish the stick's serial or the Mac's former device identifier.

All unexecuted physical Secure Boot cases remain **NOT TESTED**. Missing media
inspection is **BLOCKED / SB-INSPECTION**; unknown firmware databases/revocations
remain **UNKNOWN** and denied inspection remains **INSPECTION FAILED**. The
[acceptance matrix](secure-boot-acceptance.md) still governs: even an observed
guide screen cannot qualify an unknown trust/policy state.

To resume physical work later, obtain a new owner-confirmed session with the
dedicated spare machine and valuable disks disconnected, verified media,
physical handling and a working firmware/live-environment recovery/evidence
channel. An existing independent hardware KVM may provide a console but does
not physically remove disks or reconnect the stick. Do not reboot first and
try to arrange recovery afterwards.

## Coordinate, retain evidence and preserve gates

Before editing, read the relevant other-agent branch/PR and local worktree
status. Record the baseline SHA and agree file ownership through an available
authorized channel. Fetch/read updates without switching the other agent's
branch or discarding its files. A posted note is not proof that the agent read it.
Recheck the final head before applying a documentation patch or reusing tests.

For this session, the dual-USB agent owns its remote-control wrapper, VM
admission/lease tests and task crosswalk in its separate checkout. The Wipe
agent owns the Wipe/Easy Use unattended-host guidance and local source checks.
Keep new peer messages under the shared coordination directory in separate
files; do not rewrite the other agent's packet or claim its tests as ours.

Use new run directories on the fixed development volume or a Linux worktree,
never on a connected USB. Record repository, tested SHA/tree, dirty diff,
OS/tool versions, exact commands/exits, test/skip reasons, artifact hashes and
cleanup outcomes. Keep sensitive raw logs local/private. Export a checksummed
bundle to an authorized location and verify its readback so a later agent can
continue without Windows access. A private link requires the recipient's access;
do not promise anonymous download or share credentials.

Review [automatic CI triggers and publication rules](ci.md) before any push,
PR or dispatch. This documentation work does not request hosted CI. Final
public/customer candidates still require the applicable exact-source gates;
release publication is separately authorized. Do not invoke legacy Cloud Build,
re-enable Wipe Cloud gates, change IAM, weaken approvals/coverage, or mark an
unavailable gate passed to avoid physical access. A needed but unavailable
check is a recorded release blocker, not a reason to stop safe development.
