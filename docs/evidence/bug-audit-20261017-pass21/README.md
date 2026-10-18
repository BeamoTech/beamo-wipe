# Beamo Wipe bug audit — pass 21

2026-10-17 / Codex. **Local checks pass; overall qualification remains blocked
by the historical and platform checks below.** Source is local and uncommitted.
Nothing was pushed or published.

BeamoTech/beamo-wipe, branch `fix/safety-audit-20261015`, worktree
`/root/dev/Beamo Wipe`, HEAD `35107a8d1a701093eac876a58ab4efd50e291673` plus the
preserved dirty snapshot. All 779 starting inputs match pass20 final. Final
788 inputs contain 775 unchanged starting inputs, four changed runtime files
and nine new canonical regression modules (219 cases). Runtime SHA-256:
`8e18e259414408eff434768ad24b38432bf913b12a864439f40b585a264496c1`.
Source-freeze SHA-256:
`c4ecdfc8e8c814bd3d033bd478472cbd498a766c76e077006ba2bfb093093dac`.

The proved fixes cover seven failure areas:

- Whole-disk records with missing or lexically noncanonical kernel NAME could
  lose their flat PKNAME partition evidence. They now refuse target creation;
  physical observations and contradictory or excluded alias evidence remain.
- Direct nonfinite float size conversion now raises the parser's ValueError
  category. Public discovery already caught OverflowError; this fix does not
  claim that public discovery previously exposed infinity as a target.
- Unicode line and paragraph separators could split an accepted JSONL
  diagnostic event at readback. The existing field sanitizer now replaces
  those separators alongside Unicode control characters.
- All wizard-created Tk variables bind explicitly to the wizard's interpreter,
  including when another root exists or Tk's default-root support is disabled.
- Exact owned Tcl trace commands are adopted before trace_add can return an
  interruption. A temporary instance-local registration hook restores the
  previous attribute and preserves independent peer traces and replacements.
- Tk and GTK refresh Event construction/set interruptions settle the refresh
  claim. The worker and UI share the acceptance lock, preventing a worker
  already awakened by a failed set from scanning after rejection. Controlled
  actual waiting-thread interleavings also prove a fresh retry resets gates.
- GTK close attempts every independent cleanup after an earlier failure and
  rethrows the original first exception, with secondary failures noted.

The nwipe engine, method mapping, owner/token/countdown requirements, completion
validation, boot/build/CI/publication controls, claims and pins are unchanged
from the starting snapshot. Native destructors, exception frames, peer traces
and product GC modes/thresholds are preserved. The complete incremental and
cumulative diffs and both source archives are retained. Three bounded source-only
reviewers independently reviewed the changed areas; the final 13-input review
also authenticates all 788 source/archive inputs.

| Verification | Observed result |
| --- | --- |
| Starting core baseline | 228 passed |
| Exact final regressions on 58 authenticated original source inputs | 219 cases: 89 failures and 130 passing controls; zero errors/skips |
| First focused fixes | 338 passed |
| Final corrected focused run | 290 passed, including all 219 new cases, six actual-thread cases and adjacent native/refresh behavior |
| First eight fresh local phases | Lint/types, preview, negative safety, Go 1.26.8 version/race/vet/350,000 fuzz iterations and actual Windows crossbuild passed |
| Full Python main gate | 10,126 passed; 14 artifact-dependent skips; zero failures/errors in 1,147.50s |
| Separate clean Orca gate | 1 passed in 58.60s; zero failures/errors/skips |
| Final combined report readback | 10,127 passed; 14 exact prior artifact skip IDs; no failures/errors/duplicates. All 59 retained audit modules/3,924 cases ran and passed |
| Canonical native child readback | 64 zero exits, empty stderr, no parent timeout or reported finalizer errors; 36 emit direct source/hash provenance and 28 inherit the admitted canonical environment |
| Final native ownership/pressure campaigns | 10 sessions, 220 original finalizers returned on creator thread, one GC callback, max depth 1, pools empty; 12×128 actual Fonts released with zero errors or remaining wrappers. Fixture-only GC settings restored |
| Fresh runner/evidence artifacts | 153 short and 153 actual >1MiB log cases; 90 authenticated sidecar roundtrips, 54 advisory traces; 621 fixture files hashed, archived and read back |
| Fresh cancellation/retry | 144 cases; 288 regular-file fixtures; uncertain state retains ownership until confirmed terminal |
| Fresh geometry | 270 Tk/GTK views, 27 critical Tk focus views fully visible; no callback errors/effects. Root viewed and hashed five PNGs |
| Fresh GTK owner follow-up | Nine language/text-size combinations reveal the checkbox fully after three actual Tab traversal steps; authorization unchanged |
| Fresh reports | 90 variants; five complete bundles/70 files; manifests, owner/sharing outcomes and archive readback pass |
| Retention/readback | Status and counts are recorded in primary/retention-verification.json; SHA256SUMS authenticates the retained files |

The fresh full gate runs on Python 3.12.3 with fake devices and private X11 at
72 DPI. No test observer/plugin is injected. Crossbuilding a Windows executable
is distinct from native Windows acceptance. The 14 artifact skips match the
exact authenticated prior IDs: two live-build
generated-config checks and 12 manufacturing-ISO-dependent checks. Their
individual reasons are in gate-verification.json. They remain skips. The actual
9,021,440-byte PE32+ AMD64 crossbuild is retained, distinct from native Windows
acceptance. Bounded native pressure observations do not prove every possible
GC phase or explain historical aborts.

Proof history remains explicit. The first trace proof used an invalid Boolean
row-fixture value and is INVALID; its corrected version supplies three original
failures and one control. Strict finalizer observers set their return marker
only after the original destructor returns; preceding versions are retained.
The first final-focused selection named a nonexistent test file and exited 4
without running tests; the corrected selection passed 290. The exact final
219-case replay combines the corrected proofs and synchronized actual-thread
module, giving 89 failures and 130 passing controls. Original failures and passing controls are
never relabeled. Preparation retains a prose-only checksum typo and its
single-character correction; the machine-readable review checksum was correct.
Two copied campaign docstrings were corrected from Pass20 to Pass21 before
execution, preserving the first preparation receipt separately.

Detailed receipts:
[source/archive verification](primary/source-artifact-verification.json),
[gate verification](primary/gate-verification.json),
[native readback](primary/native-final-readback.json),
[campaign verification](primary/campaign-verification.json),
[capture review](primary/primary-capture-review.json),
[independent source review](runner/final-source-review.md),
[UI review](ui/FINAL-UI-SOURCE-REVIEW.md), and
[independent final evidence review](runner/final-verification-review.md).

The unchanged lint output matches pass20 byte for byte: five existing mypy
annotation-unchecked notes and the reviewed TODO-regex false positive are
recorded in the warning review; none is a new material warning.

Pass19's two uncanceled native aborts remain unattributed. Current fixes and
passing current full checks do not identify their original creator or cause.
Pass18's original GTK latency trace, pass16's loop incident, pass8's SIGTERM
attribution and pass9's original timing trace retain their recorded limits in
prior audit records. No current passing result supplies missing incident data.

Python 3.11/live-bookworm, ISO/QEMU, native Windows, firmware, physical
reconnect/readback and hardware qualification are **NOT RUN / BLOCKED**. No
physical disk, guest, privileged acceptance, host setting, hosted CI, network
login or publication was used. Historical evidence reconciliation and the
prescribed separately authorized isolated platform checks remain necessary.
Commit/push is pending those requirements; a discovery commit needs `safety:`.
Publication requires separate authorization. The canonical unfinished-work
record retains the exact next actions and acceptance criteria.
