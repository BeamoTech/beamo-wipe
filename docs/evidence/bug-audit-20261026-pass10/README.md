# Comprehensive audit pass 10 - 2026-10-26

**Available source audit finished. Required Linux/full, native, artifact and
physical acceptance remains BLOCKED/INCOMPLETE.** Two P3 helper cleanup findings
are corrected. No release qualification is claimed.

Owned checkout: `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`, branch `codex/wipe-audit-20261024`, HEAD/base
`9764d93ac21273aa79ae4618629b0a30e3eda271` plus pre-existing dirty work. This pass changed only
`src/beamo_wipe/diagnostics.py`, `src/beamo_wipe/sound.py` and the new portable
`developer_tests/test_optional_helper_cleanup.py`. Final **936 functional inputs**:
`682501409de92473b4cdb44505358a4dda83a24514b75bb4fd0eec5b7e8d77f7`. Exact source delta and AST preservation are retained in raw
helper-implementation.json and helper-cleanup.diff.

Raw evidence: `C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261026-r10`. [verification.json](verification.json) binds
source, checks, canonical files and sealed bytes. [reviews.json](reviews.json)
retains all four terminal reviews and parent validations. R9's sealed evidence
and canonical records were rechecked; historical backlog bytes remain intact.

## Corrections and causal evidence

Diagnostics directory, log and serial descriptors could be acquired outside their
cleanup protection. Cleanup errors could also replace primary interruptions,
which optional reader/logger/serial fallbacks then swallowed. Acquisitions now
occur inside protected scopes; owned descriptors are consumed before a single
close attempt; every remaining close is attempted; primary exception identity is
preserved. Cleanup-only errors still prevent success. Metadata, sanitization,
bounded read/write/rotation and marker policies retain their original main bodies.
Failed native close may release or retain a descriptor; the fakes do not settle it.

The sound helper could leave a rejected reaper's admission flag set after a
mutation-then-exception during acceptance. It now clears the flag before caller
cleanup and opening the decision gate. The entire sound AST is otherwise equal.
Queued fake reapers confirm obsolete callbacks remain inert. Real scheduling,
native teardown and arbitrary opcode interruption are not qualified.

The same assertions against saved originals produce 19 failures and four errors;
the errors are close OSError replacing expected KeyboardInterrupt/SystemExit.
These are retained causal defect evidence. Corrected source passes **13 portable
pytest nodes plus 29 subtests**, zero failures/errors/skips. Direct unittest also
passes 13. The expected-red driver exits 0 because original failure was required.
No assertions were weakened. All OS/process/event/import effects are fake.

## Independent reviews and checks

- Runtime/UI lifecycle: 49 matching observations across 22 cases, 64 unique exact
  current AST nodes and 21 unchanged scoped inputs. Bounded no objection.
- Artifact metadata/identity verification: 74 matching observations, 87 unique
  exact AST nodes and 23 unchanged scoped inputs. Crypto is synthetic; no built
  artifact or release is qualified. Bounded no objection.
- Report truth/privacy composition: 29 matching observations, 550 exact AST
  bindings and 22 unchanged scoped inputs. Real classifiers, evidence, sharing,
  renderers and recovery compose over memory boundaries. Only v7 counts; five
  failed adapters and superseded v6 remain retained. Bounded no objection.
- Fresh helper correction review: 114 matching before/after/control observations;
  independent exact test-class replay reproduces the same original failures and
  current 13 nodes/29 subtests. Bounded no objection. Counts include expected old
  defects and are not 114 passing product tests.

Root read drivers, guards and independent oracles, rechecked complete serialized
observations, exact current source/AST and every packet byte. No remaining concrete
scoped objection was established. This is not universal input, concurrency,
descriptor, process, native or full-source execution proof.

Fresh four Ruff gates, static types across 52 files and 747 syntax parses pass.
Windows mypy uses Linux/Python3.11 stubs and retains five existing annotation-
unchecked notes. Whole current source bytes match the successful receipts.
Historical portable/kiosk and R9 identity checks retain only their exact unchanged
scoped inputs; old whole-source static receipts are superseded. No broad suite,
unexpected skip, timeout, pending gate or model is represented as acceptance.
All root/reviewer setup failures, corrections, source/context drift and superseded
attempts remain retained with their actual exits.

## Preparation and remaining acceptance

Lab doctor, sync, Wipe plan and report exited 0; all four actual runs verified
VALID at unchanged Lab revision `d3d0959bb26b17531464dbd1ba233d4d842ad581`. These are preparation only.
Offline report DOM/text and no external resource loads were inspected. Visual
verification remains BLOCKED: two preview screenshot timeouts; fallback browser
unavailable. No product adapter or unchanged Lab selftest was rerun.

Entry disk free space was 1,325,404,160 bytes; closure
observed 1,618,214,912 bytes. The unchanged 8 GiB disk
and 1 GiB RAM floors remain in force; capacity fluctuations have no established
cause. No admission retry, WSL operation, cleanup or lowered floor occurred.
Full main/Orca containment remains unimplemented/unqualified: controlled reaping
PID-init/lifelines/private proc, service-socket/Windows-interop exclusion,
aggregate resource limits, bounded writable/log transport and ten finite selftests
remain prerequisites.

Actual Linux suite/module integration, native descriptor and process behavior,
kiosk shell/isolated Debian import/proc executable identity, GTK/audio, Go/native
platforms, artifacts and separately authorized final public ISO/QEMU/hosted gates
remain incomplete. Full local acceptance is still required before release.

Physical Task119 remains **NOT TESTED/BLOCKED** until an explicit new physical
session supplies the spare machine, disconnected valuable disks, authenticated
cold media reconnect/readback, independent recovery/evidence channel and complete
firmware trust/revocation/SBAT/enforcement prerequisites. Boot alone cannot qualify
it. Windows session, security, network and connected USBs/disks were preserved.

Index is empty; whitespace check passes. No staging, commit, push, PR, release,
hosted CI/spend, guest/mount/real engine, media/device operation, firmware/security,
host power/network/service change or peer edit occurred.
