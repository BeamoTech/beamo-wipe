# Pass19 discovery source audit

2026-10-17; Codex discovery child; BeamoTech/beamo-wipe at
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, local HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Source-only review; no application,
tests, native inventory, processes, devices, network or hosted job executed.
Parent owns all proof, authorization to fix, runtime verification and canonical
task status. After parent confirmed the failing proof and approved the minimal
change, this child edited discovery and copied the exact proved module into
canonical tests. No runtime was executed by this child.

Reviewed `AGENTS.md`, relevant pass18/pass17 unfinished record, discovery,
safety, wizard final identity handoff, boot exclusion signals, relevant existing
discovery and ancestry regressions. `/root/dev/AGENTS.md` is absent. Current
`discover.py` SHA256 is
`b66f3f50692dbeaa7cfad3ed87ed1edea4530756e45b3bbd057fff0ee0278a29`;
`safety.py` is
`ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b`.

## Proved candidate P19-DISC-BCACHE, approved fix awaiting parent verification

The existing unmounted filesystem ancestry check at discover.py1879–1904
includes TYPE `bcache`, but it omits a bcache device reported as TYPE `disk`.
The latter is already the documented/tested source shape:
`tests/test_audit_20260908_discovery.py:344` and discover.py1929 both explicitly
describe it. `_is_stacked_holder` at717 recognizes NAME `bcache*` irrespective
of TYPE and is used by the mounted-chain guards, but the unmounted filesystem
ancestry check does not call it.

For an unmounted root-level `bcache0` with an opened filesystem UUID and no
PKNAME, `_resolve_owner_disk` treats TYPE `disk` without PKNAME as its own
physical owner at584–587. The row is not an eligible whole `/dev/...` target,
and `_flat_layout_id`/`classify_disk_contents` skip its evidence when looking
for raw disk `sda`. With unknown/cyclic PKNAME the owner is instead empty,
but the filesystem ancestry check still omits the TYPE `disk` holder. With
contradictory tree versus PKNAME the same omission avoids the explicit
filesystem contradiction rejection. Mounted bcache cases already refuse.

The candidate contract is the current guard's own explanation: an opened
filesystem with no physical ancestry can belong to a candidate disk; omitting
it hides contents and weakens layout identity. Missing or contradictory ancestry
must fail closed. Parent executed the corrected probe on the unchanged original
discovery hash and reported 24 intended AssertionError failures / six adjacent
controls, zero errors or skips. Parent inspected the actual failure and approved
the minimal source change before any product edit.

Prepared `unbound_bcache_filesystem_probe.py`, SHA256
`0d85a54e13de50b18b3402896f2bb426e0adad6e3bfd96b2c86cef21cdf4e127`.
It has 24 source-predicted failing cases over missing, unknown, cyclic and
contradictory ancestry; ext4/UUID/label, UUID-only and PARTLABEL-only evidence;
injected and production-metadata-stub public routes. Six controls cover valid
flat/tree binding and an unmounted orphan without filesystem evidence. It
reuses the retained pass16 fixture's explicit native-acquisition guards. Only
AST parsing was performed here. Parent's first runtime attempt failed all 30
cases at fixture construction: `_disk("sdc", name="bcache0", ...)` supplied
the name twice. This is a fixture error and supplies no product proof. The
constructor now creates `_disk("sdc")` and updates its metadata afterward;
all assertions and parameters are unchanged. Parent retained the original
fixture failure and owns the corrected rerun under a separate evidence name.

The approved fix reuses the existing stacked-holder predicate in the filesystem
guard and excludes stacked holders from both physical-owner terminal shortcuts.
This follows valid tree-parent and flat-PKNAME binding rather than returning
`bcache0` as an independent physical owner when PKNAME is missing. It preserves
empty unmounted orphan behavior, mounted membership refusal, hardware alias
projections and meaningful parent IDs. No method, argv or authorization gate was
changed. Simply adding the predicate to the filesystem guard would have been
insufficient for missing PKNAME because the old owner returned `bcache0`.

