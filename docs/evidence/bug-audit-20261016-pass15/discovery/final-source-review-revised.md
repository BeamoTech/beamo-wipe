# Pass15 revised discovery patch review

Reviewer: `/root/pass15_discovery`; 2026-10-16 UTC.
Result: **APPROVE revised source delta**, pending the primary's applicable
checks. This supersedes the earlier approval that adjacent tests invalidated.
No runtime campaign or product/test edit was made by this reviewer during this
revision review.

## Exact bytes reviewed

Compared the changed source to the58-file starting archive
`/tmp/pass15-primary/starting-source.tar.gz`, SHA256
`a8d57369704ca71daf701a53641ca73f76d32076583d330ffa9dc96716f979cc`.
Same worktree, branch and HEAD as `final-source-review.md`.

- discover.py: `1925854e28b989c1b88dbfb8c6b1012a96615d7792837ace9b86b02cf129d4b3`
- models.py: `9fb0bcb97d35b1ee0f041f8ccb728fe8a2b9f173242a904bf2af6f7b5f42b95c`
- safety.py: `ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b`
- test_physical_observation_context_pass15.py:
  `319d7195e4a80be9c77ee00d5829da28d6680401352dc4dff6457b7ee3742323`

## Revision and safety assessment

`_physical_observation` now extracts serial and WWN independently. Each uses
the existing full parent/empty-parent-descendant expression, catches only its
ValueError and returns empty plus a per-field invalidity bit in this safety-
only context. Any independently valid other ID stays intact. It never truncates
or scrubs malformed IDs. Ordinary `node_to_disk` is unchanged: malformed target
IDs are still omitted per row, preserving recognized boot identity and direct
parse API behavior. Mounted rows still call that full validator before the
projection, preserving the existing full-inventory refusal for malformed
mounted physical metadata.

The duplicate signature includes projected Disk, tri-state RO and both
invalidity bits. Thus a malformed duplicate cannot compare equal to a valid
missing-ID observation after its unusable field is represented as unavailable.
Two malformed observations with equal projected facts cannot make a selectable
target because both still fail the ordinary full parser. A valid contrary WWN
is retained even if serial is malformed; an invalid WWN becoming unavailable
can only widen conservative alias protection in the nonselectable context.

The new404-case module retains all400 earlier assertions and adds4 meaningful
missing-vs-malformed duplicate ID cases (serial/WWN, both orders). Its strict
fake acquisition/path guards remain intact. The prior module's400-case pass
is historical evidence only; the revised404 cases and wider adjacency still
need fresh execution by primary on these exact bytes.

`previous_physical` is now distinct from the later parsed Disk `previous`,
avoiding the local variable type collision. The annotated physical dictionary
value matches the inferred three-part signature. No change to model/safety
bytes or the serialization/selection/anchor-WWN conclusions in the original
review was made; those source findings remain applicable.

No source objection remains. No independent runtime pass is claimed here.
Any further source-byte change requires updated exact-hash review.
