# Comprehensive audit pass 8 — 2026-10-26

**Available source review is finished. Required Linux/full, native, artifact and
physical acceptance remains BLOCKED/INCOMPLETE.** No concrete new actionable
product defect was established in this bounded pass. No product or test files
were changed. This finding does not qualify the source for publication.

The current source is `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`,
branch `codex/wipe-audit-20261024`, HEAD/base `9764d93ac21273aa79ae4618629b0a30e3eda271` plus pre-existing dirty
changes. All **934 functional inputs** remain byte-identical to final pass 7:
`25ff560c06cbba0ce405603e71a735af452c13a0afb81f77d23ecdf5a191dc9e`. Documentation and backlog are bound separately.
The prior 662-member packet was fully read back at entry and closure; its seal
and historical bytes remain unchanged. Its source overlay remains authenticated
by that packet. No old receipt was overwritten or presented as a new run.

Raw evidence: `C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261026-r8`.
[verification.json](verification.json) binds source, checks, canonical files and
the sealed raw packet. [reviews.json](reviews.json) retains all three terminal
reviews and parent validations. [Pass 7](../bug-audit-20261025-pass7/README.md)
records its actual fixes and limitations; they are preserved rather than
reclaimed as new work in this pass.

## Review results

| Fresh review | Bounded observations | Disposition |
| --- | --- | --- |
| Completion | 463 | No new concrete finding |
| Lifecycle | 94 | No new concrete finding |
| Build | 54 | No new concrete finding |

Parent read the reports, inspected relevant source/oracle contracts and checked
scoped current hashes and complete packet bytes independently. Reviewer model
observations are not pytest passes. The review packets retain setup failures,
withdrawn or unproved candidates, actual exits and scope-specific limits.

Parent caught an evidence-recorder defect in the lifecycle packet: three stored
mutable-list values changed after their instantaneous equality checks. The sealed
original packet and failed parent comparison remain intact. A separate parent
replay changes only retention of actual/expected values to deep copies; all
production AST and case oracles remain identical. All 94 replayed observations
have matching stored values. This corroborates the lifecycle result without
adding overlapping counts or claiming a product fix.

The completion review excludes earlier otherwise successful runs whose path
fake called native realpath metadata APIs. Its final three batches use lexical
paths plus guarded OS metadata/read/write functions and have no denied events.
Parent independently checked all 463 stored actual/expected values, 560 exact
AST bindings and nine full decompressed original receipts. The superseded runs,
initial errors and original bytes are retained, not treated as final evidence.

Parent additionally exercised **66 exact-AST/fake safety controls**: 19 discovery,
8 final rediscovery, 33 argument validation and 6 executable-process proof cases.
The controls cover raw target/boot ancestry, mounts/read-only/remote/alias
refusal, changed identity, unsafe or mismatched arguments, same inode/deleted
executables, permission uncertainty and disappearing processes. Kernel transport,
log-filesystem and inventory presentation are explicit fake boundaries.

Another **55 confirmation observations across 11 declared families** matched
hand-declared token/refusal outcomes under peer-order permutations. Serial
suffix collisions, full identifiers, WWN fallback, kernel-name/path-like serials,
missing IDs, differing capacities and cross-disk token conflicts are covered.
Prompt text is mocked. No universal input, physical identity, actual UI or native
execution proof follows from these finite controls.

Supplemental source inspection covered the safety eligibility/snapshot and
parse_lsblk_json refusal paths, raw ancestry/NVMe corrections, pinned process
inspection, argv construction/validation, complete runner start, and launcher
request authorization, strict decoding, busy/closed/revision checks, consumed
readiness and boot-option parsing. No additional concrete defect was established.
This is source review, not native Go, shell, firmware, or race-free topology proof.

## Verification scope

- Fresh parsing succeeded for **745 functional Python files**; no product modules
  were imported by that syntax check. Parent safety and confirmation probes used
  inert OS/process observations and refused external process/network operations.
- Prior **254 portable tests + 37 subtests**, **2 kiosk tests + 10 subtests**,
  four Ruff commands and static types across 52 source files were rebound to
  unchanged exact inputs/configuration. They were **not rerun** in pass 8.
  Retained interpreter/Ruff bytes and probe dependencies match where receipted.
  This does not requalify current dependency installations or Linux/native
  runtime behavior. Windows mypy used Linux/Python 3.11 stubs; its five existing
  annotation-unchecked notes and configured analysis limits remain.
- Fresh source/index/guide/peer checks match, `git diff --check` passes, and the
  index is empty. No staging, commit, push, PR, hosted CI, spend or publication
  occurred. Existing dirty source and other-agent work are preserved.
- Fresh Lab doctor, sync, Wipe plan and offline report exited 0; all four printed
  runs verified integrity VALID. They remain **preparation only** at unchanged
  Lab commit `d3d0959bb26b17531464dbd1ba233d4d842ad581`. Header/outcomes were visually inspected in an
  owned blank incognito browser tab without a host server or network resources.
  Direct file navigation was unsupported; the retained error and the subsequent
  owned-tab rendering are recorded. No product/native UI acceptance is claimed.

One parent probe setup attempt failed because its evaluated type alias lacked
the stdlib typing namespace. The original driver and nonzero exit are retained;
the corrected adapter preserved selected production AST and case oracles. An
initial read-only search quoting failure and a receipt-inspection shape error
are also retained. None supplies product observations. The lifecycle recorder
objection and corrected replay are described above. Unsuccessful reviewer adapters stay explicit in their own
reports. Prior failed/timed-out/canceled/skipped/incomplete gates remain incomplete.

## Remaining work and blockers

Entry free disk space was **1,762,316,288 bytes**; closure
observed **1,436,913,664 bytes**, below the unchanged
8 GiB admission floor. Capacity loss cause remains unknown. No WSL/guest/full-gate
admission retry, cleanup, peer/cache deletion or lower threshold occurred.

Full main/Orca test containment remains unimplemented/unqualified: positively
controlled reaping PID-init, lifelines/private proc, service-socket and Windows
interop exclusion, aggregate resource limits, bounded writable/log transport and
the ten finite selftests remain required. Adequate capacity and current worker/
peer admission are prerequisites for the reviewed final-identity gate chain.

The actual Linux suite, 30 new startup regressions, 11 kiosk shell cases, actual
Debian isolated import, descriptor/proc/pgrep/kiosk integration, GTK/audio,
Go/startup/platform/artifact gates and separately authorized final public
ISO/QEMU/hosted verification remain unrun or pending. Existing old fixture and
native-test gaps remain on the backlog; bounded source models cannot replace
those gates. No release qualification is claimed.

Physical Task 119 cold reconnect/readback, dedicated spare machine with valuable
disks disconnected, firmware boot and trust/revocation/SBAT/enforcement cases
remain **NOT TESTED/BLOCKED** until an explicit owner physical-session update and
all original recovery/evidence prerequisites exist. A successful boot alone is
insufficient. No host power, real engine, device/media, firmware, security,
network, service, guest or other physical operation occurred.

The canonical unfinished-work record retains exact next actions and all R7-and-
earlier bytes. Required verification and publication authority remain outstanding.
