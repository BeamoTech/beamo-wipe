# Beamo Wipe comprehensive bug audit, fifth pass

This fresh audit starts from `e4871239f02e46137fb6d8df64b5880ae2ea4b4d`
on `fix/safety-audit-20261019`. It repairs five independently proved root causes:
unbound recovery reads, terminal quiet-interval bypasses, lost terminal key
origins, an unchecked Linux live-state read, and a blocking log-file open. All devices, inventories,
process/firmware inputs and media were fixtures or ordinary temporary files.

| Trigger and previous behavior | Result after repair | New coverage |
| --- | --- | ---: |
| A journal is replaced after its old descriptor opens; recovery accepts the stale valid journal while its name refers to foreign content. | Compare the opened private regular file to its nofollow named entry before and after reading. Replacement, removal, links and directories refuse; a post-open disappearance cannot trigger fresh-journal creation. | 47 Python cases |
| F5, an overlay or a suppressed key returns before quiet-time bookkeeping; held Enter can confirm refresh or advance another screen prematurely. Separately, Space/S history resets outside action screens, letting repeats grant owner consent, toggle sharing or confirm Stop after a transition. | Record key history before early returns, preserve origins across screens, and observe real quiet intervals inside overlays. Fresh controls and repeated literal keyboard/token input retain their behavior. | 40 shared Python cases for the two terminal defects |
| Linux cannot read the live marker but continues probing; a matching fake USB/EFI route yields a ready guided-restart offer. | Return an unverified runtime state before media, inventory or firmware work. Consistent guidance says to keep the computer on; known normal/live/platform/legacy behavior remains covered. | 1 Python integration case containing 15 named Go scenarios |
| A same-owner/root actor replaces a validated regular log with a FIFO; runner startup blocks in the write-only open while holding the wipe lock. | Open nonblocking before existing inode validation. FIFO refusal releases ownership without launching an engine; ordinary logs and corrected retry still work. | 9 Python cases |

Root independently replayed the original failures before authorizing edits:
recovery 2 failures/1 control, shortcut Enter 1/1, owner Space 1/1, pre-Working
S-to-Stop 1/1, FIFO log open 1/1, and Linux 1 failing/2 passing named scenarios. Expanded baseline
coverage records recovery 29 failures/18 controls, terminal 18/22, and Linux
7 failing/8 passing named scenarios; the final FIFO module gives 3 failures/6
controls on archived source. Go parent status is counted separately.
All **97 new Python regression/control cases** now pass. The integration's
one Go parent and 15 scenarios also passed independently with the race detector;
they are within one Python case and are not added to its count. The eleven
original external Python proofs and original Linux normal/live/error proof pass
unchanged after repair. No existing test file or assertion was changed.

The complete final source gate records **11,154 main cases passed, 28 unchanged
unverified skips, and one separate Orca case passed**: **11,155 unique Python
passes**, with no failures/errors. All 11,085 prior main test IDs remain and
exactly 97 were added; skip IDs and reasons are identical. Focused, supplemental
and embedded Go executions overlap this coverage and are not summed into it.
The compressed JUnit files and summary preserve exact identities and hashes.

Configured lint/security/shell checks, default mypy (52 source files), preview,
private negative safety mutation, uncached Go race tests, vet, 350,000 fuzz
executions, launcher cross-builds and Windows test cross-compilation pass.
Root verified PE32+/ELF64 x86_64 headers, exact launcher hashes/build receipt,
source digest and executable entrypoint modes. The actual fake preview was
visually inspected at 72 DPI on a private display and closed through its
registered window callback with exit 0. Its image stays outside Git; its hash
is retained. Nine unchanged supplemental browser assertions passed with explicit
system Chromium 155, which does not qualify the missing pinned browser.

The initial rotated runner review found no additional proved defect: 1,380 existing
cases passed; a seeded 2,000-log comparison across three methods preserved
exact full-log/projection outcomes and check payloads. Root independently
replayed that comparison. Read-only review of pinned nwipe source confirms
the serial normalization/length and status-model limits; its source URL/hash
receipt is retained. No native engine was executed.
Root's final safety review then found the FIFO hang; the runner follow-up proved
and repaired it. Its 207-case adjacency passes. This is narrow availability
hardening for same-owner/root replacement inside the private log directory;
no normal Beamo path creates a FIFO, and no unsafe erasure or unprivileged
attack is claimed. The initial no-finding runner receipt remains historical.

