# Final pass17 source cross-review, revised for unknown WWN alternatives

2026-10-17, Codex UI/boot peer. Source-only: no runtime campaign, source/test edit,
privileged action, hosted job, build or external side effect in this review round.
Exact four runtime and eight new test hashes are in `final-cross-review.json`.

This review supersedes `final-cross-review-before-wwn-unknown.md` and its JSON.
The prior review missed the malformed-WWN unknown-alternative defect subsequently
caught and proved by root. Its earlier no-objection conclusion does not qualify
those prior bytes. Root reports the exact 48-case proof as 16 intended failures /
32 controls; root retains the original proof and owns subsequent runtime gates.
No peer runtime pass is claimed here.

Exact revised discovery SHA256:
`a2fa08ce083d8b99403473ab8646a6b19f01157d1c2fd9df73e8469c92836bc4`.
Runner remains:
`465d3495bd36b3be2507798ad3b57930645c165ba025a2afbe2ea0ca6c45e39d`.

The previous discover bytes were independently reconstructed by reversing only the
five expected uncertainty edits, then authenticated against their prior reviewed
`7dbff4e...` hash. `wwn-unknown-incremental.diff` is that exact delta. Runner, both
UI sources and five existing pass17 test modules retain identical reviewed bytes.
The bridge and duplicate modules differ only in their first-line docstrings;
reconstructing those lines authenticates their old hashes. Their assertions remain
unchanged. The eighth module supplies the 48 uncertainty cases.

No material source objection remains on the exact revised bytes:

- `_PhysicalIdentityContext` already retained separate serial/WWN malformed bits.
  The unresolved-identity tuple now carries the correct WWN bit (`context[3]`), so
  malformed WWN alternatives no longer disappear before protection decisions.
- When malformed WWN data leaves an unknown alternative, the observed valid WWN
  key set cannot exhaustively disambiguate a protected anchor. The early contrary
  key-set rejection is therefore disabled only in that unknown case. A retained
  valid matching WWN still immediately protects; a contrary candidate plus unknown
  alternative permits the existing serial candidate match to protect the component.
  This repairs the ROOT/LEAF serial bridge without inventing an unknown WWN value.
- With no malformed WWN alternative, the prior authoritative contrary-WWN logic
  remains exact: known distinct keys still disambiguate serial reuse, including
  through a bridge. A meaningful physical parent WWN remains authoritative and
  suppresses descendant errors before the malformed bit is computed. The new
  authoritative-parent controls exercise that boundary explicitly.
- An unknown WWN flag alone never establishes a protected alias or creates a target
  identity. A candidate WWN or serial still needs to match the existing protected
  component. Unrelated malformed singleton observations preserve independent
  targets; the new unrelated controls exercise both child orders, both tree shapes
  and four malformed representations. Protected matches cause inventory refusal.
- Parser-local candidate tuples still never become selectable Disk identity,
  confirmation peers/tokens, argv or a public model field. Duplicate signatures
  retain normalized candidate sets and malformed bits. Parent authority,
  placeholder fallback, duplicate contradiction and malformed unrelated contracts
  remain supported by the earlier modules, whose assertions are unchanged.
- Runner no-erasure proof still requires native timestamp/severity context when
  available. Bare legacy parser inputs retain their explicit contract. Unattributed
  skip/open/geometry guards remain negative context for actual activity, yielding
  indeterminate rather than success or an unsupported no-erasure claim.
- Large-log projection retains the first native record in original order and
  existing byte budget. No size cap, pathname/inode authentication, explicit
  completion evidence, method-count or engine/lock-ownership gate weakens.
- Initial UI fixes and 49 tests retain their reviewed bytes: exact startup timer
  retirement and post-countdown canonical-terminal input retirement. No additional
  UI, public API, claims, method, nwipe flag, boot ordering or publication change.

Root must finish focused/full checks against this latest source. This source review
cannot substitute for them. Physical devices, isolated ISO/QEMU and native Windows
acceptance remain outside this review; safety-changing work requires a future
`safety:` commit after all required acceptance criteria pass.

Final fixture-lint annotation update: root added one imported-fixture `# noqa: F811`
comment in each of the duplicate and WWN-uncertainty test modules. Independently
compared exact retained pre-annotation copies from the failed lint snapshot with
the current files. Their prior SHA256 values match the previous review receipt;
ASTs (excluding location metadata) and all assertions are identical. All four
runtime files and six other new test modules remain byte-for-byte unchanged.
`fixture-annotation-ast-equivalence.json` retains the exact two diffs, before/after
hashes and assertion counts; the final JSON test hashes now identify current
comment bytes. Pre-annotation review receipts are preserved separately. This was
static comparison only; root owns the replay and final full gate.
