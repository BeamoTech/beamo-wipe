# Pass17 inherited hardware identity review

Final-source addendum below supersedes the initial discover.py hash and approval
after the primary found and proved the adjacent physical-projection fact loss.

2026-10-17, Codex `/root/pass17_discovery`. Local, uncommitted work on
`fix/safety-audit-20261015`, HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.

The primary agent ran and authenticated the frozen 362-case module against the
unchanged starting source: **176 AssertionError failures, 186 passes, no errors
or skips**. I independently read its original-proof review and the first raw
failure traceback. The injected boot serial example leaves `/dev/sdc`
selectable even though it matches the boot disk's later descendant serial:
`assert '/dev/sdc' not in {'/dev/sdb', '/dev/sdc'}`. All 754 starting inputs were
unchanged when the primary authenticated the proof. This child agent ran no
runtime tests, native inventory, network, loop, guest, or privileged operation.

The tests preserve normal controls and exercise boot, mounted and selectable
physical anchors; direct and nested descendant IDs; both child orders;
null/empty parents; malformed, conflicting and placeholder children; equivalent
serial case and canonical WWNs; meaningful parent authority; and raw parent
placeholder retention. Their fixture denies process acquisition and reads of
`/dev`, `/proc` and `/sys`, and uses only explicit copied payloads with a fake
device realpath mapping. Tests stayed frozen during implementation.

The fix is restricted to discover.py:

- Hardware fallback visits all descendants before accepting an inherited ID.
  Every field is validated before interpreting missing/placeholder values.
  Distinct meaningful serials or canonical WWNs cause refusal instead of
  retaining only the first candidate.
- Placeholder values cannot hide a later meaningful candidate. Equivalent
  candidates retain the first reported spelling after comparisons use the
  same normalization as the existing alias guards.
- A meaningful parent hardware ID remains authoritative. Otherwise the
  validated meaningful descendant is used; when neither supplies one, the
  raw parent value (or first raw child) remains in the rediscovery identity.
- Both display-owned Disk conversion and safety-only physical observations use
  that shared node resolver. Vendor and other display fallback behavior,
  method flags, token/countdown/owner laws, and launch boundaries are unchanged.

Parent placeholders are in scope because the existing meaningful-identifier
policy already classifies all-zero/unknown/N/A strings as absent. Letting one
suppress a valid inherited ID creates the same missing-alias defect. Retaining
the original raw placeholder when no stronger ID exists preserves the prior
exact-identity contract.

Reviewed final bytes:

| File | SHA256 |
| --- | --- |
| src/beamo_wipe/discover.py | 0203da10e2efde1db560d5eecc853dc503aac3e3c906ca053b74fcfd0a5bfddf |
| src/beamo_wipe/safety.py | ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b |
| src/beamo_wipe/models.py | 9fb0bcb97d35b1ee0f041f8ccb728fe8a2b9f173242a904bf2af6f7b5f42b95c |
| src/beamo_wipe/methods.py | edf22b0a3cc4fb5de61c43a5ab82cccafbf6280270753c802f58ca6fe1ae6e13 |
| tests/test_descendant_hardware_ambiguity_pass17.py | 55c79450a3dd7676876ae5896569653d5bb913f962e92cc3e0fd17ddfc25900f |
| incremental-discovery.diff | 9ef0c0524995cc915926a1ac854c9f4dc2d43a2a81d64268b4043d4ec278ebfb |

The incremental diff was generated against the primary's archived exact
starting discover.py; its extracted SHA256 was independently checked as
`0e77fcf0fa626e945c40fae8c8e5f544b735490f4acf8c718260abbabb20197f`.
The `diff` command exited 1 because these reviewed differences exist.
`git diff --check` passed for the assigned source/test paths.

Status: source review approves these exact bytes for the primary's serial
affected/full regression gates. Those runtime checks are pending in this
child review; no completed acceptance claim is made here. Existing incident,
historical trace, final-public ISO/QEMU/native Windows and physical acceptance
limitations remain as recorded by the primary in the canonical backlog.
Any eventual commit containing this change requires a `safety:` prefix.

