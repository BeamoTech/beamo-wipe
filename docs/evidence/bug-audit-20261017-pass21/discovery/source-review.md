# Pass21 discovery and safety source review

Prepared 2026-10-17 20:54 UTC by `pass21_discovery`. Source-only work; root owns
all tests and application/native runtimes. No source/test edits, imports,
application invocation, native inventory, device access, network, guest, hosted
CI, staging, commit, push or publication was performed by this child.

Repository `BeamoTech/beamo-wipe`, branch `fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`, worktree `/root/dev/Beamo Wipe`.
Current local dirty source, including all prior audit work, was preserved.

Read current `AGENTS.md`, relevant `.ai/memory/MEMORY.md` index and top pass20
unfinished record. Shared `/root/dev/AGENTS.md` is absent. Existing proof
fixtures and prior relevant discovery/layout regressions were read as source.

Source hashes at review:

- `src/beamo_wipe/discover.py`:
  `9f5a5a36ddf9dad77c7195920ed6290ed745d4684d63beeac103882fb6198f65`
- `src/beamo_wipe/safety.py`:
  `ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b`
- `src/beamo_wipe/wizard.py`:
  `be375a0861ec569a652e15f9f572bfa689f40048d736c5bedef641453d464bbb`

## BW-P21-DISCOVERY-NAME — PREPARED, NOT EXECUTED BY CHILD

Hypothesis: a physical disk with valid PATH and absent/null/empty NAME can
remain selectable while losing a flat partition's filesystem/Windows evidence
and layout fingerprint. `_validate_real_lsblk_metadata` checks only NAME key
presence. `_partition_parent_contradicts` accepts a flat `sda1` with PKNAME=sda.
The physical disk is not entered under `sda` in `by_name`; both
`classify_disk_contents` and `_flat_layout_id` return early on its missing NAME.
Changing the unbound flat partition UUID can then leave `disk_identity` equal.

Prepared fake-only 60-case `missing-physical-name-probe.py`, SHA256
`6a8ba18b26bf539197f3a87c06c4cdf47e4d6cde3ef3090ebe3c8cb1f826dd1c`:

- direct/injected/production-metadata-stub routes;
- present/empty/null/omitted physical NAME;
- flat/nested partition placement;
- observed Windows+layout evidence and changed UUID identity boundaries;
- adjacent mounted partition controls.

The proof allows refusal of uncertain storage; it never requires inventing a
kernel identity from PATH. Predicted 16 assertion failures and 44 controls on
reviewed bytes, subject to root execution. Direct ValueError is valid failclosed.
No bug is claimed proved by this source review alone. Remaining acceptance:
root-run original receipt, minimal proved fix, unchanged probe assertions passing,
adjacent safety suites, source identity review and final prescribed gates.

## BW-P21-DISCOVERY-SIZE — PREPARED, NOT EXECUTED BY CHILD

Hypothesis: JSON numeric positive/negative infinity, including exponent `1e999`,
reaches `_as_int`'s early float conversion and raises OverflowError outside its
conversion try. `discover` does not catch OverflowError, so a malformed size can
escape its public DiscoveryResult failure contract. NaN raises ValueError and is
already handled by the public API; finite floats are intentionally supported.
The product loader currently accepts Python JSON nonfinite constants.

Prepared fake-only 72-case `nonfinite-size-probe.py`, SHA256
`1ba4604055fa2964ddf31f4ac5dcda43d9db3c2ce10792efb026a58823e0e4fb`:

- NaN, Infinity, -Infinity and overflow exponent, loaded through product loader;
- size located on boot disk, target disk or flat partition;
- direct/injected/production-metadata-stub routes;
- finite integer, finite float, finite exponent and `2**100` integer controls.

The proof accepts rejection by the loader, lower-level ValueError or ordinary
safe DiscoveryResult, but not escaping OverflowError. Predicted 27 OverflowError
failures and 45 controls, subject to root execution. No bug is claimed proved by
this source review alone. Remaining acceptance is root original/fixed evidence,
finite-float/large-integer behavior preservation and applicable gates.

## Other reviewed boundaries

Source inspected whole-disk eligibility, boot mount/typed-source/UUID resolution,
partition name and PKNAME contradictions, duplicate physical observations,
mounted flat ancestry, holder membership, aliases, layout hashing and final
selected/boot identity checks. Authorization paths were read through refresh,
selection/token/method operation binding, visible countdown, claimed preflight,
final rediscovery and active-run cleanup. No additional concrete source-supported
defect was established in those paths. This is a bounded source review and does
not replace root runtime verification or previously blocked platform acceptance.

## 20:59 UTC follow-up and proposed fix review

Root reports original NAME probe: 16 failures/44 controls, matching source
prediction. Root reports nonfinite probe: 9 failures/63 controls, with all nine
failures on the direct parser only. The earlier statement that OverflowError
escapes the public API is corrected: `discover` has a following generic
`except Exception` that already returns an ordinary failed DiscoveryResult.
The specific exception tuple alone was insufficient evidence. Root's actual
proof establishes inconsistent malformed-numeric handling in the lower-level
parser; it does not establish a public uncaught exception or erase permission.
These counts are root-reported here; root retains the actual run receipts.

Proposed `_as_int` fix review: wrapping its early float `int(value)` conversion
and translating only OverflowError to ValueError is narrow and consistent with
existing malformed lower-level metadata handling. Finite floats, integer and
large integer paths stay unchanged; existing NaN ValueError also stays unchanged.
Use a closed diagnostic message that does not embed raw metadata.

Proposed NAME guard review: keep the existing missing-path check before a new
disk-name rejection. `test_node_to_disk_rejects_empty_path` explicitly requires
the existing `no usable device path` message for a pathless type=disk row. A
guard scoped to type=disk preserves inventory/rom behavior and prevents false
display targets without repairing the identity from PATH. Unmounted malformed
disk rows have already contributed `_physical_observation` alias facts; mounted
malformed disk rows currently fail the whole inventory through the earlier
node_to_disk check. Boot-disk NAME uncertainty then cannot create a boot Disk,
so parse returns no targets. Keep the independent physical observation path
free of the new display eligibility guard.

Empty NAME alone may not close the same root cause: `_identity_text` allows
nonempty NAME values containing slash segments. `_disk_identity_contradicts`
compares realpath aliases of `/dev/NAME`, so `./sda`, `x/../sda`, `sda/` and
`/sda` can alias `/dev/sda` while remaining unbound in by_name for PKNAME=sda.
Prepared 30-case `noncanonical-physical-name-probe.py`, SHA256
`aff66a05804c06116ceeffc986312e61163088b45b95bd9ca64d097cfac9b81f`.
It uses only lexical `posixpath.normpath` for fake /dev realpath semantics;
all native guards remain in force. Canonical NAME=sda is the control. Predicted
24 failures/6 controls; NOT RUN by this child. Root should prove this variant
before deciding whether the NAME guard must require one kernel-name component.

No shared source/test edits or native/test runtime were performed in this follow-up.
