# Adjacent unresolved physical-bridge hypothesis

2026-10-17, source-only follow-up requested by the primary while its full gate
is active. No product or test input was changed. The evidence-local
`bridge_probe.py` is prepared but **unexecuted**; it is outside the frozen
source/test input set. SHA256:
`fb211952b3cada7eefb49bd68926ac74ff995ba0d1b3ec7e0f40807a96a7b8f4`.

Exact proposed source trace at discover.py SHA256
`0203da10e2efde1db560d5eecc853dc503aac3e3c906ca053b74fcfd0a5bfddf`:

1. Boot or mounted anchor reports serial SIDE-A and no WWN.
2. Unmounted physical sda has no parent serial; two descendants report SIDE-A
   and SIDE-B. The accepted fallback policy makes both meaningful physical
   identity candidates. Its conflict raises ValueError.
3. `_physical_observation.hardware` catches the exception and returns empty
   serial plus invalid=True. Disk conversion later skips sda. The observation
   graph thus contains neither candidate serial.
4. A writable sdc reporting SIDE-B is no longer connected to the protected
   anchor through the competing physical observations on sda.

The malformed-identity variant is also supported by the source. If sda instead
reports a valid explicit WWN B and has one valid child serial SIDE-A plus one
malformed child serial, the serial resolver raises and the projection retains
only WWN B. Boot SIDE-A/no-WWN cannot reach that observation, and a writable
leaf with another serial/WWN B loses the A-to-B exclusion bridge. The ordering
does not rescue it because the new resolver validates every descendant.

These are not arbitrary fabricated correlation claims: descendant fallback is
already the supported source for a physical ID when the parent omits it, and
earlier retained regressions explicitly require hidden/malformed physical
observations to retain safety-only alias bridges. Refusing a target because
its inherited ID is ambiguous is correct, but removing all valid candidate
facts can expose another path belonging to the protected component.

The proposed bounded probe has 200 statically counted cases:

- 16 conflicting-SERIAL/WWN bridge cases across boot/mounted anchors, both
  child orders, and direct/nested descendants.
- 48 controls for unrelated ambiguous singleton, meaningful parent authority,
  and a normal consistent inherited alias.
- 8 controls where distinct authoritative WWNs disambiguate a conflicting
  serial bridge.
- 32 valid-serial/malformed-sibling cross-field bridge cases, with overlong,
  control-containing, scalar and list invalid values in either position.
- 96 cross-field controls for unrelated malformed records, meaningful serial
  parent authority and distinct authoritative WWNs.

Expected current-source result if the trace is confirmed: 48 intended
AssertionError failures / 152 controls, zero errors/skips. This expectation
must not be substituted for a run. All acquisition/process/native path access
is forbidden, and scans use explicit copied dictionaries and fake realpaths.

Possible minimal remedy, subject to the proof and primary review: retain valid
inherited candidates separately from their malformed/conflict signature in
the parser's safety-only physical context. A target resolver must continue
raising on ambiguity; do not repair target identity or use these candidates
as picker/confirmation peers. A meaningful parent field remains authoritative
and suppresses its descendant fallback candidates.

One narrow option avoids new public Disk/DiscoveryResult fields: after boot
and mounted anchors and normal alias components are known, refuse the inventory
only if a physical record whose identity could not be resolved has a valid
candidate connected to that protected component. If the first unresolved
bridge is reached, full refusal is sufficient; its other candidate does not
need to be promoted to target identity. An unrelated malformed/ambiguous
singleton remains skipped and preserves unrelated safe disks. Candidate views
must retain a valid authoritative other field so known distinct WWNs continue
to disambiguate serial reuse. Do not project a serial candidate with an empty
WWN when a meaningful authoritative parent WWN was actually observed.

Alternatively, an ambiguity-aware internal fact projection can retain all
candidate combinations and match them with the existing normalized alias
policy. Merely adding separate same-path Disk views to the existing graph
does not connect two different serials on one path, because that graph follows
hardware IDs rather than path equality. Such a design needs explicit handling
or targeted refusal; silently expanding global path-alias semantics would need
separate justification and focused controls.

