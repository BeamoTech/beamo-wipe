# Pass17 Beamo Wipe bug audit

2026-10-17 / Codex. Four areas are fixed locally after failing proofs: inherited
disk identity, no-erasure log attribution, plain-console consent and Tk startup
callback lifetime. Final local checks and artifact readback pass. Overall
acceptance remains **BLOCKED** by the existing incident/trace review and unavailable
platform acceptance below. Nothing was committed, pushed or published.

Worktree `/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Final runtime source SHA256:
`b4e76a50ff6e9d376b6a56f7d1b469192dd4284347923ac1aca02254664bf423`.
The [source receipt](primary/source-review.json) and
[762-input freeze](primary/source-freeze.json) identify the uncommitted result;
HEAD alone does not identify it.

- Discovery now examines all inherited serial/WWN observations. Conflicts and
  malformed values cannot hide later identifiers or a boot/mounted alias bridge.
  Parser-local candidate facts and malformed-WWN uncertainty survive filtering
  and duplicate comparisons. A meaningful parent ID remains authoritative;
  invalid identity never becomes a target identity. Some ambiguous inventories
  conservatively refuse all targets. Known contrary parent WWNs still disambiguate.
- A model containing an LF could forge a bare skip/open/geometry sentence and
  produce a false unchanged-disk explanation. Native logs now require a complete
  timestamp/severity record for that stronger claim. Projection preserves the
  first original native record within its byte budget and original order.
  Unattributed guards remain negative context when contradicted by erase activity.
- Plain console input queued during the five-second review could start the fake
  engine when the timer expired. Canonical terminal typeahead is now discarded
  before accepting the separate Erase action. Unusable terminal controls and real
  piped consent refuse; fake preview/test input remains supported.
- Tk startup now retires its exact current polling and initial focus callbacks
  before destroying the window, including after external destruction. Other
  interpreters' callbacks remain intact.

Only four runtime files changed from pass16. All other 750 starting inputs and
all previous work are preserved. Eight new modules add 1,247 regression cases;
33 retained audit modules contain 3,010 cases. Methods, argv, pins, claims,
launchers, build/publication automation and public data schemas did not change
in this pass. Any eventual commit containing these authorization/discovery
changes requires the `safety:` prefix.

| Verification | Observed final result |
| --- | --- |
| Exact private starting-source replay | 496 assertion failures / 739 controls; zero errors/skips; 1,235 high-level cases. The 12 new helper-only controls were deselected only on old source. |
| Nine local gate phases | All exit 0: lint/types, preview, boot-guard negative mutation, Go version/race/vet, Windows cross-build, 350,000 fuzz executions, full Python/Orca. |
| Full Python/Orca | 9,213 unique passes / 14 expected image-only skips; zero failures/errors/duplicate IDs. All 3,010 retained regressions execute and pass, including all 12 helper controls. |
| Fake runner semantics | 153 short/projection comparisons and 153 actual >1 MiB regular-file polls agree; 90 evidence/export-readiness/recovery/tamper roundtrips pass. |
| Cancellation/retry | 144 cases pass, including actual ordinary-file flock contention and descriptor retention during uncertain exit; ownership releases only after terminal confirmation. |
| Small-screen UI | 270 Tk/GTK layouts at 800×600 / 72 DPI across three languages/text sizes pass. All 27 critical Tk input allocations are fully visible; five actual PNGs viewed. Long body content intentionally scrolls. |
| Reports | 90 method/language/error/log-size cases pass; five retained bundles / 70 files authenticate against their COMPLETE manifests. |
| Artifact readback | All 754 starting inputs, 762 final inputs, 33-module archive, incremental/cumulative patches, 621 runner fixtures and 70 report files authenticate. Exact 12-file peer review matches final bytes. |

See [gate verification](primary/gate-verification.json),
[serial commands/times](primary/local-gate-status.json),
[campaign verification](primary/campaign-verification.json),
[campaign commands/times](primary/campaign-status.json),
[source/archive verification](primary/source-artifact-verification.json),
[visual review](primary/primary-visual-review.json), and
[final peer review](ui-boot/final-cross-review.json).

The Windows artifact is an actual 9,021,440-byte PE32+ AMD64 **test cross-build**
using pinned Go 1.26.8; SHA256
`d05ac4db6463aa6d7f51188f3bcfcfb4891aeab549ab481843538114904a76d9`.
It is not a shipped launcher or native Windows acceptance. The 14 skips are the
same two generated-live-config and 12 manufacturing/ISO cases as pass16; their
exact IDs/reasons are in the gate receipt. The lint TODO warning matches the
scanner's own regex literal; existing mypy unchecked-body notes are retained.

All substantive campaigns ran serially after the canonical main/Orca pair
finished. Runner campaigns reject process, signal, socket and native-path
acquisitions and recorded zero forbidden effects. The no-space interpreter and
eight immutable rejecting PATH guards prevent the known pass16 fake-shebang
fallback. They are not a universal OS sandbox. Twelve guard admission probes
pass. The three actual SDK calls across the baseline/failed-candidate/final runs
only list files in owned private local fixtures with fresh offline configuration;
no GCP CI, authentication or hosted job was invoked. No forbidden PATH fallback
was recorded. No real wipe engine, physical target, loop acceptance or guest
was invoked in this pass.

Earlier failures remain evidence, not passes: the first full candidate failed
three existing contradictory-log tests; 108 added mixed-origin cases proved that
regression before correction. Discovery's initial aggregation also lost physical
candidate context; 200 bridge and 32 corrected duplicate cases proved the needed
correction, followed by 48 malformed-WWN cases. Original invalid duplicate and
console fixture shapes are retained separately with corrected proof lineage.
Final lint initially reported two imported-fixture F811 notices; inline fixture
annotations preserve identical ASTs/assertions. Result authentication also caught
one trailing space in the audit note; its correction leaves all 762 gate inputs
unchanged. Raw failed results and superseded hashes are retained and explicitly
superseded by the final receipts.

Bulky exact raw transcripts, JUnit reports and test binaries are stored at their
original relative paths inside [primary/raw-evidence.tar.gz](primary/raw-evidence.tar.gz),
authenticated by [its byte index](primary/raw-evidence-sha256.json). This includes
the failed `candidate-one/` run and final `final.xml`/`final.xml.orca.xml`.
Starting inputs, final untracked tests, runner fixtures and report bundles have
separate checked archives in `primary/`. Five PNGs and geometry receipts are
in `ui/`. [SHA256SUMS](SHA256SUMS) covers every retained file except itself;
[retention verification](primary/retention-verification.json) records compaction
and readback. Working staging is also retained under `/tmp/pass17-primary`,
`/tmp/pass17-runner` and `/tmp/pass17-ui`; durable evidence is this directory.

Existing blockers remain in the
[canonical unfinished-work record](../../../.ai/memory/unfinished-work.md): review
pass16's unauthorized native regular-file loop-probe incident; recover/reconcile
the original pass8 unexplained SIGTERM attribution and pass9 failed timing trace.
Later successful tests cannot explain those historical events. ISO/QEMU,
native Windows, firmware/hardware and physical reconnect acceptance remain
**NOT RUN / BLOCKED** on this host. Review those incident/trace records before
acceptance, then qualify any final public candidate on prescribed isolated
workers and an authorized physical session. No commit/push/merge/release step is
marked complete, and this evidence grants no new production or device authority.
