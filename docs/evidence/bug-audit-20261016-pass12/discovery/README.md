# Pass12 discovery and authorization review

Date/reviewer: 2026-10-16, Codex discovery child. Repository/worktree/branch:
BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`, `fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Existing pass8/pass10/pass11 local
uncommitted changes were preserved. This reviewer made no repository source,
test, canonical memory/report, staging, commit, push, CI, network, guest, physical
media, power/firmware or engine changes.

Result: no additional discovery/authorization root-cause defect proved by this
bounded review. The fresh matrix and selected focused tests pass; they do not
prove the application is free of bugs. Historical SIGTERM/timing attribution
remains unresolved; passing checks here cannot establish those original causes.

## Source review and boundary disposition

Read AGENTS.md, the relevant memory index/unfinished audit record and source.
The missing shared `/root/dev/AGENTS.md` is unchanged and already handled by the
parent's recorded owner continuation. Reviewed `discover.py`, `safety.py`,
`models.py`, `identity.py`, `methods.py`, relevant wizard authorization/refresh/
launch code, and runner argv/construction/final identity calls. Receipt
`source-hashes.json` records six main source modules plus all51 selected test
modules. All57 hashes matched again after validation.

Reviewed current behavior and failure boundaries:

- Native lsblk column/schema validation, duplicate JSON fields, identity
  sanitation, length/control handling, integer conversion and capacity units.
- Live mount priority, contradictory/unresolved mount sources, stale cmdline,
  typed UUID/LABEL/PARTUUID/PARTLABEL resolution, absent/disagreeing udev links,
  aliases and subvolume brackets, optical/loop media and label fallback.
- Flat/tree partition and holder ownership; orphan, cyclic, duplicate and
  contradictory ancestry; mounted RAID/LVM/Btrfs/bcache refusal and shared
  filesystem/hardware ID mount coverage.
- Whole disk-only normalization, boot/target alias and rdev distinctions,
  read-only and any-mount exclusion, local SCSI/NVMe transport gates.
- Confirmation token collisions across size/serial/WWN/kernel names, strict
  owner/countdown booleans, operation/method/peer binding, overlay countdown
  reset, final target/boot identity snapshots and retry invalidation.
- Exactly one canonical target and boot exclude, canonical three method flags,
  disabled engine PDF, forbidden force/unknown/duplicate options, protected
  temporary log location.

Source-level peer-arrival candidate was investigated and rejected as an
unproved bug: the wizard explicitly binds displayed peer inventory at its final
rescan; the runner's subsequent under-lock rediscovery contract rechecks target
and boot identity, and its request remains exactly one explicitly named target.
An unrelated later peer cannot redirect that target. Current explicit task/docs
require fresh boot/target identities and do not establish an identical entire-
inventory check at every defense layer. No speculative source change proposed.

## Serialized focused validation

The parent explicitly granted a sole runtime slot after other test/GUI jobs
retired. Root and sibling reviewers performed source-only work during these jobs.
Commands, in order:

```sh
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH python3 /tmp/pass12-discovery/matrix.py
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH dbus-run-session -- xvfb-run -a -s '-screen 0 1600x1000x24 -dpi 72' python3 /tmp/pass12-discovery/run_focused.py
```

Both exits0; `matrix.log`, `focused.log`, exit files and `focused.xml` retained.
The owned private Xvfb/D-Bus test job retired before the slot was released.

`selected-files.json` names51 modules. JUnit independently parsed as461PASS,
zero failures/errors/skips,8.003s. The controlled host boundary guard provides
fake findmnt results and empty proc text; unmocked native lsblk/nwipe acquisition
is forbidden. Observed16 fake findmnt calls, two fake mountinfo and two fake
cmdline reads. Individual tests provide their own controlled fake fixtures and
processes. Counts overlap the parent's eventual full gate.

## Fresh fake-only matrix

`matrix.py` uses injected inventories and prohibits subprocess.run/Popen and
proc/sys/dev file opens. Diagnostic emission is stubbed. Paths are inert device
strings and output consists of ordinary files under this evidence directory.
Zero native acquisition attempts recorded.

All1455 cases pass, with unique labels and deterministic observation SHA256
`f77ca9172febc0ddd3c927d624233dad70b117b1cd1bc53e3a1c2d81bc6bfdb0`:

- 510 identity/mount/read-only mutations over SATA/NVMe/virtio and tree/flat
  layouts:507 changed/mounted/read-only/malformed cases cannot satisfy the old
  selected disk identity; three redundant empty tree-PKNAME controls retain the
  same identity via proven nesting. Root serial, WWN, model, vendor, exact size,
  transport, mount and RO; partition UUID, PARTUUID, label, PARTLABEL, PARTTYPE,
  PARTTYPENAME, FSTYPE, size, mounts, PKNAME and path are exercised.
- 180 combinations of six direct/typed boot sources, unchanged or conflicting/
  unresolved/overlay/loop companions, source ordering/duplicates and empty or
  stale competing cmdline. Mount ground truth is retained when unique; every
  competing unresolved/contradictory source closes the safe list.
- 36 equivalent tree/flat/permuted inventory representations preserve the exact
  selected identity and keep the boot medium excluded.
- 729 three-disk serial combinations over a nine-value adversarial alphabet.
  Every available confirmation token avoids kernel names and is accepted only
  by its own spec.1088 available specs across676 combinations prove the
  uniqueness check is not satisfied by refusing every disk;53 combinations
  conservatively refuse all tokens.

Final source-only assertion review (`matrix-assertion-review.json`) confirmed
explicit Cartesian dimensions and all1455 unique labels. The first postprocessing
count assumption mistakenly expected330 identity and360 boot cases (the1455 total
was correct). That auxiliary assertion exited1; the exact mistake/correction is
recorded in `matrix-assertion-review-initial.json`. Correct dimensions are
(35+50)*6=510 and6*5*3*2=180. No product, focused test or matrix assertions were
changed, and no runtime campaign was rerun to correct that counting mistake.

## Independent runner candidate review

`runner-review.md`, `runner-reviewed.diff` and `runner-review-hashes.json` retain
an independent read-only review of the new prefixed negative-error fix. Source
SHA256 `7672c9c0646aa9679b87d9b729c3f9228f0cf1b7f9bb4b1c162a7e37e16dbf9b`
was approved subject to primary original-source proof and focused/final gates.
The change repairs body/header/count/delimiter consistency for negative evidence;
raw exact positive completion provenance, scanner caps/order, launch/method/argv
rules, cancellation and conservative headerless/shared/no-erase rules remain.
No runtime campaign was run by this reviewer for that source review.

## Remaining work and limits

Parent owns original-source independent proofs, final combined diff/artifact
review, frozen exact-source full local gates and durable canonical checkpoint.
Separate ISO/QEMU/native Windows/firmware/hardware/physical reconnect acceptance
remains unperformed and is not replaced by these fixture checks. No changes from
this reviewer need staging or integration.
