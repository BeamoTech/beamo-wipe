# Pass15 safety-context repair considerations (source only)

No implementation is authorized to this reviewer. These are options for root
to assess after independent proof, not final patch approval.

## Hardware observations

A defaulted `DiscoveryResult` tuple of safety-only physical observations is a
clean way to preserve the full boot guard context without adding hidden or
malformed rows to `disks`, `selectable`, `listed_disks`, confirmation peers or
display nesting. Existing callers construct DiscoveryResult by keywords and
can retain the empty default; manually constructed results still receive the
existing disks/selectable guard context.

The closure only needs path, serial and WWN; mounted propagation additionally
needs effective mountpoints (including flat child mounts). A safety projection
should validate those fields without consulting model/vendor/volume label/
filesystem layout display parsing. Malformed identifiers must not be repaired
into another identifier. A minimal non-eligible Disk projection (zero capacity,
unknown kind, empty display fields) can reuse the current closure, or a small
dedicated record can express the narrower contract. Do not accidentally feed
these projections to disk_identity or selection.

Prefer using the full physical-observation context consistently for:

1. discovery boot closure;
2. mount propagation from each original mounted anchor;
3. final assert_boot_excluded, in addition to disks/selectable.

Keep anchor WWN filtering exactly as pass14. A hidden bridge does not waive a
known contrary anchor WWN. Keep optical and eMMC boot/RPMB areas non-targets.
`tests/test_malformed_mounted_alias_regression.py` explicitly requires hidden
unmounted rows to remain out of disks and selectable, while mounted malformed
physical rows fail closed and unrelated unmounted malformed display data
preserves the valid target. Existing pathless-node skip behavior must survive.

`session_recovery.py` serializes discovery.disks explicitly with asdict(Disk),
not asdict(DiscoveryResult); support export also uses disks explicitly. An
additional defaulted context does not automatically enter those stored reports.
Recovery reconstructs non-selectable historical DiscoveryResult and does not
authorize a new wipe. No persistence migration appears necessary solely for
this context, but root should verify all consumers.

## Duplicate observations, pending runtime proof

A full ID context may fix boot aliases while leaving same-path safety conflicts
hidden by per-row metadata errors. Reconciliation of repeated physical paths
must consider every raw physical observation before display/layout skips.
The prepared36-case probe tests explicit RO, serial, WWN, size, bus and mounted
conflicts against valid/overlong-model/overlong-layout variants and both orders.

If verified, a small pre-filter repeated-path check could refuse conflicting or
unparseable repeated observations while preserving unrelated malformed-row
skips. Compare the real safety/identity facts rather than merely parsed display
Disk objects. Avoid rejecting harmless repeated equivalent rows that current
contracts deliberately retain for the final unique-target check. Do not infer
that missing metadata equals safe metadata on a duplicate physical path.

## Regression shape

- Full240-case original probe retains visible controls, four omitted bridge
  representations, two protected chain forms, contrary/unrelated controls,
  boot/mounted anchors and six orders.
- Include hidden `mmcblk0boot0` as an adjacent physical-observation case; the
  current mounted-hidden contract already uses this representation.
- Construct a leaf whose is_boot/mount flags are reset and verify final boot
  guard still sees the retained bridge.
- Malformed unrelated display-only metadata remains excluded while a valid
  separate target remains eligible; invalid hardware IDs do not become aliases.
- Tests must assert hidden rows never enter selectable/confirmation peers.
- Duplicate regression should prove the original failure independently and
  preserve explicit valid-conflict/mounted failure controls and retry recovery.

## Refined field and fallback contract

The alias/mount projection needs only canonical path, name, reported serial,
reported WWN and effective mountpoints. For pre-filter same-path conflict
checks, retain parsed size, normalized bus/transport, rotational kind,
read-only state and hotplug separately as well. They should not consult
display model/vendor or filesystem label/layout. Existing later full-Disk
conflict reconciliation still catches two fully parseable rows with different
model/layout/content metadata.

- Use `node_path()` / `_identity_text()` for path and name without repairing
  controls, padding or path mismatch. The existing path/type identity scan
  should continue rejecting contrary name/path observations. Pathless isolated
  malformed rows must retain their existing per-node skip behavior.
- Use `_hardware_identity()` for serial/WWN. Preserve current empty-parent
  fallback to `_first_descendant_field(node, 'serial'/'wwn')`, so a bridge with
  IDs only on a partition does not disappear. Keep prefix/case normalization
  only inside canonical_wwn/alias comparisons; stored values stay intact.
- A core field error after a usable physical path is established creates an
  ambiguous physical observation. Do not shorten or scrub it into a usable
  ID. Root should fail closed according to the existing core metadata gate;
  an unrelated bad model/vendor/label is a different display-only case.
- Use the same `_as_int(size)` representation as actual Disk identity; do not
  let zero/negative/invalid capacity make an observation eligible. Invalid
  nonfinite arithmetic can refuse inventory through current top-level catches.
- Use `classify_bus(tran)` and `classify_kind(name,tran,rota)` consistently so
  the projection neither relaxes transport exclusions nor manufactures a new
  selected identity. These fields do not participate in alias matching.
- Unknown RO must not silently compare equal to explicit writable on a
  repeated physical path. Production already rejects unknown RO globally;
  fixture compatibility can preserve single-row None while a pre-filter
  signature records `_as_bool(node.get('ro'))` distinctly from False.
- Merge `_node_mountpoints(node)` with `flat_mounts[name]` before projecting
  mounted physical facts. Preserve existing validation of malformed mounted
  nodes via node_to_disk; do not let the narrow projection waive that refusal.
- Do not let propagation invent new mounted anchors as it traverses one known
  anchor. Compute from each original mounted observation with the same known
  anchor WWN restriction, just as pass14 does.
- Effective physical context should include disk and rom rows, including
  hidden mmc boot/RPMB areas. Partition/mapper filesystem facts remain in the
  existing ancestry reconciliation rather than becoming new whole targets.

Ordinary focused contracts to retain include:

- tests/test_protected_alias_chains_pass14.py (168 chains/contrary/placeholder/
  unrelated/order/final guard cases).
- tests/test_malformed_mounted_alias_regression.py (hidden physical/malformed
  mounted/unrelated malformed display/flat child contracts).
- tests/test_boot_serial_alias_pass7.py and test_boot_wwn_alias_pass12_discovery.py.
- tests/test_audit_20260908_discovery.py: unmounted duplicate WWN stays selectable,
  blank WWN does not glue a mounted disk, same serial/distinct known WWN remains
  disambiguated, ordinary LUKS/flat ancestry behaviors stay unchanged.
- tests/test_boot_exclusion_fails_closed.py:test_duplicate_lsblk_nodes_refuse_identity
  (identical duplicate observations deliberately remain ambiguous at final gate).
- tests/test_discover.py:test_parse_skips_pathless_node_keeps_sibling and
  test_serial_is_inherited_from_child_when_disk_serial_is_empty.
- tests/test_discovery_layout_identity_pass9.py and metadata/label/duplicate-
  JSON/ancestry tests (no identity truncation, omission or field-boundary loss).