Status: unresolved until the primary runs/authenticates this proposed probe.
The earlier cross-review's final acceptance recommendation is conditional on
resolving this newly identified information-loss hypothesis. Existing full-gate
passes do not establish behavior outside their frozen regression set.

## Prepared patch text and duplicate-context extension

The primary requested a concrete narrow proposal while the existing full gate
remains active. `bridge-fix.proposed.patch` contains apply_patch-format text
against the exact discover.py hash above. **It has not been applied, compiled,
linted or executed.** SHA256:
`9a918202f613a8388c71648d705ee8395d12f0d784a7e9b794d656dfe0be0683`.
Only the primary can authorize its application after the pure probe is proved.

The collector returns all valid raw descendants plus a first malformed error
string, separately from normalized-key conflict. A meaningful parent returns
before descendant collection. The normal resolver raises on either malformed
or conflicting identity; a safety-only observation still keeps the affected
field empty but passes deterministic parser-local candidate tuples and malformed
booleans. No exception object enters physical duplicate comparison. The
duplicate signature includes those tuples/booleans so different valid candidate
contexts cannot collapse merely because both rows were invalid, while identical
invalid observations remain equal under the same preexisting uniqueness law.

After boot identification, a parser-local predicate computes the existing
normal alias component for boot and each mounted source. It refuses only when
an unresolved physical path is already in that component, or a valid candidate
can join it under the same normalized serial/WWN rule. Candidate-set matching
does not construct Cartesian Disk variants. It filters candidate WWNs through
the root anchor's known WWN before checking component members; two known
different WWNs never fall back to serial comparison. Existing partial
projection membership is also sufficient for refusal because dropping that
unresolved record's further candidates would truncate an already proven
protected bridge. Unrelated malformed singleton rows remain skipped.

No Disk, DiscoveryResult, public API or global alias policy changes are
proposed. `_physical_observation` has only its one internal parser caller;
that private return value is extended. Vendor fallback is preserved. Normal
target identity never uses candidate sets to repair ambiguity.

`bridge_duplicate_probe.py` is an additional **unexecuted**, evidence-local
32-case proposal importing the guarded fixture/helpers from `bridge_probe.py`.
SHA256 `1724bc7cf14e84f52aa32a05b7a166dc9eccfec309ef72dbcccddeaabd0af096`.
Expected current-source result: eight differing-candidate invalid-duplicate
failures / 24 controls. It covers SERIAL/WWN, conflicting/malformed fallback,
both repeated-row orders, identical vs different context, and meaningful parent
authority. Meaningful parents continue to ignore contradictory/invalid
descendant fallback; identical invalid repeats must not differ solely because
the collector raised different exception instances. This extension does not
change the frozen 200-case initial probe or any source/test input.

## Authenticated initial result and duplicate-fixture correction

The primary subsequently authenticated the original 200-case probe:
**48 intended AssertionError failures / 152 controls, zero errors/skips**.
That confirms the exclusion-fact loss, rather than just the source hypothesis.

The initial duplicate extension did not establish its intended contract:
**24 failures / eight passes**, with the 24 intended positive controls losing
boot identification. The raw initial file is preserved as
`bridge_duplicate_probe.initial.py` at its original SHA256 above. No passing
or expected result is claimed for those controls.

The fixture itself introduced unrelated unresolved layout ancestry. Repeating
physical sda made partition owner resolution ambiguous; every `part` contributes
a nonempty layout row even without a filesystem. `_flat_layout_id` tests that
ambiguity while converting every disk, including boot, so it skipped the boot
row. Therefore those positive controls were invalid for this signature probe.

The corrected duplicate extension uses uniquely named direct crypt descendants
carrying only the hardware-ID field and no filesystem/partition/layout data.
They still exercise authoritative descendant hardware fallback, while their
empty filesystem rows do not imply unresolved contents. Meaningful-parent
copies retain identical empty layouts. Every original control/rejection
assertion is unchanged. Corrected file SHA256:
`809701524fc31a5030b4f978c3aae8cf9d2803b91e6909172fa162cb9396ec96`.
This child has not executed it; the primary must authenticate its actual result
before treating the duplicate candidate-signature extension as proved.
