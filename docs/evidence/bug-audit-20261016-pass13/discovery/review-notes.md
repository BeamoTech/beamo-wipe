# Pass13 discovery, authorization and classification review

Date/reviewer: 2026-10-16 / Codex discovery child. Repository/worktree/ref:
BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`, `fix/safety-audit-20261015`,
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`. Read current AGENTS.md and
the current unfinished audit records. The previously recorded continuation for
missing `/root/dev/AGENTS.md` applies; no new permission is inferred from notes.
Preserved all prior dirty source, tests and evidence. No staging, commit, push,
hosted CI, external messages, native inventory/engine, physical device, USB,
power/firmware, guest or network operations.

## Proven defect and minimal fix

`_contents_from_evidence()` treated any occurrence of the letters `efi` in a
GPT PARTLABEL/PARTTYPENAME as EFI evidence. Plain data partitions named
`Benefits` or `Definitions` therefore received Windows-removal instructions for
NTFS and operating-system-removal instructions for ext4. Existing contract:
`tests/test_prepare_aftercare.py::test_ntfs_data_without_windows_marks_is_not_a_windows_claim`
and `test_data_disk_has_no_os_partitions`; `copy.prepare_selected()` maps the
classification to the actual owner-facing consequence copy.

Before editing, the root granted a sole runtime slot for
`candidate_trace.py`: all eight unrelated-name combinations were misclassified,
and eight genuine EFI/UEFI controls retained expected classification. Exact
16 records and output are in `candidate-trace.json` and `candidate-trace.log`.
The original source is `discover-original.py`, SHA256
`6528038ba87a46e2d58957cccdbf1a7b963d77b9961b724883f7809e93e9c7a4`.
Root reviewed the trace and contract before authorizing product edits.

Only `src/beamo_wipe/discover.py` and a new regression module were edited by
this reviewer. The compiled pattern `(?:^|[\W_])u?efi(?:$|[\W_])` recognizes
EFI/UEFI name tokens, retaining spaces, punctuation, underscores and dashes as
separators while keeping adjacent Unicode letters inside a word. All exact
firmware labels, type GUIDs/codes, ESP and independent Windows/BitLocker markers
retain their prior path. `discover-change.diff` is the complete product diff.
No eligibility, boot exclusion, hardware/layout identity, token, countdown,
method or argv code was changed. The project guide requires a future `safety:`
commit for discovery changes; no commit is made while acceptance is pending.

Final source SHA256:
`b45a4a32953ac47d0b1b69fc98a1c8f1f2295704e15de677f5b88f3ee33d58e2`.
Final `tests/test_contents_efi_token_pass13.py` SHA256:
`7e0e2fcc2504df6efa84a57453c8183e0f2c8c607e8b863a4c70f4f036338539`.
Its104 cases cover32 unrelated ASCII/Unicode name cases,40 genuine EFI/UEFI
name controls, and32 independent firmware/Windows controls. Tree/flat ownership,
both GPT fields and NTFS/ext4 are exercised. Every case checks boot exclusion,
exact selected target/size/serial, token128 and the appropriate preparation copy.

## Serialized command and result receipts

All campaigns ran only during the root's explicit sole runtime grants. Owned
commands exited before releasing the slot; other reviewers remained source-only.
Python uses the already installed pinned audit environment; no installs.

```sh
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH python3 /tmp/pass13-discovery/candidate_trace.py
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH python3 /tmp/pass13-discovery/nested_trace.py
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH python3 /tmp/pass13-discovery/original_proof.py
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH python3 -m pytest -q tests/test_contents_efi_token_pass13.py --junitxml=/tmp/pass13-discovery/fixed.xml
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH python3 /tmp/pass13-discovery/namespace_matrix.py
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH dbus-run-session -- xvfb-run -a -s '-screen 0 1600x1000x24 -dpi 72' python3 /tmp/pass13-discovery/run_focused.py
```

All command/wrapper exits0. The original-source inner pytest intentionally
exits1:104 cases,32 intended failures,72 passing controls,0 errors/skips,
0.698s JUnit suite duration. The script privately extracts all58 exact starting
source/static files, checks original discovery bytes, and copies the final
test/conftest into that import root. Shared checkout is never reverted.
`original-proof.{json,log,xml}` and `original-proof-summary.log` retain proof.

Fixed regressions:104PASS,0 failures/errors/skips,0.452s JUnit suite duration;
`fixed.{log,xml}`. Adjacent selection:644PASS across54 modules,0 failures/errors/
skips,9.846s JUnit suite duration; `focused.{log,xml}`, `selected-files.json` and
`run_focused.py`. Counts overlap and must not be added to the final full gate.
The focused guard recorded16 fake findmnt calls and two each empty fake proc
mountinfo/cmdline reads; native lsblk/nwipe acquisition is forbidden. GUI tests
use an owned private Xvfb at72DPI and D-Bus session, never shared display :1.
`summary.json` independently parses all case counts and duplicate IDs.

The fresh namespace matrix passes156 cases across hda/dasda/xvda/mmcblk0/
nvme0n11/vdz and tree/flat inventories. Each namespace has a normal accepted
case and12 mounted/RO/zero/duplicate/boot-alias/serial/layout/ancestry mutation
cases that cannot satisfy the previous exact target snapshot. Partitions remain
refused as whole-disk targets and the boot path is never selectable. Unknown
hardware is represented by inert strings, injected rows and regular temporary
files. Subprocess acquisition and proc/sys/dev file opens are forbidden;
zero native attempts. `namespace-matrix.{py,json,log}` retain all observations;
observation SHA256 `daeced50d90a19e1b682661ecac3bd9538bb690fa68bb63f02e90de5a5e438e5`.

## Other source review and candidate dispositions

Read/reviewed discovery's native columns/schema/duplicate fields, identity and
Unicode sanitation/lengths, exact byte sizes, whole-disk and partition naming,
tree/flat ownership, duplicate/contradictory observations, mounted-holder/shared
filesystem/hardware-alias closure, and typed/live/cmdline/label boot resolution.
Reviewed safety's local/remote transport and sysfs refusal, whole-device/rdev/
size/log checks, hardware alias canonicalization, token collision rules and exact
rediscovery identity. Reviewed models/identity presentation/method mapping, and
wizard ownership, selection/token, displayed peer binding, countdown/overlay,
refresh/stale completion, preflight launch and retry invalidation boundaries.
Existing local pass8/10/11/12 changes are preserved; this classifier fix is
independent of their runner/UI state changes.

Nested whole-disk topology was traced without a speculative fix. Four fake
records (`nested-trace.{py,json,log}`) show a mounted child closes the physical
parent's targets, and mounted bcache refuses the entire unresolved inventory.
An unmounted kernel whole-disk child can remain an independent explicit target;
no supported physical topology, hidden mount or violated current contract was
established. Generic rejection would risk legitimate stacked topologies, so no
ancestry behavior was changed. Other reviewed boundaries yielded no additional
proved defect in this bounded pass.

`source-hashes.json` records six reviewed runtime modules and all54 selected
test modules. Historical pass8 SIGTERM source and pass9 timing attribution
remain unresolved; these passes cannot establish their causes. Parent owns
independent proof/review, final freeze/full local gate, artifact checks and
durable canonical evidence. ISO/QEMU/native Windows/physical/firmware/reconnect
qualification remains unrun and is not replaced by these fake local checks.
