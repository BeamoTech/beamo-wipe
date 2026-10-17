# Pass18 discovery candidate: pathless physical alias bridge

Date/author: 2026-10-17 / Codex discovery subagent. Source-only review;
the root owns all runtime admissions and proofs. Product patch applied only
after primary proved both cases and approved the exact diff below.

Root proof checkpoint: primary's authenticated `original-proof-review.json`
reports this exact 208-case module as 96 intended assertion failures and
112 passing controls, zero errors/skips. All 762 starting inputs remain
unchanged. The module is frozen at SHA256 `04eec1aa841a1b30d65acd3bcdac5d61b0ef794940e03e78010acd7fe8ee1ef7`.
This proves valid pathless alias loss.

Prepared adjacent source-only probe: `malformed_pathless_probe.py`, 32 cases,
SHA256 `1407a8632fd71737e65744d7bc599a52930a3541b1d9922d0e48a99ff3edae31`.
Primary also proved 16 intended assertion failures and 16 passing controls,
zero errors/skips, on unchanged starting discovery. The probe includes two
separate pathless rows sharing no usable path and reuses the existing
native-rejecting fixture. Root authorized copying the exact bytes to
`tests/test_pathless_unresolved_identity_pass18.py`.

Approved patch preserves a hardware-only projection of each pathless row in
safety observations, never in target rows or duplicate-by-path keys. Size,
display and transport defaults preserve prior skipping of unrelated unusable
metadata. Existing helper retains malformed/conflicting candidate keys in a
private unresolved tuple with unknown empty path. Empty or `/dev/` observations
are excluded from component path equality, and unknown unresolved paths cannot
match by path. The existing hardware alias rule retains meaningful parent
authority and known contrary-WWN disambiguation.

Exact incremental patch: `discover-pass18.patch`, SHA256
`85984cf10081a82745e8bc413f0020d673e299e531150b0e80727ff3940d23e8`.
Patched `discover.py` SHA256
`b66f3f50692dbeaa7cfad3ed87ed1edea4530756e45b3bbd057fff0ee0278a29`.
The frozen 208-case module and canonical 32-case copy keep their proof hashes.
No runtime was run by this subagent; primary must independently review the
exact patch and execute fixed/adjacent regression and final gates.

Repository: BeamoTech/beamo-wipe; branch `fix/safety-audit-20261015`;
HEAD `35107a8d1a701093eac876a58ab4efd50e291673`; worktree
`/root/dev/Beamo Wipe`. All dirty inherited work preserved.

The physical observation loop in `discover.py` skips any row whose strict
`node_path` is empty or `/dev/`. That is appropriate for target creation but
also discards its serial/WWN alias facts. A serial-only protected anchor A,
pathless physical row with serial A and WWN X, and valid target with serial C
and WWN X can therefore lose the bridge joining the target to protected
storage. The inverse serial/WWN chain has the same proved gap.

Prepared proof: `tests/test_pathless_physical_bridge_pass18.py`, 208 cases:
192 core cases (2 protection kinds × 4 pathless forms × 4 alias chains ×
6 row orders) and 16 meaningful-parent hardware authority controls.
Expected original result: 96 intended exclusion failures and 112 adjacent
controls. The guard fixture is the existing pass15 `fake_machine`, rejecting
native acquisition, subprocess launch and `/dev`, `/proc`, `/sys` opens,
with explicit identity realpaths for injected `/dev` paths. The module does
not run any engine or host inventory. An overlapping pathless row may force
full refusal or protect the alias; an unrelated pathless row or a chain
disambiguated by distinct known WWNs must preserve the valid target.

Root execution suggestion: no-space project Python, rejecting child PATH
guards, `python3 -m pytest -q tests/test_pathless_physical_bridge_pass18.py`
with JUnit and transcript retained. No GUI or platform dependency.

Source hashes before root proof:

```text
a2fa08ce083d8b99403473ab8646a6b19f01157d1c2fd9df73e8469c92836bc4  src/beamo_wipe/discover.py
ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b  src/beamo_wipe/safety.py
be375a0861ec569a652e15f9f572bfa689f40048d736c5bedef641453d464bbb  src/beamo_wipe/wizard.py
04eec1aa841a1b30d65acd3bcdac5d61b0ef794940e03e78010acd7fe8ee1ef7  tests/test_pathless_physical_bridge_pass18.py
319d7195e4a80be9c77ee00d5829da28d6680401352dc4dff6457b7ee3742323  tests/test_physical_observation_context_pass15.py
```

Current guide/backlog and product constraints read; shared `/root/dev/AGENTS.md`
is absent. Inspected production lsblk validation, boot-source precedence,
typed source matching, physical duplicate reconciliation, mounted ancestry,
hardware fallback ambiguity, token uniqueness, rediscovery and authorization
binding. No other verified defect yet. Pending acceptance: primary failing
proof; then root-coordinated minimal fix, regressions/controls and local gate.