## Final discovery addendum after physical-bridge proof

The primary proved a second, adjacent discovery defect against the initial
`0203da10...` implementation: conflicting or malformed inherited IDs made a
target correctly unselectable but also removed valid candidate facts needed
to protect another physical path. This is separately attributed; the first
362-case proof alone did not cover it.

Authenticated primary-owned results before the second product edit:

- 200-case bridge proof: 48 intended failures / 152 controls, no errors/skips.
- Initial 32-case duplicate fixture: 24 failures / eight passes. These were
  invalid positive controls because repeated partition parents created an
  independent layout-ancestry refusal. Raw initial source is retained at
  `bridge_duplicate_probe.initial.py`; no passing claim applies to it.
- Corrected 32-case duplicate proof: eight intended failures / 24 controls,
  no errors/skips. Unique identity-only crypt descendants remove unrelated
  filesystem/partition layout claims. Every original assertion is retained.

The primary authorized the exact proposed patch at SHA256
`9a918202f613a8388c71648d705ee8395d12f0d784a7e9b794d656dfe0be0683`,
which this child applied without any further source alteration. It collects
every valid raw descendant and the first malformed error string, then keeps
normalized candidate keys, malformed state and conflict separate. The normal
target resolver still raises. Parent-invalid input can conservatively retain
a valid descendant **exclusion fact**; that never repairs target identity.
A meaningful parent still overrides fallback before descendant collection.

Safety-only physical projection retains deterministic parser-local candidate
context even when an invalid target field stays empty. Duplicate physical
signatures compare normalized tuples and booleans, never exception identities.
Different valid contexts on the same physical path therefore refuse; identical
invalid repeats do not become contradictory merely because separate calls
created separate ValueError objects.

After boot identification, unresolved physical candidates are checked against
the existing normal boot/mounted alias components. An overlap refuses the
inventory. Unrelated malformed singleton rows continue to be skipped while
other safe disks remain available. Set matching follows the existing
serial/WWN preference and anchor-known-WWN restriction without Cartesian
candidate expansion or global alias-policy changes. No Disk/DiscoveryResult
or public API change was made. Valid explicit other-field WWNs remain present
for the same disambiguation policy. Vendor fallback remains unchanged.

The primary requested canonical copies of the two admitted probes:
`tests/test_unresolved_physical_bridge_pass17.py` is an exact 200-case copy;
`tests/test_unresolved_physical_duplicates_pass17.py` changes only its fixture
import to that canonical module. The original 362-case module is unchanged.
This child has run no runtime campaign. The primary owns affected/full gate
execution after this final source change.

Exact final discovery approval:

| File | SHA256 |
| --- | --- |
| src/beamo_wipe/discover.py | 7dbff4e97c5e4087681744ce02857c08c6f7173de355371aff838814e1b3a8ea |
| tests/test_descendant_hardware_ambiguity_pass17.py | 55c79450a3dd7676876ae5896569653d5bb913f962e92cc3e0fd17ddfc25900f |
| tests/test_unresolved_physical_bridge_pass17.py | fb211952b3cada7eefb49bd68926ac74ff995ba0d1b3ec7e0f40807a96a7b8f4 |
| tests/test_unresolved_physical_duplicates_pass17.py | 754f8d89611a14ad047d7fbf2d7f69fd725717c03c4064f4bb90a5bd3786e58b |
| final-incremental-discovery.diff | 3324a00e70f503d00793b8541d87faaeccc5a925515a35eb45142f4b7cc025a2 |

The complete pass17 discovery diff is retained in the final incremental file;
the earlier first-fix diff and hashes are preserved as history. Diff exit 1
means the displayed differences exist; `git diff --check` passed. Source
review approves these exact final bytes for the primary's regression gates,
with all historical/incident and separate acceptance limitations unchanged.
