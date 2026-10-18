# Pass20 discovery/safety source review

Status: source review complete; one bounded hypothesis handed to root for fake
execution. No new discovery defect is proved by this document. Prepared case
bytes are not test results. Date/author: 2026-10-17 18:12 UTC / Codex delegated
agent `/root/pass20_discovery`.

Repository/worktree: BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`, branch
`fix/safety-audit-20261015`, parent-reported HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`; dirty work preserved. The agent
edited only the two files in this evidence directory. It did not run pytest,
native inventory, devices, nwipe, subprocess-backed discovery, network tools,
guests, builds, commits, pushes, hosted CI or publication. Root owns serialized
runtime and the canonical unfinished-work record.

## Pending hypothesis BW-P20-DISCOVERY-MAPPING-TYPE

`discover._node_type` lowercases TYPE without stripping or validating the
token. `_mounted_holder_hides_members` recognizes specific known types;
`_has_stacked_holder` recognizes lvm/linear/bcache. A mounted generic `dm`
mapping or a whitespace-padded known mapping does not enter either refusal.
The later mounted-ancestor walk can consequently assign its mount to the
single PKNAME leg. `inventory.kind_label_for_type` does strip whitespace and
already labels `dm` as a mapped volume, so the display and topology rules
differ on these inputs. Production metadata validation checks TYPE key
presence but does not validate its token.

`mounted_holder_type_candidate.py` prepares 28 guarded synthetic cases:

- 16 desired refusal assertions: `dm`, ` lvm `, `linear ` and ` mpath`, each
  flat/nested and injected/production-schema-stub.
- 12 adjacent controls: ordinary crypt mount retains an unrelated target;
  exact lvm already refuses unknown membership; a blank unmounted generic
  mapping does not acquire an invented mount/filesystem claim.

The proposed behavior requires root judgment after proof. A generic mapping
name and one PKNAME do not establish complete membership. The padded-type
cases exercise malformed metadata, not a claim that actual Bookworm lsblk
normally emits whitespace. No upstream tools or external source were queried.
If root confirms failure, preserve the failing result and decide a minimal
fail-closed treatment of uncertain mounted mapping types. Do not normalize
unknown types into an eligible physical disk or broaden supported devices.

Remaining acceptance: root executes these exact bytes under the existing fake
acquisition guards; preserves failure/control counts and node IDs; independently
reviews any correction and runs adjacent safety/full local gates. No product
change has been proposed as complete, applied or verified here.

## Rejected or already-contained hypotheses

- Duplicate mapper names, including identical copies, are ambiguous in
  `_resolve_owner_disk`. A filesystem-bearing row with ambiguous ownership is
  rejected by parser ancestry guards or `_flat_layout_id`; the latter runs
  for the boot record as well. This source path supplies no new bypass beyond
  pass19's retained proof.
- A mounted flat unknown child with a missing, cyclic or contradictory
  ancestor cannot silently lose its mount: the pending-ancestor traversal
  visits every matching row, follows PKNAME/tree parents, rejects cycles and
  disagreements and propagates proven mounts. This rejects the missing-parent
  version of the pending hypothesis; its distinct concern is incomplete
  membership despite one valid parent.
- Truncating a long mountpoint or removing display control characters does
  not make its physical disk unmounted: `_node_mountpoints` keeps a nonempty
  observed mount or rejects a malformed one; `is_wipeable_disk` rejects every
  nonempty mount, regardless of whether its protected-path label changes.
- Unknown/missing RO is allowed by explicit fake inventory compatibility but
  production `_validate_real_lsblk_metadata` requires a usable boolean RO on
  every disk. No relaxation of the production gate was found.
- Float Infinity in SIZE can raise in `_as_int`, but public `discover` has a
  final catch-all producing an empty fail-closed result. Partition float
  truncation was not promoted into a product defect: real `lsblk -b` supplies
  integer sizes and final whole-device kernel size comparison is mandatory.
- Missing boot, conflicting live sources, unresolved typed/by-* links,
  duplicate live UUIDs, and unresolved stacked boot ancestry lead to no
  trusted boot result. `_resolve_boot_path` and `identify_boot_path` do not
  silently replace an unresolved observed mount with a label guess.
- A stale/different confirmed disk or boot identity is rejected by
  `assert_disk_identity`/`assert_rediscovered_identity`. Wizard final preflight
  rechecks boot and target; `_authorization_matches` also binds every listed
  peer identity and method parameters. Refresh clears owner, target, token,
  method/countdown and operation authorization. Stale refresh completions
  recheck sequence ownership after validation. No new transition bug proved.
- Same-path duplicate target rows cannot pass the final unique identity check.
  Hidden/malformed physical observations are retained before display filtering
  for mount/hardware alias protection, including pathless alias bridges and
  unresolved serial/WWN candidate sets added in earlier passes.
- Noninteger/Unicode-looking whole-disk names were not treated as a new real
  device issue. Final live launch requires actual nonsymlink block nodes,
  distinct block identity, fresh inventory, kernel size and local transport.
  No native device or kernel path was read to test this rejected hypothesis.

## Reviewed source identity

SHA-256 at this source-only handoff:

| File | SHA-256 |
| --- | --- |
| `src/beamo_wipe/discover.py` | `1b5ba659da7c12455451d7ed3e1c1bc7c9bfd84d4abdcbed0e3839174508367b` |
| `src/beamo_wipe/safety.py` | `ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b` |
| `src/beamo_wipe/wizard.py` | `be375a0861ec569a652e15f9f572bfa689f40048d736c5bedef641453d464bbb` |
| `src/beamo_wipe/inventory.py` | `bd594d0f6279181bb01bfa96c07ed8041d3da09fbee9ae9baf16dba60caa6acd` |
| Guard fixture `tests/test_discovery_observation_fallback_pass16.py` | `ef39198161cbd5426e8ea81945d57c96463c8ac094195fa3fb00d57fac86c688` |
| `mounted_holder_type_candidate.py` | `76f5b04192faf732d3dc50b07d95932f4ed5585334a318a08f8741da3e79be05` |

The review read the current AGENTS, relevant unfinished-work/pass19 state,
source, existing discovery/safety regressions, advanced mapping and relevant
runbook safety guidance. `/root/dev/AGENTS.md` is absent per parent handoff.
This is bounded static review, not exhaustive proof of hardware behavior,
native inventory compatibility, concurrent OS mount/device changes, full-gate
success or release qualification. Pass19's native-asset/full-run blockers
remain owned by root and are not resolved by this source review.
