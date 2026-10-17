# Pass 10 discovery and authorization audit — 2026-10-16

Repo/worktree: BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`.
Branch `fix/safety-audit-20261015`, HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
Existing pass8 local implementation/tests and pass8/pass9 evidence were preserved.
No source or repository test edits were made by this reviewer.

Read current project AGENTS and canonical unfinished-work record. The shared
`/root/dev/AGENTS.md` is absent, as recorded in previous audit handoffs. Parent
owns durable integration and unfinished-work updates.

## Bounded source review

Inspected `discover.py`, `safety.py`, `identity.py`, `methods.py`, `models.py`,
authorization/final rediscovery sections of `wizard.py`, and command construction
and immediate rediscovery sections of `nwipe_runner.py`.

Focused on schema coercion and malformed ancestry rather than relying only on
previous passing matrices: tree/flat partition parents, duplicate mapper ancestry,
shared filesystem and hardware aliases, source annotations/by-* link provenance,
mount evidence precedence and contradictory competing claims, production-only RO
and mount metadata requirements, path/name contradiction checks, mounted hidden
observations, final target and boot snapshots, inventory-bound consent and peer
swaps, method-bound argv validation, token cross-collisions, and countdown reset
and claim behavior.

No additional actionable defect was proved in this bounded review. Existing
fail-closed guards cover the reviewed malformed-parent, hidden-mounted-alias,
unresolved-live-source and changed-authorization paths. Integral float sizes are
an explicitly tested supported schema; generic stricter parsing would change an
existing contract without a demonstrated bug. No speculative code change made.
This is not a claim that the software is free of bugs.

## Verification

- `focused.xml` / `focused.log`: 425 passed, 0 failed, 0 errors, 0 skipped, 49
  modules, 6.523 s. Counts derived from JUnit in `focused-summary.json`.
- `selected-files.json` records the exact bounded suite. `run_focused.py` is the
  acquisition guard used around the tests; native lsblk/nwipe are prohibited.
  Guard observations: 16 fake findmnt calls, 2 fake mountinfo reads, 2 fake
  cmdline reads. Those host reads return empty fixture data.
- System `python3 -m pytest` was a setup failure because pytest is absent from
  `/usr/bin/python3`; zero tests ran. Its log is preserved separately as
  `focused-system-python-setup-failed.log`. Corrected run used the already
  installed `/tmp/beamo-wipe-audit-python/bin/python3`, no installation.
- `reviewed-source.json` preserves reviewed file hashes and source identity.

Tests were sequenced after the parent's GTK profile; no simultaneous pytest
campaign was started by this reviewer. The test process is retired. All inputs
were repository fixtures, injected dictionaries, fake subprocess/device boundaries
or ordinary temporary files. No native inventory, actual nwipe, connected-device,
USB, guest, host-power, build, hosted CI, commit, push or publication action.

Parent owns final comprehensive local gate, historical SIGTERM/timing analysis,
independent review of any other finding and final state/approval decisions.
ISO/QEMU/native Windows/physical acceptance remains outside this review.
