# Comprehensive audit pass 9 — 2026-10-26

**Available source audit finished. Linux/full, native, artifact and physical
acceptance remains BLOCKED/INCOMPLETE.** Two related P3 cleanup defects were
corrected in `build_identity.py`. No release qualification is claimed.

The owned checkout is `C:/Users/Jack/beamo-release-work/20261024-wipe-audit-pass2`, branch `codex/wipe-audit-20261024`, HEAD/base
`9764d93ac21273aa79ae4618629b0a30e3eda271` plus pre-existing dirty changes. This pass changed only
`src/beamo_wipe/build_identity.py` and the new portable regression
`developer_tests/test_build_identity_cleanup.py`. Final **935 functional inputs**:
`4f3ddeaf0f57af82174537992d635c022b8f273e09e65c7ca705d25b2f0da7fc`. The exact two-path delta from entry934 is retained
in raw `identity-implementation.json` and `identity-cleanup.diff`.

Raw evidence: `C:/Users/Jack/beamo-release-evidence/wipe-comprehensive-repass-20261026-r9`. [verification.json](verification.json) binds the
source, checks, canonical files and sealed raw bytes. [reviews.json](reviews.json)
preserves all four terminal reviews and parent validations. The sealed pass8
packet was fully reread at entry and closure; historical packet and backlog bytes
remain unchanged.

## Correction

Directory handoff could retry a descriptor after its close reported failure and
leave the successor unclosed. Acquisition and token setup also preceded cleanup
protection. Separately, close failures could replace the original read/write
failure or interruption; identity-reader fallback then swallowed cancellation.

Owned descriptors are now registered inside protected scopes, consumed before a
single close attempt, and every remaining close is attempted. Cleanup preserves
the primary exception; a cleanup-only failure still refuses success. Failed
publication stages remain retained. Publication metadata/readback checks, identity
framing, classification, schema and all other function/non-function AST remain
unchanged. Native close-error descriptor state is not inferred from the fakes.

The same regression assertions against retained original definitions produced
15 failures and four errors. The errors show close OSError replacing expected
KeyboardInterrupt/SystemExit. The red driver mistakenly required zero errors and
returned1; that original receipt is retained. Corrected source passes **11 portable
pytest nodes +21 subtests**, with zero failures/errors/skips. Direct unittest also
passes all11 nodes. These execute exact AST with inert OS/import/token boundaries,
and do not qualify real Linux syscalls or actual product-module integration.

## Independent review and source drift

- Safety/discovery:37 guarded fake observations,81 current scoped inputs and309
  exact AST bindings; bounded no objection. Root checked source/oracles/guards,
  stored values and all packet bytes independently.
- Export/persistence/privacy:50 observations,18 current scoped inputs and346
  AST bindings; scoped no objection. Build identity is an explicit fake dependency
  in this packet; its closing whole-entry equality correctly failed on root edits.
- Startup/launcher:21 matching original-source observations,15 selected nodes and
  15 textual contracts. The original review remains INCOMPLETE/SOURCE DRIFT because
  two identity readers changed. Its failed closing equality was never upgraded to
  PASS. Root separately replayed the same21 cases against current source with the
  new helper selected:21/21,16 exact current bindings and no denied native events.
  Repeated cases are not added as21 new independent observations.
- Fresh identity correction review: **Bounded no objection to correction; current startup readers reconciled**. Its scope, counts,
  original reproductions, independent current controls, hashes and limitations
  are preserved in parent-identity-review-validation.json and reviews.json. Root
  independently checked the final packet and source. No concrete scoped objection
  remains; this is bounded source/model review, not native acceptance.

Root also completed169 language/confirmation fake observations and1790 literal
template pairs, plus684 support-code composition observations across99 refusal
pairs in English/French/German. Their executed inputs remain current. The changed
identity file participated only in a static language scan; that changed scan was
rechecked separately. These do not establish native text input, rendering, audio,
translation semantics, physical identity authenticity or universal input behavior.

## Checks and evidence limits

Fresh four Ruff gates, static types across52 source files and746 Python syntax
parses pass. Windows mypy used Linux/Python3.11 stubs and retains the five existing
annotation-unchecked notes at the same configured scope. No product module was
imported by syntax/static checks. Historical portable254+37 and kiosk2+10 results
remain bound to their exact unchanged scoped inputs and were not rerun. Old
whole-source Ruff/type receipts were superseded by fresh checks after the edit.

Fresh Lab doctor, sync, Wipe plan and offline report each exited0 and verified
integrity VALID at unchanged Lab revision `d3d0959bb26b17531464dbd1ba233d4d842ad581`. They are preparation
only; no product adapter, native UI or physical acceptance was performed.

Every failed/superseded reviewer adapter and source-drift receipt is retained.
Root additionally retained a quoting failure, guessed missing read paths, two
parent-validator schema/path mistakes and a JUnit node/subtest counting mistake.
Corrected adapters preserve case assertions and product AST. No failure, timeout,
unexpected skip or unavailable gate is relabeled as a pass.

Index is empty and `git diff --check` passes. No staging, commit, push, PR, hosted
CI/spend, publication, host power, guest, real engine, physical disk/media,
firmware/security, network/service or peer edit occurred.

## Remaining acceptance

Entry disk free space was 1,955,225,600 bytes; closure
observed 1,548,914,688 bytes. The unchanged8GiB floor
and current worker/peer admission remain required. Capacity fluctuations are not
attributed to a known cause. No WSL/admission retry, cleanup or floor reduction
occurred. Full main/Orca containment remains unimplemented/unqualified: controlled
reaping PID-init/lifelines/private proc, service-socket and Windows-interop
exclusion, aggregate resource bounds, bounded writable/log transport and ten
finite selftests remain prerequisites.

Actual Linux suite, module/native syscall and descriptor integration, kiosk shell
and isolated Debian import, proc/pgrep executable identity, GTK/audio, Go/native
platform, artifact and separately authorized final public ISO/QEMU/hosted gates
remain incomplete. The original pending regressions and platform gaps remain
pending; this audit does not substitute fake models for them.

Physical Task119 remains **NOT TESTED/BLOCKED** until a new explicit owner physical
session and all original prerequisites exist: spare machine, valuable disks
disconnected, authenticated media with cold reconnect/readback, independent
recovery/evidence, and firmware trust/revocation/SBAT/enforcement evidence.
A successful boot alone cannot qualify it. Publication remains unqualified.