Root discovery/safety review passed 1,527 existing cases on a private 72-DPI
display, then checked 192 equivalent flat/nested inventory scenarios. Another
3,000 generated inventories produced 10,509 views: 7,436 confirmable views,
3,073 ambiguous refusals and zero cross-disk confirmation-token collisions.
Acquisition guards prohibited real inventory, process and device access.
Recovery/report adjacency passed 1,026 cases, UI/controller adjacency 300, and
boot/developer adjacency 288. A 396-case sharing/privacy matrix across outcomes,
languages and identifier forms found no redaction, semantic or original-byte
preservation failures. These runs are supporting evidence, not extra unique
canonical passes.

All **804** frozen runtime/test/build inputs matched throughout final execution.
The manifest SHA256 is
`fcbe3ad83409ba91557fb5cd8584d25a42e72d3e71d4a7657e5b6cbc154144de`.
Run `python3 docs/evidence/bug-audit-20261021-pass5/verify_retained.py` to verify
source bytes, retained artifacts, exact JUnit identities, prior skips and separate
Go results. Earlier manifests apply to their own earlier source. Proof scripts
retain their original workspace paths; baseline commit and red reports identify
the source used before repairs.

Intermediate failures remain separate from passes. The first terminal candidate
did not observe quiet events inside an inventory overlay; three new fresh-key
controls exposed overblocking. The final candidate fixed that without weakening
those controls or old assertions. Earlier new-fixture failures omitted fake
block metadata or review painting and were corrected before genuine red runs.
The first Linux candidate had an obsolete Go error-variable redeclaration;
the retained history is explicitly a summary, since its original stdout was
overwritten during development. Original red/control JSONs are retained.
Missing-display and import-path setup failures were corrected in owned private
sessions. Root's first lint invocation omitted the preinstalled-dependency flag
and attempted unprivileged apt bootstrap; the corrected invocation runs unchanged
checks against the existing image. The lint TODO warning matches the existing
placeholder-detection regex.
The initial full source run was canceled before the late FIFO repair and is
explicitly superseded, not passed. A fresh complete Python/GTK/Orca gate and
affected lint/preview/negative checks use the final 804 inputs. The already
successful Go component group is reused only after exact comparison of every
desktop input and its build script: those bytes did not change. Its uncached
race, vet, fuzz and cross-build evidence remains separately identified. The
new FIFO fixture's initial FD-accounting error and an adjacent collection-path
error are retained; corrected behavioral coverage passes without old-test edits.
The first completed full run passed the same 11,155 cases but exposed nine
Python warnings from the FIFO helper forking after GUI threads had started.
That run is also superseded. The final helper starts a fresh process, with
unchanged assertions and owned-child cleanup; a strict post-thread control
and a fresh complete gate verify the warning is resolved. Warnings were not
filtered or suppressed. The final canonical Python run has zero warnings.
An earlier preview image was captured after its title appeared but before its
welcome body painted. It is retained outside Git as an incomplete capture.
The inspection helper now observes the actual welcome text before capture;
root inspected the completed image and normal close again. No product defect
or runtime change resulted from that capture correction.

The 28 Python skips remain open: 14 generated-image/artifact checks, 9 pinned
browser checks, 4 Microsoft documentation network checks and 1 legacy gcloud
check. Full Go separately skips native inventory (not opted in) and Windows
inventory (PowerShell unavailable). Managed network observations are current and
report enforced restricted policy; the required browser/documentation hosts
remain unavailable. No policy/proxy bypass or credential discovery was attempted.

Remaining qualification requires the supported environment allowlist update,
pinned-browser installation and affected checks, followed by separately authorized
isolated ISO/KVM and native Windows/macOS qualification. Actual firmware,
physical media and physical reconnect/readback remain unverified. Cross-builds,
Python 3.10 grammar checks and fake fixtures do not qualify those platforms.
Named-file checks do not claim atomic filesystem compare-and-swap.

The retained build receipt records baseline HEAD with `source_dirty=true` during
frozen-source testing. Development launchers were rebuilt after the local commit
from clean HEAD; the external final delivery receipt records that identity.
No actual nwipe, native disk inventory/mount/write, guest, host power/firmware
change, hosted workflow, PR, merge or release occurred. Source/evidence are
committed locally; remote publication remains pending the prior approval review.
No remote mutation was attempted this pass. The canonical backlog links this
report; full operational checkpoints and exact final delivery details stay under
`/workspace/beamo-tools/audit-pass5-20261021/root/` outside Git.