First-fix discovery SHA256 is
`523c1443360dd89e6c4e436695c56df878f2bfef24086cecb6a98c110ddfb406`.
The exact corrected 30-case module was copied unchanged to
`tests/test_unbound_bcache_filesystem_pass19.py` (same hash as probe).
`discover-pass19.patch` SHA256 is
`d188fde6f0585b4b68994676a5942302800cd495e92081550a5719fd64e2b20d`;
`fix-source-receipt.json` records all assigned source/test hashes. Child checked
AST syntax and reread the exact incremental diff; parent owns fixed/adjacent
runtime verification and required gates.

## Rejected numeric-size hypothesis

`_as_int` converts a float directly with `int(value)`, whereas its string path
catches OverflowError. A valid JSON numeric exponent such as `1e309` can become
infinity and raise OverflowError in the direct branch. This initially appeared
to escape the public API, but the complete discover.py tail at2639 has a generic
`except Exception` that returns a blocked DiscoveryResult. The public API is
therefore fail-closed already. No product fix is justified by this discrepancy.

Prepared `nonfinite_size_probe.py`, SHA256
`430b60c80f9feb2772049b05d9a31cea546a92b5827bad4f2bcff34d0eec173b`,
before completing that catch-all trace. It remains unrun and is only a possible
38-case public control matrix, not a failing proof or a bug claim. Parent was
notified immediately when the catch-all rejected the hypothesis.

## Adjacent cases and transitive contradiction proved and approved

Parent requested two additional bounded source-only probes before final acceptance.
The original 30 module remains frozen. Parent then ran all 104 adjacent cases on
the exact first-fix source: descendant cases yielded 30 AssertionError failures /
44 controls; duplicate cases yielded 20 AssertionError failures / 10 controls;
zero errors or skips. Parent inspected actual failures and approved two additional
hunks before edits.

`descendant_holder_filesystem_probe.py`, SHA256
`91d29c2893a48dd878faf06089053714b092a5a424e58f9b23e5a5d1bdb09a10`,
has 74 cases. A blank unbound holder has no own filesystem row and therefore does
not enter the current guard, while an unmounted partition below it has a valid
partition name/PKNAME and no opened-holder TYPE. Its actual filesystem UUID can
be omitted from every raw disk's identity. This occurs directly below bcache,
LVM or linear holders, and through an intermediate blank crypt node. The probe
has 36 predicted failures for missing/unknown/cyclic physical ancestry and 38
controls for flat/tree binding, blank holder subtrees and an unrelated standalone
orphan partition. Parent must prove both first-fix and original-source behavior.
The initial prediction of 36 descendant failures was too broad: the six direct
bcache-partition cases already pass because `_is_stacked_holder` recognizes the
`bcache*` partition name. Parent's retained JUnit confirms this difference.
The broadened contract remains holder ancestry with actual filesystem evidence;
it must not reject every standalone orphan partition or blank subtree.

`duplicate_bcache_filesystem_probe.py`, SHA256
`fe520ce1c5adfde6cdac781c2edc9b4d85ddf1298cf70871944f624acbd16c7e`,
has 30 cases. `_reject_shared_device_ancestry` excludes all TYPE `disk` rows,
including the recognized bcache holders. Normal mixed populated/empty copies
are already rejected by final Disk reconciliation and are retained as controls.
Identical populated copies can have identical canonical Disk signatures; a
display-invalid copy can instead be omitted from that reconciliation while its
physical signature deliberately omits layout/display fields. Both cases may
leave one shared opened bcache device claiming multiple physical parents. The
probe has 20 predicted failing cases and 10 existing/adjacent controls, including
one-parent repeats, distinct bcache devices and a blank unmounted shared holder.
The runner peer independently identified the shared ancestry omission and
corrected the normal-mixed-copy hypothesis before any product change.

