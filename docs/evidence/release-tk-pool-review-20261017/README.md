# PR90 Tk retirement race and CodeQL review

2026-10-17–18 / Codex, BeamoTech/beamo-wipe, fix/safety-audit-20261015.
Parent commit: 4f7ee8d434497f52b58966792ed6cc28b587635e.
This is local candidate evidence. Protected merge, exact-main hosted CI and
production publication remain pending; no physical hardware was tested.

Greptile's [summary](https://github.com/BeamoTech/beamo-wipe/pull/90#issuecomment-6243204273)
and [P1](https://github.com/BeamoTech/beamo-wipe/pull/90#discussion_r4304997909)
identify the same confirmed race in both native retirement pools. A foreign
collector snapshot retains record tuples without incrementing the native
resource's direct refcount. The creator can remove the shared pool entry,
leaving the foreign snapshot to release the final tuple on the wrong thread.

Records are now partitioned by their creating Thread before any snapshot is
taken. Empty metadata buckets remain to protect an in-progress pin from a
reentrant GC drain. Resource refcount checks, original destructors and creator
ownership remain. Only four helpers changed; the wizard class AST and every
other top-level definition are unchanged. Disk discovery, authorization and
nwipe command construction are unchanged.

The first full local run returned zero but was rejected for one material
unraisable GC warning: empty metadata buckets let unrelated thread teardown
call current_thread and construct DummyThread while the audio fixture had
replaced Thread.__init__. Its10137 main passes, one Orca pass,14 skips and
warning remain in initial-unqualified-local-gates/. Two raw-thread regressions
reproduce the same KeyError before correction. Actual Tk owners now tag their
creating thread using thread-local metadata during pinning. Drains read that
tag without creating thread wrappers for unrelated GC callers. Actual Thread
identity still selects each pool, without relying on reusable OS thread IDs.

| Verification | Observed result |
| --- | --- |
| Original deterministic regression v2 | 8 failures, 2 external-owner controls passed |
| Final test bytes replayed against archived original sources | Same8 ownership and2 callback failures;2 controls passed |
| Fixed deterministic regression | 10 passed |
| Unregistered-thread reproduction | 2 failures before correction |
| Final focused native/audio run | 87 passed with unraisable warnings fatal;65 native child results zero exit/empty stderr |
| Fresh full local gate | All9 phases passed; 10140 combined Python/Orca passes |
| Local artifact skips | 14 exact existing artifact-dependent skips; retained as skips |
| New and prior audit modules | 60 modules/3937 cases passed |
| Full-gate native children | 65 zero exits/empty stderr/no parent timeout; 37 direct source hashes |

The new native child invokes actual worker GC and original Font, Variable and
Image destructors on an isolated72DPI display, with application side effects
forbidden. It checks every native wrapper settles on its creating thread.
The original v1 reproduction inadvertently paused the empty asset pool before
the interpreter pool: four failures and six passes. Its output/test remain;
v2 corrects that fixture before product code changed. The final13-case module
adds the real-native child and two raw-thread cases after the original10-case
reproduction. The clean full gate is a fresh second run on a separate freeze;
the first run's warning is never counted as a successful qualification.

Runtime SHA-256: d8f527df821941d73332ae365b98f45ac289848bd9e535838e006c958e14e08a.
Tk source SHA-256: f43af23bfb37ca184a3a85c316c5f6235c528a102fd4a98493f9df9452db740b.
Frozen876-input source map: fd1496381d10cd93169f56b276260d8aa5cbe7badf3976f18f4e7d2a8e3891a5.
No source changed during the full gate. The Windows test binary is indexed to
its identical archived bytes; the current compile ran independently. This is
a crossbuild, with native Windows and hosted ISO/QEMU qualification required
for the new commit before release.

Four CodeQL URL findings (32–35) concern archived audit scripts checking for
visible support text in complete HTML reports. Every script matches committed
bytes;280 bundle files authenticate and16 failed reports parse with support
text and zero URL attributes. No URL validation/request/redirect/authorization
sink exists. All four alerts were dismissed as false positives with individual
rationale. GitHub CodeQL was then green on4f7ee8d. CodeQL configuration and
all historical archives remain unchanged. Focused23 report/support cases pass
at72DPI. An initial no-display22-pass/one-Tk-skip attempt is retained separately.
The initial long-comment API dismissal request exited1 (stderr not retained);
the concise request succeeded. No hosted retry or product change addressed
these false positives. This evidence does not pre-claim new-commit CodeQL.

Current local verification does not attribute historical native aborts,
SIGTERM, timing or loop incidents, or replace physical/firmware acceptance.
The receipt archive preserves failures, skips, source snapshots and commands;
SHA256SUMS authenticates retained files independently of Git text conversion.
