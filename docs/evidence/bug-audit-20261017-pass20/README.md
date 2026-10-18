# Beamo Wipe bug audit — pass 20

2026-10-17 / Codex. **Local verification passes; overall qualification remains
blocked by the historical and platform checks below.** Source is local and
uncommitted. Nothing was pushed or published.

BeamoTech/beamo-wipe, branch `fix/safety-audit-20261015`, checkout
`/root/dev/Beamo Wipe`, HEAD `35107a8d1a701093eac876a58ab4efd50e291673` plus the
preserved dirty snapshot. Starting 771 inputs match pass19 exactly. Final 779
inputs comprise 768 unchanged starting inputs, three changed runtime files and
eight new canonical test modules. Runtime SHA-256:
`c3a9b4c2145e86203eb7669e5073b0fb7de0a932eb2920b5b881c58fba6af2aa`.
Source-freeze SHA-256:
`bc83136ee6bd52c8ef4c80206c9b80b958845f839546eb57d8d518263d59ca04`.

The fixes close three proved failure areas:

- Discovery normalizes holder TYPE whitespace and treats a mounted generic
  `dm` holder with unresolved membership as unsafe. Unknown ancestry refuses
  targets. Physical eligibility and the existing boot exclusion remain intact.
- Audio launch construction, start and acceptance interruptions revoke launch
  permission, clear the selected pending queue and settle the ticket. A worker
  that was spawned before rejection cannot execute queued work.
- Tk owns native resources across successful and partial construction, later
  widget-adoption failure, startup, normal exit and propagated exceptions.
  Teardown removes exact owned traces/callbacks and releases the owned graph;
  identity-indexed pools defer final native release to the creating thread.
  An owner-only GC-stop drain preserves ordinary collectibility. Original
  native destructors, peer traces and exception identity remain intact. Image
  pre-initialization establishes only the absent no-handle `name=None` state.
  Closed navigation callbacks refuse work; lightweight stale-callback behavior
  is preserved.

The engine, methods, owner/token/countdown authorization, completion evidence,
recovery, power and export runtime modules are unchanged from the starting
snapshot. The complete incremental and cumulative diffs, all source archives,
and exact hashes are retained. Independent reviews cover all 11 selected
runtime/test inputs and authenticate the full 779-input archive.

| Completed verification | Observed result |
| --- | --- |
| Exact final regressions replayed on all 58 authenticated original source inputs | 149 cases: 88 failures, 61 passing controls; zero errors/skips. Failures include 86 AssertionError and two controlled RuntimeError cases. Shared source was never restored. |
| Final localized audio/discovery suite | 663 passed |
| Final Tk constructor/ownership, busy and existing collection checks | 106 passed |
| Fresh full Python gate | 9,907 passed; 14 artifact skips; zero failures/errors |
| Separate clean Orca gate | 1 passed, zero skips/failures/errors |
| Combined report readback | 9,908 passed; no duplicate cases; all 50 retained audit modules/3,705 cases ran and passed |
| Other fresh local phases | Lint/types, preview, negative safety gate, pinned Go1.26.8 version/race/vet/350,000 fuzz iterations and actual Windows crossbuild passed |
| Full-report native child readback | All 53 exited zero, no parent timeout, empty stderr; no nonempty unraisables. 25 children emit direct source/hash provenance; the other 28 inherit the admitted canonical environment. |
| Final-source repeated Tk sessions | 10 sessions; 220 original finalizers returned on their creating thread; one registered GC callback, maximum GC depth1, pools empty, no effects/unraisables |
| Final-source native pressure | 12×128 actual Fonts released; zero errors/remaining wrappers. GC observed at getrefcount, no snapshot mutation reproduced. Only fixture GC settings changed. |
| Fresh runner/evidence artifacts | 153 short and 153 actual >1MiB log cases; 90 evidence roundtrips/sidecar pairs, 54 advisory traces; all 621 fixture files hashed and archived/read back |
| Fresh cancellation | 144 cases, including uncertainty/retry; 288 regular-file fixtures authenticated |
| Fresh geometry | 270 Tk/GTK views; 27 critical Tk focus views fully visible; zero callback errors/effects. Root viewed all five PNGs. |
| GTK owner capture follow-up | All nine language/text-size combinations reach the ownership checkbox after three native Tab traversal steps and reveal it fully; authorization unchanged |
| Fresh reports | 90 variants; five complete bundles/70 files, manifest/readback and owner/share outcome checks passed |

The 14 skips are the same exact IDs as the earlier authenticated gate: two
live-build-generated configuration checks and 12 manufacturing-ISO-dependent
manifest checks. Their reasons are recorded individually in
[gate verification](primary/gate-verification.json). They are not passes.
The actual 9,021,440-byte PE32+ AMD64 crossbuild is retained in the raw archive;
it is not native Windows acceptance.

Failed and invalid experiments remain distinct. Candidate1 exposed native
wrong-thread deletion. Candidate3's first broad private attempt imported shared
parent source because pytest overrode PYTHONPATH; it is invalid acceptance.
Corrected provenance, constructor boundary, identity-comparison and ordinary
collectibility proofs led to candidates4–6. Candidate7's full gate produced
9,901 passes, one stale-callback compatibility failure and 14 artifact skips.
Both final-gate failures and their exact source snapshots/logs remain under
`primary/failed-gate-1` and `primary/failed-gate-2`; large raw streams are indexed
in `primary/raw-evidence-sha256.json`. None is relabeled as a pass.

The post-gate evidence helper initially rejected two newly exclusively created
empty logs because their kernel mtime preceded the wall-clock start by less than
one millisecond. A separate 50-file probe reproduced this 50 times. The helper
now bounds only the two known silent phases between the preceding completed
phase and their own completion; the runner's exclusive creation and exact source
receipts remain required. Product source, tests, gate logs and statuses were
unchanged. Original helper, observations and correction are retained. The
inherited lint TODO warning is a reviewed false positive from the unchanged
placeholder-detection regular expression; its exact source trace is retained.

[Source and archive readback](primary/source-artifact-verification.json),
[native results](primary/native-final-readback.json),
[fresh artifact readback](primary/campaign-verification.json),
[capture review](primary/primary-capture-review.json),
[independent source review](runner-boot/final-candidate8-review.md), and
[independent final evidence review](runner-boot/final-verification-review.md)
provide the detailed receipts. `SHA256SUMS` authenticates retained files; the
retention receipt documents raw archive readback and the unchanged index.

Pass19's original two uncanceled aborts remain unattributed. The isolated native
ownership failures are now fixed and the current full gate passes; those facts
do not identify the original aborting object's creator. Pass18's original GTK
latency trace, pass16's loop incident, pass8's unexplained SIGTERM and pass9's
original timing trace retain their recorded limits. Their original histories
are preserved in the preceding audit directories.

Python3.11/live-bookworm execution, ISO/QEMU, native Windows, firmware, physical
reconnect/readback and real hardware qualification are **NOT RUN / BLOCKED**.
Current execution is Python3.12.3 with fake devices on private X11 at72DPI.
No guest, physical-device or privileged acceptance was substituted. Before
qualification, follow the unfinished record to reconcile historical evidence
and run prescribed checks on separately authorized isolated workers/platforms.
Commit/push remains pending those requirements; a discovery commit requires
`safety:`. Publication requires its separate authorization.
