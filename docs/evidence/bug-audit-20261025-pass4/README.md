# Comprehensive audit pass 4 — 2026-10-25

Status: source corrections reviewed and saved; remaining qualification BLOCKED.
No release qualification, staging, commit, push or hosted run.

Owned worktree: `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`,
branch `codex/wipe-audit-20261024`, base
`9764d93ac21273aa79ae4618629b0a30e3eda271` plus dirty changes.
All 922 entry functional/configuration inputs matched R3 at
`1016e41e61b2f78a4cf84841c8657b5cc55a4ae09a2553668ffb5635a909df51`.
The default checkout and peer were not edited. The latest type-corrected snapshot
has 926 functional inputs, identity
`fc2d15fdfeebe3aa9d3352f752bf5f1dba0d7deff34042e223b879d2212b829b`.
Its 72-path source overlay was read back against every frozen input; SHA-256
`6b81da679f125d044a57d81c897963b7547d4cdd88141d022338c52e37645777`.

Raw evidence root:
`C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261025-r4`.
The [prior pass](../bug-audit-20261025-repass/README.md) retains previous fixes,
withdrawn hypotheses and incomplete gates; it does not qualify this snapshot.

## Findings and corrections

Each finding was independently reproduced by root before correction.

| Finding | Correction | Causal evidence |
| --- | --- | --- |
| P2: interruption strands an acquired engine/wipe-lock descriptor; partial engine ownership can double-close | Empty engine owner before acquisition; protected acquisition/validation; immediate lock ownership; detach before close | Root: six failures/four controls before, ten pass after |
| P2: engine close replaces the original launch refusal | Explicit primary error through every engine cleanup branch; standalone failures remain visible | Root: nine failures/eleven controls before, twenty pass after |
| P2: checksum publication discards concurrent foreign SHA256SUMS | Retain validated prior snapshot/absence before manifest rewrite; use existing collision-preserving publication; hash exact verified manifest bytes | Root: two failures/three controls. Implementation: 22 pass after versus 15 pass/seven fail before |
| P2: French curses discard rejects its advertised accented phrase | Decode UTF-8, matching shipped LANG=C.UTF-8; retain exact phrase/generation checks | Root French failure/English control; 31 direct AST controls pass across six localized phrases |
| P3: evidence token failure leaks an open directory descriptor | Initialize ownership before protected acquisition and token generation | Root token OSError/KeyboardInterrupt failures; expanded ownership matrix retained |
| P3: evidence close errors mask cancellation, which callers swallow | Explicit operation-local primary error; all detached closes attempted once; standalone errors visible; fixed-stage/type reporting | Root identical-interruption control and masked-interruption failure; reader/writer/inspector/export/caller controls |

The engine assertion wrapper initially retained an interruption boundary at
finally entry. Root reproduced four failures and corrected the protected normal
close; four now pass. Final launch review passes 85 cases versus 51 failures and
34 controls on entry. Failed intermediate receipts remain retained. Finite
bound-ownership and line-event probes do not prove arbitrary-bytecode cleanup.

The checksum fix preserves build-only versus release verification, all three
shell checksum rechecks, verified prior reruns and the existing atomic writer.
Its 21 Linux fixture cases remain unrun. An existing shell-sidecar test's fake
Python producer now models aggregate checksum creation in the initial Python
transaction; every existing assertion remains intact.

The shutdown document now describes localized confirmation and existing EOF
behavior accurately. No controller shutdown behavior changed for this item.

A fake-only FileExistsError-from-close experiment also exposed overly broad
collision recovery. Ordinary Linux close producing EEXIST was not demonstrated.
Narrow error-origin hardening is defensive work, not a newly proved real export
or erase-completion defect. It preserves the established two-argument writer
boundary. A tentative keyword variant was rejected during review because it
broke existing injectable wrappers; that variant was not retained.

## Review and coverage

Fresh bounded reviews covered completion/projection/progress/evidence,
wizard/recovery/export/interface ownership, build/handoff/launchers and boot
packaging. Root additionally inspected discovery, authorization and launch.

- Completion review: 6,700 full/projected comparisons and 69 terminal controls
  found no new erase-completion false-success or misleading NOTHING_ERASED
  finding. These bind retained entry parser bytes; changing launch code has
  separate review.
- Recovery review: 30 controller and eight adjacent UI controls pass.
- Root current-source adapters: 27 topology and 60 argument controls pass,
  using invented paths/rdev/process/log boundaries. A considered optical
  ancestry bypass was not established in production discovery.
- Independent final checksum/locale review: 87 modeled controls pass; seven
  scoped file hashes unchanged; no concrete objection.
- Final launch review: 85 modeled cases pass, scoped hashes unchanged, no
  further objection; trace and fake-module restoration verified.

Raw handoffs: completion-review/HANDOFF.txt,
recovery-review/review-summary.json, build-review/RESULT.md,
launch-final-review/handoff.json, checksum-implementation/RESULT.md,
checksum-locale-final-review/RESULT.md and
evidence-cleanup-implementation/HANDOFF.txt. Setup errors, failed intermediate
patches and corrected harness expectations remain recorded. Assertion counts
are not distinct bug counts or actual-module/platform acceptance.

