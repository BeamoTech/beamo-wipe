# Pass15 bounded discovery/safety review

Reviewer: `/root/pass15_discovery`, 2026-10-16 UTC.
Repository: `/root/dev/Beamo Wipe`; branch `fix/safety-audit-20261015`;
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
No product or test edits by this reviewer. Runtime campaigns require root
admission; source reads and preparation only until admission.

Read current AGENTS.md, memory index/product constraints, pass14 canonical
unfinished entry and retained/new regression contracts. Shared guide absence
and continuation are reported by root; no new authority is inferred.

## Exact reviewed starting bytes

- AGENTS.md: `1e6f980d50267db488a9beb353802242ac57379450c1d9c0ad77c13928509290`
- discover.py: `9a95b24403dad52c2ca4212a25ccc069ac7c55eafc3a4cb366a0bf62fdbefd92`
- safety.py: `f0ad1dc5d32d5f71aa8d27c7172634ace061111a47f5135d4df55021121be818`
- wizard.py: `be375a0861ec569a652e15f9f572bfa689f40048d736c5bedef641453d464bbb`
- identity.py: `4ccada033bab0c3811450cb9ab4e85c74936af56e8cd94fdf84f8d5566942050`
- methods.py: `edf22b0a3cc4fb5de61c43a5ab82cccafbf6280270753c802f58ca6fe1ae6e13`
- nwipe_runner.py: `7672c9c0646aa9679b87d9b729c3f9228f0cf1b7f9bb4b1c162a7e37e16dbf9b`
- test_protected_alias_chains_pass14.py: `f59bc0b6b6bfc9f5b63f113fdd33a95b9b4be6e23e02cf2f884ebf88272417a3`

## Verified omitted-observation defect

`parse_lsblk_json()` computes hardware protection over picker `disks` plus
`mounted_observations`. `disk_nodes()` omits optical `rom` rows, `should_hide()`
can omit physical disk names containing `live`, and per-node display/layout
validation can skip an unmounted bridge. Those rows still contain reported
serial/WWN observations. A boot or mounted anchor S/noWWN can reach a bridge
S/WWNX and then a target T/WWNX; if the bridge is omitted before closure, the
target may stay selectable. This would be an evidence-loss defect preceding
the pass14 closure rather than a defect in the closure traversal itself.

Prepared `omitted_alias_context_probe.py`: 240 injected fake cases. Boot and
mounted anchors; visible, optical, hidden physical name, overlong model and
overlong layout-label bridge forms; root-missing/leaf-missing chains;
contrary-WWN and unrelated controls; all six row orders. Native acquisition,
subprocess and `/dev`, `/proc`, `/sys` open/lstat are trapped. Every row records
raw payload, inventory, bridge context, target flags/IDs and guard/identity/token
outcomes. Any malformed case that fails discovery is fail-closed, not a bug.

## Nonfinding dispositions from source review

- The pass14 closure preserves a known anchor WWN through a missing-WWN
  intermediate, so distinct known WWNs remain disambiguated. Its visited
  observation indices terminate cycles and make row ordering irrelevant.
- Live mount resolution rejects unresolved competing sources, shared live UUID,
  direct/typed link disagreement, mapper/Btrfs sources and contrary ancestry.
  Label/cmdline fallback cannot uniquely select one disk when another whole
  target-sized disk can be the live medium.
- Production metadata validation requires read-only and mount fields; fixture
  permissiveness does not waive the real acquisition gate.
- Mounted raw/flat/mapper ancestry and repeated mapper ownership are checked
  before picker filtering; unresolved mounted stacks fail closed. The review
  did not find a new mounted ancestry defect.
- Selected and boot rediscovery use complete recorded identity tuples.
  Duplicate target rows do not satisfy unique identity checks. Pre-start
  wizard consent binds the full listed inventory, method mapping and selected
  identity; refresh revokes owner/token/countdown. Final launcher rediscovery
  repeats boot/target identity checks under the wipe lock.
- Separate Erase action and the five-second review gate remain present.
  Overlay/navigation/keyboard paths restart or revoke review. A fake clock NaN
  was considered but rejected as an injected dependency issue with no supported
  production path.
- Everyday/prng+last, Three overwrites/dodshort+last and Quick zero/zero+off
  remain mapped to one process. Whole-disk normalization, one positional target,
  exact exclusion, method-bound flags, no `--force`, log location and block
  identity checks remain at final command construction/execution.
- Placeholder serial/WWN child fallback was considered but has no concrete
  supported trace yet. No speculative change is proposed.

## Limits

This document is a source review and probe design until runtime receipts are
appended. It is not a passing test claim, final patch approval, release
qualification or permission for physical/native/hosted work.

## Admitted runtime receipt

Root explicitly admitted one bounded fake campaign after the baseline exited.
`PYTHONPATH=src python3 /tmp/pass15-discovery/omitted_alias_context_probe.py`
exited 0 normally in 0.29 seconds. Runtime lane released immediately.
Raw output: `omitted-alias-context.txt`; exact JSON:
`omitted-alias-context.json`; receipt: `omitted-alias-exit.json`.

- 240 cases: 96 protection violations, 144 expected controls.
- Zero native process, inventory or `/dev`, `/proc`, `/sys` path attempts.
- All 240 had boot identified and no discovery error; overlong bridge model/
  layout-label cases were skipped, not refused inventory.
- Visible bridge: all 48 expected behaviors pass.
- Each omitted bridge form (rom, hidden_name, overlong_model,
  overlong_layout_label): 24 violations across the two composed alias chains
  and both boot/mounted anchors; 24 contrary/unrelated controls pass.
- All 96 violating leaves stayed writable, unmounted, non-boot and selectable,
  passed final disk identity and obtained a confirmation token.
- All 48 violating boot cases passed `assert_boot_excluded` too.
- Optical/hidden-name bridge rows remain visible in the excluded inventory;
  overlong metadata rows lose path in the generic unavailable inventory row.
  Both lose their meaningful hardware identifiers before safety closure.

The malformed cases do not justify accepting malformed targets. A correction
can retain only validated protection evidence or refuse unsafe ambiguity;
display filtering must not remove an established hardware bridge. Root must
independently reproduce and choose the smallest correction. No fix or tests
were edited by this reviewer.
