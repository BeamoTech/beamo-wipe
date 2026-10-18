# Pass 11 discovery and authorization review

Date: 2026-10-16. Reviewer: Codex discovery child. Repository/worktree:
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, starting HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Existing pass 8 and pass 10
uncommitted source and test work was preserved. This reviewer made no repository
edits, staging, commit, push, hosted CI, device or engine actions.

Result: no additional root-cause defect proved in this bounded review.
This result is not a claim that the application is bug-free.

## Source review

Read current AGENTS.md, memory index and unfinished work record. Shared
`/root/dev/AGENTS.md` remains absent, as already recorded by the parent. The
current instructions preserve local fake-only validation and prohibit host/USB
state changes or unapproved guests. Prior unexplained SIGTERM/timing observations
are not resolved or attributed by this passing run.

Reviewed `discover.py`, `safety.py`, `methods.py`, `identity.py`, relevant
`wizard.py` authorization/refresh/start sections and `nwipe_runner.py` argv
construction/validation. Main paths inspected:

- Native column validation; strict identity text, raw layout identity, display
  sanitation, numerical conversions and disk kind/bus classification.
- Mount versus cmdline versus label boot priority, unresolved and conflicting
  evidence, typed UUID/label resolution, udev aliases, optical media and loops.
- Flat/tree partition ownership, contradictory PKNAME, orphan partitions,
  duplicate mapper ancestry, mounted Btrfs/LVM/RAID/bcache membership refusal,
  shared filesystem and hardware ID mount coverage.
- Whole disk path normalization, boot path/rdev/identity exclusion, native
  transport and read-only/mount gates; final boot and target identity snapshots.
- Distinct confirmation tokens, serial/WWN suffix collisions, missing IDs,
  forbidden kernel-name tokens, strict owner/countdown booleans.
- Refresh/review authorization invalidation, peer set and method binding,
  review overlay countdown suspension, launch claim and preflight failure retry.
- Exactly one target, one boot exclude, canonical method flags, disabled PDF,
  no force, duplicate/unknown argument rejection and off-target log path.

`source-hashes.json` captures the six main reviewed runtime sources and the 51
selected test modules. All 57 hashes matched again after validation.

## Focused test evidence

`selected-files.json` records the exact 51 module selection. `run_focused.py`
uses preview mode and fake machine boundary guards: `/proc/cmdline` and
`/proc/self/mountinfo` reads receive empty text, findmnt receives a controlled
nonmount response, and unmocked subprocess.run acquisition of lsblk/nwipe is
prohibited. Tests use their own controlled fixtures and fake processes.

Final command:

```sh
PATH=/tmp/beamo-wipe-audit-python/bin:$PATH dbus-run-session -- xvfb-run -a -s '-screen 0 1600x1000x24 -dpi 72' python3 /tmp/pass11-discovery/run_focused.py
```

`focused.xml`: 461 PASS, zero failures/errors/skips, 9.020 seconds. Boundary
observations: 16 fake findmnt calls, two fake mountinfo and two fake cmdline reads.

The initial invocation omitted DISPLAY after adding an actual GTK operation
identity case: `initial-missing-display-focused.xml` records 458 PASS, one Gtk
initialization setup failure, two DISPLAY-dependent skips, 8.242 seconds. Its
trace is retained. The corrected private72DPI invocation reran the same full
selection and executed all 461 cases. No test assertions/source/thresholds were
changed to address this harness error.

## Additional fake inventory matrix

`matrix.py` runs only injected fake payloads, with subprocess.run/Popen and
native proc/sys file reads explicitly prohibited. `matrix.json` retains every
case and outcome, plus a deterministic observations digest.

588 cases PASS, consisting of:

- 540 combinations of USB/optical boot, SATA/NVMe/virtio targets, tree/flat
  partition shape, five mount schemas, correct/missing/contradictory parentage
  and ext4/NTFS/LUKS contents.
- 36 direct/partition/UUID/label/PARTUUID/PARTLABEL boot cases with unchanged,
  conflicting, missing, overlay or loop evidence.
- Eight hardware alias cases: shared serial, shared WWN, shared serial with
  distinct WWNs and all-zero missing serial, mounted/unmounted.
- Four duplicate disk cases: identical observations remain unable to satisfy
  the unique final identity gate; size, read-only and mount contradictions
  refuse all targets.

67 cases retain their expected eligible targets; 521 have the expected empty
safe list. Every boot disk remains excluded. Zero native acquisition attempts.
The matrix performs no erase or runner start, and writes only temporary regular
file evidence.

## Limits and next action

The focused count overlaps existing gates and is not additive coverage evidence.
It does not qualify ISO/QEMU, native Windows, physical boot/USB/reconnect/hardware,
or resolve the historical interruption and GTK timing attribution. Parent owns
full integration, the durable canonical checkpoint and disposition of remaining
blockers. No changes are proposed from this review.