All eight delegated tasks are complete with no pending child run; see
[review states](reviews.json). The eighth task assessed full-suite containment.
Its [design and ten-case acceptance checklist](/C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261025-r4/full-containment-review/review.md)
requires controlled PID-namespace init lifetime, private proc/service endpoints,
effective aggregate resource limits, bounded writable storage and successful
inert ownership/limit selftests. These controls are not implemented or qualified.
Resource recovery alone cannot admit the full gate.

## Verification and remaining acceptance

| Latest source-bound check | Actual result |
| --- | --- |
| Portable Windows AST-only pytest | 124 passed, zero failures/errors/skips; process/pytest exit 0; input hashes unchanged |
| Linux canonical syntax/shell/security/lint/types | PASS, queried exit 0; 52 source files type checked |
| Linux new regressions and three GTK sound-state cases | 504 passed, zero failures/errors/skips; queried exit 0 |
| Python/embedded-Python syntax and overlay readback | 737 Python files plus changed generator Python parse; exact overlay readback passes |
| Next Linux adjacent batch | Admission refused before WSL/test startup; controller exit 2, test exit unknown/unrun |

The Windows set is included in the Linux 504-case selection; these counts are
separate platform replays, not 628 distinct tests. Windows tests execute extracted
source against fake OS/process boundaries and do not import the Linux product or
qualify a real application/engine/terminal. The final run uses one bounded process
with process/network creation refused; no external-operation event occurred.

Earlier Windows child runs include 45-second timeouts and are retained as
incomplete. A diagnostic replay passed, but neither progress nor Job emptiness
was promoted to general descendant ownership or acceptance. Read-only observation
found no recorded old roots/immediate child links remaining. A later refusal
proved JUnit's hostname query can invoke Python's Windows-version shell fallback.
Only the reporter-local hostname provider now uses the actual direct OS hostname
API; global platform state, tests, refusal policy and timeouts remain unchanged.
Other startup stalls and the prior Go startup timeout remain unproved/unresolved.

Initial Windows static checks found one no-op lambda style violation and three
missing annotations for deliberate checked-in test-code execution. Root corrected
the spelling and added narrowly documented annotations; assertions/global rules
were unchanged. All four Windows static commands passed on that snapshot.
Linux lint then caught two optional-return annotation errors in the checksum
helper. Explicit `return None` corrected them; fresh `r4v2-lint` passes on the
latest frozen snapshot. Existing untyped-body notes and the TODO grep matching
the unchanged PLACEHOLDER_RE literal are retained as baseline diagnostics.

Capacity initially blocked Linux work, then recovered to 10,436,440,064 free C:
bytes. The new uniquely named Linux phases ran with unchanged 8 GiB disk/1 GiB
RAM admission and 300-second phase budgets. Source, namespace and owned group
cleanup checks passed. A subsequent read-only sweep of the completed phase's
exact mount/network namespaces and unique sentinel found no matching processes
and no inaccessible same-UID entries. It signalled no process.

The next batch was refused at 6,432,006,144 free C: bytes and 811,606,016 available
RAM bytes. A later observation showed 4,409,245,696 bytes free and 997,507,072
available RAM bytes. The resource cause is unknown. No floor/timeout was relaxed,
no gate blindly retried, and no peer cache/worker, shared WSL configuration or
physical media was changed. A coordination note was saved; it is not proof of
peer acknowledgement.

The final report observation was 3,996,053,504 free C: bytes and 998,588,416
available RAM bytes, still below admission. No further gate was started.

To resume bounded batches, first obtain fresh adequate capacity and peer-worker
observations. Prepare a new reviewed/pinned controller from
`candidate-checks-r4-v2.py` with fresh phase names and an explicit chain from the
successful `r4v2-new-regressions`. The existing controller hardcodes its phase
names; do not rename receipts, rerun the consumed `r4v2-adjacent` name or overwrite
the refusal. Retain source, ownership, admission and timeout guards.

Raw `final-verification.json` was a provisional earlier snapshot and included a
hardcoded BLOCKED label despite its recovered-capacity observation. The explicit
`verification-capacity-erratum.json` preserves and corrects that label. Use the
latest source and phase receipts, not that provisional label, for disposition.
The reconciled [verification record](verification.json) binds the latest frozen
source, raw receipt hashes, actual exits and remaining blockers. Its immutable
raw counterpart is `completion-verification.json` under the evidence root.

Lab revision d3d0959bb26b17531464dbd1ba233d4d842ad581 remains unchanged. Fresh
doctor/sync/Wipe-plan/report are preparation PASS, receipts verified VALID,
candidate_acceptance=false. They do not qualify product source.

Remaining: adjacent actual-module Linux tests, the 21 checksum publication
fixtures and other evidence/build shell transactions, large-log suites,
preview/negative phases and the full local gate with reviewed service and
resource containment. Canonical lint/types/shell syntax already passed for this
snapshot. Preserve the
older 300-second timeout and incomplete full gate as incomplete. Native Go
startup remains blocked after its earlier owned 45-second timeout; no blind
retry. Native launcher/macOS/artifact and separately authorized final-public
ISO/QEMU/hosted gates remain open.

Physical reconnect/readback, valuable-disk disconnection, real firmware/Secure
Boot and device acceptance remain NOT TESTED / BLOCKED. No host restart, USB/disk
change, guest, host-service change, real nwipe, release or historical-artifact
operation occurred. Owned private test D-Bus/Xvfb were covered by the bounded
Linux phase receipts. Changes remain uncommitted until required gates are
satisfied.
