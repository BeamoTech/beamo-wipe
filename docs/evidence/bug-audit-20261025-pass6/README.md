# Comprehensive audit pass 6 — 2026-10-25

**Available review and portable/static checks are finished. Full source, native,
artifact and physical acceptance remain BLOCKED / INCOMPLETE.** One pre-existing
P3 sound-control defect was proved, minimally corrected and independently reviewed.
No new proved wipe-safety or completion false-success defect emerged in this pass.

Owned worktree: `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`,
branch `codex/wipe-audit-20261024`, base/HEAD
`9764d93ac21273aa79ae4618629b0a30e3eda271` plus dirty changes. The default and
peer checkouts were not edited. Original owner instructions authorize bounded
delegated review and require independent proof before fixes.

Raw evidence: `C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261025-r6`.
Machine-readable records: [verification.json](verification.json) and
[reviews.json](reviews.json). [R5](../bug-audit-20261025-pass5/README.md) remains
immutable at its original scope; this pass does not turn earlier incomplete
gates or historical observations into passes.

## Corrected finding: R6-SOUND-1, P3

The dialog ignored a known mute observation when the independent volume query
failed. An initially muted output could display Mute and keep issuing mute=True
on repeated clicks. Exact backend-query and UI callback AST with independent
fake commands reproduced four failures and four normal controls before the fix;
all eight current observations match after it.

`SoundDialog._show_volume` now consumes known, available mute state independently
of volume and preserves the last accepted state for absent/unavailable/unknown
observations. The production change is limited to that condition and assignment.
The new `tests/test_sound_partial_state.py` checks labels and successive commands.
No engine, authorization, disk-selection or completion behavior changed.

Fresh independent sound review found no concrete regression: 55 current fake
observations match; 51 historical observations reproduce 19 old mismatches and
32 positive controls. It exercised exact list/query/set and real dialog submit/
poll callback AST through independent fake boundaries. Known volume/unknown mute
now intentionally preserves the previous accepted state. Unknown readback does
not prove a command's actual audio effect. Parent read the result and checked
the exact scoped source and sealed evidence. Native GTK/audio remains untested.

## Completed bounded review

| Scope | Reviewer observations | Current input binding | Disposition |
| --- | --- | --- | --- |
| Disk identity, ancestry, authorization, launch/stop ownership | 194 product-model + 3 harness guard controls | 17 functional/guide inputs | No new proved defect |
| Completion, progress, persisted evidence, recovery, retries | 388 AST/fake observations | 8 modules | No new actionable finding |
| Build, manifest, checksum, handoff/publication transactions | 95 AST/in-memory observations | 36 inputs | No new concrete finding |
| Sound correction | 55 current; historical cases separate | 10 inputs | No concrete regression |

All four delegated tasks are terminal with bounded no objection. Parent reviewed
the results and relevant oracle/probe scope and independently checked current
source hashes and evidence readback. Parent did not rerun the reviewers' matrices;
these are not an additive pytest total or native acceptance. Scope hashes,
commands, failed harness attempts and limits are retained in each RESULT packet
and the four `parent-*-review-validation.json` records.

Parent additionally inspected report-intent/export/receipt/privacy/UI call chains
and ran 26 exact receipt controls. Concurrent sharing changes at DONE and raw
report-candidate ancestry were not established as new product defects. Accepted
large-log suffix refusal, withdrawn numeric-controller-reuse speculation and
unproved native interruption/errno candidates retain their prior qualifications.

## Available verification and exact identity

- New Windows-hosted portable pytest: **2 passed nodes + 14 subtests**, exit 0,
  no failures/errors/skips. Only exact AST and fake GTK/audio execute.
- Four current cache-free Ruff commands exit 0. Windows-hosted mypy with Linux/
  Python 3.11 stubs passes 52 source files; five pre-existing untyped-body notes
  remain. These are static checks, not actual-Linux execution.
- 743 Python syntax files and the generator's
  embedded Python parse. Source remained unchanged after those checks.
- Earlier R5 portable 254 + 37 subtest evidence is rebound only to its exact
  unchanged inputs. It was not rerun or relabelled as this pass's fresh execution.
- Final census: **932 inputs**, identity `7e14f2ffb55ab8323365aeb06a34d284277efc6ae1df3a9b72905c6e0b382376`.
  Only sound_dialog.py and its new test differ from entry. The verified overlay
  has 81 paths, SHA-256 `e18cb63cdd7f89c3b1f2473b8479810caa01e4efd3e52437e676f79f0e52561d`.
  Current source, shared guides, captured peer inputs, index and whitespace
  observations match the preserved records.

The first new pytest attempt failed before collection because the audit boundary
refused the existing Windows console dependency's ctypes bootstrap. The corrected
driver bootstraps that tool dependency before the probe boundary and refuses
external actions throughout test execution. Initial Ruff S102 was resolved with
a documented local trusted-AST annotation, consistent with existing tests; no
assertion or global rule was weakened. Tested/current test ASTs are identical
after that comment/annotation. An old-key observer adapter setup failure is
retained; only the entry key translation changed. Reviewer setup failures remain
separate from product outcomes. No blind gate retries or changed deadlines.

## Remaining acceptance and concrete next work

- Actual-Linux/full gate admission remains blocked. Final observed C: free bytes:
  **2,360,705,024**, below the unchanged **8 GiB** floor.
  No WSL gate/admission retry, peer/cache deletion or resource-floor reduction.
  Capacity cause remains unknown. Restore adequate capacity through separately
  authorized work, establish current peer admission, then use a freshly reviewed
  controller and unique final-identity phase chain with original gate limits.
- Full main/Orca containment is unimplemented/unqualified: PID-init/reaping,
  lifelines/private proc, service/interop exclusion, aggregate resource limits,
  bounded writable storage/logs and the ten finite containment selftests are
  required before a full run. Earlier timeouts remain incomplete.
- Native launch/kiosk question remains **UNPROVEN**: descriptor-path engine
  execution and kiosk `pgrep -x nwipe` may interact. Root checked primary kernel,
  procps and pinned main source; this is a source-supported concern, not observed
  native engine behavior or a proved missed live engine. Resolve with harmless
  owned native fixtures and inert power recording before publication. See raw
  `native-process-name-question.md`; no speculative source edit was made.
- Native GTK/audio, Go/startup/platform/artifact and separately authorized final
  public ISO/QEMU/hosted verification remain pending. Lab doctor/sync/Wipe-plan/
  report preparation all exit 0 with integrity VALID at Lab commit
  `d3d0959bb26b17531464dbd1ba233d4d842ad581`; old configured adapters do not qualify
  this dirty source. No observed VM worker does not grant guest admission.
- Physical Task119 reconnect/cold readback, valuable-disk disconnection, firmware
  boot, Secure Boot trust/revocation/SBAT/enforcement remain **NOT TESTED/BLOCKED**
  until an explicit owner physical-session update and original safety/recovery
  prerequisites are satisfied. Successful boot alone remains insufficient.
- Commit/push/merge/release await required gates and authorization.

Windows, remote access, physical disks/USBs and Lab's pre-existing notes are
preserved. No real nwipe, guest, device/firmware/service/security/network/power
change, hosted job or new spend occurred. Existing historical backlog is retained.
