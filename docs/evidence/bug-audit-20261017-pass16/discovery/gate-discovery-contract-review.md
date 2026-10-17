# Source-only discovery contract review while full gate is running

2026-10-17. Requested because parent observed failures in the full gate's early progress, without final JUnit attribution yet. No runtime commands, source edits, retries or termination performed here. This note does not identify or explain those failures.

Inspected all of `tests/test_audit_20260908_discovery.py`, adjacent 20260907 duplicate tests, relevant 20260905 discovery/boot-exclusion fixtures, and source paths touched by the discovery patch. No concrete incompatibility between the current assigned discovery delta and those contracts was found.

- Every20260908discovery `probe` supplies an authoritative `mount_sources=[boot]` and empty cmdline. New cmdline optical competition is therefore bypassed by the existing earlier mount-hit return. Its mounted-optical/loop control similarly supplies `/dev/sr0` authority and remains outside fallback.
- The physical disk rows in those20260908cases have distinct canonical paths. Shared serial/WWN tests describe separate paths (`sda`/`sdb`), so the new repeated-path set remains empty. Duplicate hardware IDs are not duplicate physical observation paths. Partition/mapper children have distinct paths/types and do not become extra physical observations of their parent.
- Existing mounted-stack/unknown ancestry refusal cases reject before selectable construction, unchanged. The single-disk LUKS and bcache-content controls likewise use distinct physical rows and do not enter the repeated-path branch.
- The20260907duplicate contracts remain deliberate: fully valid conflicting core facts already reject; two identical valid target rows remain two selectable observations and are rejected by the existing final identity guard; identical duplicate boot/RO rows do not have one surviving selectable row at their repeated path and preserve unrelated targets.
- The size-label module constructs Disk objects and calls size/confirmation helpers; neither new branch applies. Nearby boot driver tests inspect/execute only inert shell stubs. No new discovery state is global: collections are local per call, so no carryover to clean retries is introduced.
- Current source still has the exact reviewed discovery SHA256 `0e77fcf0fa626e945c40fae8c8e5f544b735490f4acf8c718260abbabb20197f` at this source read.

Remaining next action belongs to parent: allow the original gate to finish, inspect its exact failing test IDs/tracebacks and source snapshot, then diagnose the actual case. Progress position/cache order is insufficient evidence to classify a discovery regression or justify a change.
