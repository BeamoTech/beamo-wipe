# Pass15 independent discovery patch review

Reviewer: `/root/pass15_discovery`; 2026-10-16 UTC.
Result: **APPROVE source delta**, subject to the primary's required final
gates/artifact verification. No runtime campaign was executed during this
review. No product/test source was edited during this review.

The primary implemented the patch. This reviewer earlier authored the400-case
regression module and the original240-case probe. The primary independently
reproduced expanded alias and duplicate failures and reports all400 new cases
passing. Those are primary receipts, not an independent runtime claim here.

## Exact source identity

Repository/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`.
Branch `fix/safety-audit-20261015`;
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
Compared the full changed source text with the starting bytes in
`/tmp/pass15-primary/starting-source.tar.gz`, SHA256
`a8d57369704ca71daf701a53641ca73f76d32076583d330ffa9dc96716f979cc`.

- models.py: `9fb0bcb97d35b1ee0f041f8ccb728fe8a2b9f173242a904bf2af6f7b5f42b95c`
- discover.py: `ba82f23f4bbf2fea6bd0bdcdddaf545c83cde3ac111b3b9288429fb93fc7de35`
- safety.py: `ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b`
- test_physical_observation_context_pass15.py:
  `3a49bd5dc72f4e310dd054b84cfbf8b2564b0edb268e639f8e980cf58ec97e1c`

## Root cause and resulting behavior

The correction retains validated physical observations before presentation/
layout parsing can drop them. `_physical_observation` depends on core path,
name, serial/WWN including existing descendant fallback, size, kind, transport,
RO, hotplug and effective mount facts. It does not parse display model/vendor
or filesystem labels/layout. A duplicate canonical physical path compares the
full projected facts plus a tri-state RO value, so missing/unknown RO cannot
compare equal to an explicit writable observation. Known core conflicts now
refuse the inventory before display parsing.

The defaulted `DiscoveryResult.physical_observations` tuple stores the context.
Discovery boot closure, mount propagation and final `assert_boot_excluded`
include it. Resetting a leaf's display/protection flags cannot erase the
retained hardware bridge. The pairwise alias rule and pass14 traversal are
unchanged, including known contrary anchor WWNs.

## Contract review

- The new field is appended with an empty immutable default. Existing keyword
  constructions and recovery reconstructions remain valid; manually built
  results continue using disks/selectable for guard context.
- The field is consumed only by safety context/closures. `disks`, selectable,
  listed confirmation peers and displayed inventory are still built by their
  existing parser/filter path. Hidden optical/eMMC/name rows and malformed
  display rows do not become selectable or enter confirmation peers.
- Mounted physical rows still call full `node_to_disk` before the narrow
  projection. Malformed mounted model/vendor/layout remains a full refusal.
  Existing flat-child effective mounts are merged before projection.
- Isolated pathless unmounted rows still skip. Unrelated malformed model/
  vendor/label does not abort otherwise valid targets because those fields do
  not enter the projection. Ambiguous core identity now fails closed; it is
  never shortened or scrubbed into another usable device identifier.
- Ordinary empty-parent serial/WWN descendant fallback is retained exactly.
  Placeholder and distinct known-WWN interpretation remains in unchanged
  canonical/meaningful identifier helpers.
- Identical physical duplicate rows retain both observations and both parsed
  disks; existing final unique-target identity refusal is not weakened.
  Different physical paths sharing an unmounted WWN remain ordinary candidate
  rows unless they connect to boot/mounted evidence. Contrary-WWN and unrelated
  controls remain governed by the unchanged anchor rule.
- Later full parsed-Disk reconciliation still catches metadata/layout/content
  differences between two parseable copies. The new pre-filter check catches
  the proven core conflicts even when one copy is skipped for display errors.
- `Disk` projections are immutable, and tuple/dictionary comparisons do not
  require additional hashing or equality overrides. Tri-state RO annotation
  matches `_as_bool` and the `Optional[bool]` dictionary signature.
- The renamed private mount helper has one production caller; no other source
  or test directly calls the old keyword.

## Serialization, recovery and claim boundary

Searched all production asdict/vars/field reflection and DiscoveryResult
construction consumers. SessionStore.arm serializes `discovery.disks`
explicitly as Disk records and strips mountpoints. Support export similarly
uses disks/fingerprints explicitly. There is no production
asdict(DiscoveryResult) or generic `__dict__` serialization, so the new physical
context is not automatically persisted/exported. Recovery builds an empty-
selectable historical DiscoveryResult and does not authorize another wipe.
No stored schema or migration change is needed for this additive in-memory
field.

No change to nwipe argv/methods/token/countdown/owner action, engine pin,
allowed target classes, claims, boot priority, build/publication, actual device
access or native qualification was found in this delta. No objection remains
from this bounded source review. Any subsequent source-byte change requires
review against the updated exact hashes.

## Subsequent adjacent-test evidence (approval superseded pending revision)

The primary's2271-case adjacent run found7 preserved-contract regressions in
the reviewed implementation: direct parse of overlong serial/WWN/child serial
now raised, and Unicode serial/WWN targets caused boot identification failure
instead of retaining boot plus excluding that target. The new400 cases passed.
The source approval above is therefore superseded until the planned correction
and updated exact-byte review; it is not proof that every existing contract
passed.

Recommended source-only correction: independently attempt the current serial
and WWN extraction expressions, returning an intact valid value or empty plus
an invalidity flag in the narrow nonselectable projection. Keep per-field
invalidity flags in the same-path physical signature so malformed duplicate
observations cannot compare equal to valid writable rows. Do not truncate or
scrub malformed IDs into another usable value. Keep node_to_disk unchanged so
the actual malformed target is still skipped, and keep mounted full validation
before projection so malformed mounted rows continue refusing the inventory.

This retains any valid contrary WWN even when serial is invalid. Clearing an
invalid WWN in the safety-only context can conservatively widen protection;
it cannot make the malformed row selectable. Existing empty-parent descendant
fallback is preserved by applying the catch to the complete original
extraction expression. Names/paths/mounts and structural metadata remain under
their existing global gates. No runtime/source edit by reviewer for this
assessment.
