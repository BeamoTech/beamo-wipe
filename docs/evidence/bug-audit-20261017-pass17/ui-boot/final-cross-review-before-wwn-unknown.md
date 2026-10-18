# Final pass17 source cross-review

2026-10-17, Codex UI/boot peer. Source-only; no runtime campaign, source edits,
privileged action, hosted job, build or external side effect in this review round.
Exact four runtime and seven test file hashes are in `final-cross-review.json`.
The initial two UI fixes and 49 tests retain their previously reviewed bytes.

Compared final `discover.py` SHA256 `7dbff4e97c5e4087681744ce02857c08c6f7173de355371aff838814e1b3a8ea`
and `nwipe_runner.py` SHA256 `465d3495bd36b3be2507798ad3b57930645c165ba025a2afbe2ea0ca6c45e39d`
against root's exact starting-input archive, and reviewed all seven new regression
modules. Root's focused/full runtime results remain separate acceptance evidence.

No material source objection found:

- Meaningful physical parent IDs remain authoritative. Otherwise every descendant
  contributes candidate keys; malformed/conflicting observations cannot silently
  choose a first valid child. Placeholders do not mask meaningful facts. Raw parent
  placeholder remains when no better descendant exists, preserving source contract.
- Candidate keys are parser-local tuples, never selectable Disk identity, picker
  peers, tokens, argv or public model state. Normalized key sets make duplicate
  observation comparisons deterministic; differing retained candidate context is
  rejected even if the invalid projection has the same empty identity fields.
- Valid other-field facts remain in physical projections. An unresolved bridge
  matching any boot/mounted protected component causes inventory refusal, so an
  omitted conflicting/malformed row cannot reopen a later target alias.
- Shared alias helpers and known-WWN disambiguation remain in force: authoritative
  contrary WWNs prevent serial-only bridges from overriding the protected anchor.
  Unknown/multiple candidate WWNs cannot manufacture a unique contrary identity.
  Unrelated malformed singleton observations still skip without erasing an
  independent sibling's identity; refusal is tied to a protected match or duplicate
  contradiction. The new tests cover both orders, both fields, nested descendants,
  parent authority, placeholders, malformed unrelated cases and contrary WWNs.
- Runner origin filtering only changes proof of *no erasure*. A native timestamp
  plus severity is required when such context exists. Bare legacy parser inputs
  retain their explicit contract. A short optional prefix or LF model continuation
  cannot authenticate a no-erasure guard in a real native-context log.
- Unattributed skip/open/geometry sentences still act as negative context when
  actual activity exists. They cannot be dropped to allow success; contradictions
  remain indeterminate. Attributed genuine skips retain occupied/open/geometry
  outcomes when no activity contradicts them.
- Large-log projection retains the first native record in original position and
  existing byte budget, rather than appending context out of order or promoting
  an unprefixed continuation to a legacy-only log. No byte cap, pathname/inode
  authentication, terminal evidence, method-count or lock-ownership gate weakens.
- Private helper signatures change only within discover's parser implementation;
  no public Disk/DiscoveryResult or runner API change is introduced. No claims,
  method mapping, nwipe flags, boot fallback ordering or publication change.

Minor evidence consistency note sent to root: bridge and duplicate test module
docstrings still call themselves "Unexecuted" even though root has executed and
retained proofs. This does not affect assertions; update descriptive text before
final freeze if desired. Exact reviewed hashes intentionally retain that text.

No peer runtime validation is claimed. Root must finish source-bound focused/full
checks after its latest edits; real devices, ISO/QEMU and native Windows remain
outside this source review. All safety-changing work requires a future `safety:`
commit only after required acceptance criteria pass.
