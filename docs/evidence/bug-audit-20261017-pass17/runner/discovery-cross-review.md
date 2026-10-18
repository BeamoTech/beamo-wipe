# Independent inherited-identity safety review

2026-10-17 / Codex `pass17_runner`, source only. Current source reviewed against
the starting archive and proposed bridge patch, with all supplied proof history
kept distinct. This child ran no test, native inventory, process, network or
privileged action and made no product/test edit for this review.

Initial reviewed discover.py SHA256:
`7dbff4e97c5e4087681744ce02857c08c6f7173de355371aff838814e1b3a8ea`.
Proposed patch SHA256:
`9a918202f613a8388c71648d705ee8395d12f0d784a7e9b794d656dfe0be0683`.
The starting archive's discover.py independently hashes
`0e77fcf0fa626e945c40fae8c8e5f544b735490f4acf8c718260abbabb20197f`.
Other exact reviewed hashes are in discovery-cross-review-initial-sha256.txt.

The normal resolver and the safety-only collector are appropriately separate.
Meaningful parent authority is preserved; otherwise all valid descendants and
the first malformed error are collected. Target identity still raises for a
malformed or conflicting field. Normalized candidate sets and malformed flags
are deterministic; duplicate comparisons do not compare exception instances or
mistake different candidate contexts for identical invalid observations. Raw
placeholder observations remain when there is no meaningful replacement. No
candidate context reaches the picker, confirmation peers, request or public
Disk/DiscoveryResult schema. A private return-type change has one production
caller, and public discover catches parser failures before returning any partial
selectable result. Mounted malformed metadata and uncertain boot remain full
refusals. Unrelated invalid unmounted rows retain the existing skipped-target
contract.

Any path from protected storage through unresolved nodes must first touch the
normal protected component. Full refusal at the first such unresolved overlap
is sufficient; there is no need to repair target identity or expand a Cartesian
product of candidate IDs. An already-reached partial observation causes full
refusal before candidate filtering. Example: meaningful serial ROOT plus
conflicting known descendant WWNs B/C can still reach boot(ROOT,A) through the
partial serial-only observation. That is a conservative availability boundary,
not unsafe target exposure. A valid explicit contrary parent WWN remains
authoritative and is retained for the existing distinct-known-WWN filter.

## Material unresolved omission in the reviewed initial source

The primary identified, and this review independently confirms, a distinct
unsafe unknown-WWN trace. Boot reports serial ROOT / WWN A. Unresolved physical
sda has conflicting inherited serials ROOT/LEAF and inherited WWNs B plus a
malformed value. Its partial Disk correctly has neither ID. Its parser-local
context still contains candidate serials(ROOT,LEAF), candidate WWN(B) and the
WWN-malformed flag. However `_UnresolvedPhysicalIdentity` drops that flag while
copying only path/serialkeys/wwnkeys. The protected-overlap predicate then treats
the set(B) as exhaustive and rejects the bridge against anchor WWN A before
considering serial ROOT. A writable LEAF/no-WWN path can remain selectable even
though the malformed alternative leaves WWN A possible. This is not the harmless
availability boundary above. Initial exact source is not approved pending proof
and correction of this omission; the primary owns the extra48-case proof.

Minimal correction proposal: propagate exactly the existing WWN-malformed flag
`identity_context[3]` into the parser-private unresolved tuple. A known contrary
candidate WWN disambiguates serial reuse only if no unknown WWN alternative
exists. Preserve matches to known WWNs, but allow serial matching when the WWN
set has a malformed alternative. Apply this both to the anchor-known-WWN
prefilter and to member matching. Do not use invalid_ids[1] as the unknown flag:
all-valid conflicting WWN sets and malformed alternatives are distinct states.
An authoritative parent returns before descendant collection and leaves that
flag false, preserving its distinct-known-WWN control. No schema or global
alias-policy change is needed.

The root's200-case proof48FAIL/152controls, corrected32-case proof8FAIL/24controls,
and invalid initial32-case fixture24FAIL/8PASS are historical primary results,
not child runtime evidence. No existing assertion or fixture is changed here.
Final exact source review remains pending after the extra proof and correction.

## Corrected exact source approval

The primary authenticated the extra48-case proof against the initial source:
16 AssertionError failures /32 controls, no errors/skips, before editing.
It then propagated the existing WWN-malformed boolean into the private
unresolved tuple and adjusted the two contrary-WWN branches. I independently
re-read every changed collector/predicate/parser block, safety.py's normal
alias traversal, the new48-case canonical fixture, and the two canonical bridge
copies. No runtime was executed by this child.

Corrected discover.py SHA256:
`a2fa08ce083d8b99403473ab8646a6b19f01157d1c2fd9df73e8469c92836bc4`.
The final receipt is discovery-cross-review-final-sha256.txt. Safety.py and
models.py remain byte-identical to the initial review. The original362-case
module remains unchanged. The200-case canonical copy differs from its proved
evidence-local source only in the accurate module docstring; the32-case copy
differs only in its docstring and canonical helper import. No assertion changed.
The extra48-case module uses the already guarded canonical fixture, four real
malformation classes, both orders, direct/nested descendants, protected and
unrelated controls and an authoritative contrary parent WWN control.

The corrected predicate does not reject a known contrary candidate set as
exhaustive when the WWN-malformed flag is true. Known matches still establish
a possible alias; a nonmatch can fall back to serial only when that malformed
alternative leaves the actual WWN unknown. When no unknown alternative exists,
distinct known WWNs continue to disambiguate serial reuse exactly as before.
An authoritative parent WWN returns before child fallback, keeping its malformed
flag false; it therefore cannot be weakened by an unrelated malformed child.
Unknown-alternative context is not used to repair any selectable identity.

The original exception/partial-state, duplicate determinism, normal unrelated
row, mounted refusal, no-schema-change and first-overlap full-refusal reasoning
above remains valid. The earlier conservative availability boundary is
intentional and separate from the corrected unsafe unknown-alternative loss.
**No further source objection to these exact corrected bytes.** Source approval
is for the primary's affected/full gates, not a claim those gates already pass,
nor release/physical/hosted acceptance authority. Any source/test byte change
requires fresh affected review and verification.
