# Pass17 discovery and authorization source review

2026-10-17, Codex child `/root/pass17_discovery`. Shared dirty checkout
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, base HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. No product edits or runtime
tests have been performed for this review checkpoint.

Read current AGENTS.md, the current unfinished-work entry, relevant existing
discovery/identity regression sources, and the boot exclusion signal map.
`/root/dev/AGENTS.md` is absent, consistent with the existing handoff. Current
AGENTS governs; older guide claims/line references are historical context.

Reviewed source SHA256:

| File | SHA256 |
| --- | --- |
| src/beamo_wipe/discover.py | 0e77fcf0fa626e945c40fae8c8e5f544b735490f4acf8c718260abbabb20197f |
| src/beamo_wipe/safety.py | ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b |
| src/beamo_wipe/models.py | 9fb0bcb97d35b1ee0f041f8ccb728fe8a2b9f173242a904bf2af6f7b5f42b95c |
| src/beamo_wipe/methods.py | edf22b0a3cc4fb5de61c43a5ab82cccafbf6280270753c802f58ca6fe1ae6e13 |
| src/beamo_wipe/wizard.py | be375a0861ec569a652e15f9f572bfa689f40048d736c5bedef641453d464bbb |
| src/beamo_wipe/nwipe_runner.py | cd49b65a607f152bd53675dafef80777d49b2fc02afd54f545605b3ccf958175 |

Candidate awaiting an isolated fake proof: hardware-ID fallback returns the
first nonempty descendant SERIAL/WWN. When the physical parent omits its ID,
two conflicting descendant IDs are silently reduced to one. A separate path
sharing only the later descendant ID is not represented in boot or mounted
alias reconciliation. Relevant source: `_first_descendant_field` and its use
by `node_to_disk` and `_physical_observation`. Existing
`tests/test_discover.py::test_serial_is_inherited_from_child_when_disk_serial_is_empty`
establishes that child fallback is used as physical identity. No runtime
failure claim is made yet; root has been notified.

Reviewed and rejected as new bugs:

- Pass16 already reconciles filtered same-path duplicates and includes optical
  nodes in cmdline fallback competition. These are retained fixes.
- Missing/invalid real RO metadata is rejected by the production validator;
  permissive older injected fixtures do not bypass the real invocation.
- Final rediscovery's identity helper does not itself repeat every initial
  gate, but actual discovery applies boot/mounted aliases and produces the
  target collection used by that helper. A handmade inconsistent object is
  not evidence of a production bypass.
- A malformed nonfinite size may raise from a direct helper; the public
  discovery boundary catches it and returns no targets.
- Mapper filesystem ancestry, flat mount propagation, repeated physical rows,
  unresolved holders, and UUID aliases have explicit refusal/coverage paths.
- Model/label fallback can make presentation metadata equal while raw MODEL
  differs, but the requested invariant specifically binds path, serial, size
  and WWN; this review has no supported missing-raw-model bug claim.

Remaining work: root admission of the bounded fake proof, independent result
validation, and final exact-byte review after any accepted change. Existing
incident/historical qualification blockers remain in the canonical work record.