The approved shared-device guard now includes recognized stacked TYPE `disk`
holders while retaining unconditional ROM/partition/loop/RAM exclusions. The
opened-filesystem guard uses `_has_stacked_holder` to follow holder ancestry at
any unique depth; its evidence condition still requires actual filesystem/part
metadata rather than a blank partition's size alone. Both modules were copied
unchanged to `tests/test_descendant_holder_filesystem_pass19.py` and
`tests/test_duplicate_bcache_filesystem_pass19.py`. Root owns fixed verification.

Second-fix discovery SHA256 is
`158fae213e088c7dfcd0296eee78f4c68b8e3a732914cb2f05f3b1a8e1b24224`.
`discover-pass19-adjacent.patch` retains the first-fix-to-current change;
`discover-pass19-current.patch` retains the initial-to-current change. Initial
first-fix patch and receipt remain intact. `adjacent-fix-source-receipt.json`
records exact source/test hashes and root-reported proof counts.

Parent also requested a separate transitive-contradiction probe before any
resolver-consistency change. `holder_ancestor_contradiction_probe.py`, SHA256
`64d68bef146c0298cae17398b5e31286a8aa63ab00aceb4fee4c18bf29762736`,
has 72 cases: 24 source-predicted failures for a blank holder nested under raw
`sda` but declaring PKNAME `sdc`, with actual filesystem on a nested/flat leaf
at one/two depths across three known holder types and two public routes; 48
controls cover matching edges and blank subtrees. The second-fix FS checks compare
only the immediate candidate's parent; an ancestor holder's conflicting edge
could be followed silently by `_resolve_owner_disk`. Parent ran the exact probe
on the second-fix source and reported 24 intended AssertionError failures / 48
controls. The prior 134 canonical cases all passed in that same 206-case run.
Parent inspected the proof and approved consistency checks before any resolver
edit.

The approved final check compares each nonempty own PKNAME with a supplied tree
parent name, and does the same for each traversed ancestor. A conflict returns
`("", True)`, preserving the helper's ambiguity contract so relevant filesystem
callers refuse. Missing PKNAME still follows the existing tree fallback; plain
root disks remain authoritative; missing or cyclic ancestry keeps its existing
refusal. The exact 72-case module was copied unchanged to
`tests/test_holder_ancestor_contradiction_pass19.py`.

Final discovery SHA256 is
`47d73620758d07f6352e9afd6f8430091c35f1b6df9f113a0502f352465145e8`.
The final cumulative `discover-pass19-current.patch` SHA256 is
`9b7aea0d1bf544ce3fb02a63bc03ade97bd5de8d19088eb2e6ddc4bff369cb47`.
`discover-pass19-transitive.patch` retains the second-to-final change and
`discover-pass19-through-adjacent.patch` preserves the prior cumulative patch.
`final-source-receipt.json` authenticates every stage and all four exact canonical
modules / 206 cases. Child reread the complete final patch and parsed syntax.
Product edits are stopped pending root's fixed/adjacent/full verification.

All probes use the retained native-acquisition guard fixture. Only AST parsing,
source tracing and hashes were performed by this child; no runtime was executed.

## Boundaries rechecked without a new objection

Pass18 pathless rows retain hardware-only projections and invalid candidate
alternatives without becoming targets or confirmation peers. Empty paths do
not become a shared path in unresolved-identity checks. Protected closure keeps
the existing anchor-WWN rule, so contrary known WWNs continue to disambiguate
reused serials. Mounted hardware aliases remain protected before eligibility.

Final wizard and runner preflight identity checks bind serial, size, WWN,
path, displayed identity and filesystem layout; duplicate safe paths must have
exactly one observation. Owner context includes the listed peer set. No source
change is proposed to these rules. Unknown TYPE rows being hidden is an explicit
existing contract; speculative physical bridges through arbitrary malformed
TYPE values do not justify a separate policy change here.

Status: coherent ancestry fix implemented after separate root proofs/approvals;
fixed final verification pending. Exact next action is for parent to run the
fixed 206 cases and relevant adjacent discovery/identity checks under its approved
fake-device harness, authenticate the exact final bytes against original source,
then run applicable final gates. No acceptance pass is claimed by this child.
