# Pass18 discovery/safety source review

Date/author: 2026-10-17 / Codex discovery subagent. Source-only audit;
root owns all runtime proof and acceptance. Product patch applied only after
root proved valid and malformed pathless identity losses and approved exact diff.

Reviewed current `AGENTS.md`, relevant unfinished-work entries and product
constraints. The shared `/root/dev/AGENTS.md` is absent. Source identity is
recorded in `candidate-pathless-bridge.md`; repository/branch/HEAD/worktree
are the same as that note. Existing uncommitted work was preserved.

Inspected boundaries:

- Strict lsblk JSON loading and duplicate keys; required production columns;
  malformed node shapes, mountpoint shape, RO conversion and hidden rows.
- Whole-device path grammar, partition ancestry, path/name conflicts,
  path aliases, duplicate physical observations and hidden physical facts.
- Boot evidence precedence, unresolved/competing sources, typed UUID/label
  exactness, by-* link agreement, hybrid ISO UUID sharing and restricted
  label fallback.
- Flat and nested mounted ancestry, repeated mapper names, holders, cyclic
  chains, multi-device Btrfs, RAID, LVM, bcache and shared filesystem UUIDs.
- Parent hardware authority; descendant placeholders, malformed and conflicting
  fallback identifiers; protected serial/WWN alias closure and malformed-WWN
  unknown alternatives.
- Content classification and layout fingerprints, partition ownership,
  opened filesystem identities and deduplicated tree/flat observations.
- Confirmation peer set and token collisions, fallback serial/WWN tokens,
  operation authorization binding, visible review reset and rediscovery.
- Prelaunch whole-disk, boot/rdev, block-node, sysfs size and local transport
  guards; safe log location checks and tmpfs mount ownership.

One fresh defect was proved by primary: pathless physical rows lose alias facts
before the existing protected component walk (`candidate-pathless-bridge.md`).
The original 208-case proof returned 96 assertion failures /112 passing controls;
the additional 32-case malformed boundary proof returned 16 failures /16 controls,
both zero errors/skips. Root approved the exact minimal `discover.py` patch and
canonical regression copy. Retaining safety-only hardware observations allows
the established anchor-WWN rule to preserve contrary-identity controls; refusing
all pathless rows would be too broad. Primary fixed-result verification remains
pending at this checkpoint.

Rejected hypotheses / existing controls:

- Sanitized/truncated mount display cannot make a mounted disk selectable:
  every retained nonempty mount blocks selection; cleanup-to-empty raises.
- Unknown RO on injected legacy fixtures is intentional; real acquisition
  separately requires a parseable disk RO field.
- Fractional or unusual injected sizes cannot bypass live launch size proof:
  the final kernel-backed byte count must match. Invalid conversion errors
  reach public discovery's fail-closed boundary.
- Distinct known WWNs intentionally disambiguate reused serials. The alias
  walk must retain that anchor constraint through missing-WWN bridges.
- Same-path duplicate rows cannot be used to hide read-only, mount or physical
  identity changes. Physical signatures are reconciled before display filtering,
  and final identity requires a unique safe target.
- Method, listed-peer identity or path changes revoke operation consent;
  fresh discovery and safety checks precede runner start.
- A direct source parser error is not evidence of an unsafe public discovery
  result. The public wrapper returns no targets on malformed acquisition.
- Support export deliberately requires exact parent/root fingerprints for its
  protected baseline. Discovery-inherited child IDs with blank raw parent IDs
  can therefore cause conservative export refusal even if unchanged. No unsafe
  acceptance follows; broadening that stricter export identity contract is
  outside this fix and remains a compatibility limitation.

No runtime, device, GUI, network, privileged or subprocess campaign was run by
this subagent. These are source findings, not substituted acceptance evidence.
