# Pass18 Beamo Wipe audit — blocked at the local gate

2026-10-17 / Codex. Three proved product defects fixed locally; the full
verification gate failed one existing GTK responsiveness assertion. This
candidate is not accepted. The user's stop-on-blocker instruction holds the
remaining acceptance campaigns. No commit, push, hosted job or release.

## Source and scope

- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD
  `35107a8d1a701093eac876a58ab4efd50e291673`.
- Starting 762 source/test/build inputs exactly match pass17's final freeze.
  Final 766 inputs change three runtime files and add four regression modules.
  All other 759 starting inputs and all prior dirty work remain unchanged.
  No tracked test changed. Index remains empty.
- Runtime SHA256:
  `bebdb2425c6135dc79ad9dd37c89d4995173a8ffc8183edb4515cb1c726f89b7`.
- Three bounded delegated source audits covered discovery/safety,
  runner/progress/cancellation/evidence/recovery, and UI/boot/build. The primary
  independently reviewed each proposed fix, the failing evidence and all seven
  changed/new inputs. The runner peer cross-reviewed their exact final hashes.
- Methods, engine flags, claims, pins and build/publication automation did not
  change. Discovery/authorization changes require an eventual `safety:` commit.

## Proved product fixes

1. **Discovery discarded pathless hardware alias bridges.** A physical
   observation with no usable path could connect a boot or mounted disk's
   serial to another disk's WWN. Discarding it made the alias selectable.
   Malformed/conflicting candidates could also lose relevant uncertainty.
   Discovery now retains only these rows' hardware facts as safety evidence;
   they never become targets or confirmation peers. Empty paths do not establish
   same-device identity, and unrelated malformed rows retain existing behavior.
2. **Curses could accept Enter against a footer that still said to wait.** A
   slow terminal refresh could consume the remaining countdown between painting
   the disabled action and handling a queued key. Acceptance now also requires
   that the displayed frame had an enabled action. The shared live gates and
   held-key bookkeeping remain in force.
3. **Destroyed Tk checkbox rows retained variable callbacks.** Updating a
   surviving variable called destroyed widgets; Tcl callbacks also retained
   local rows and variables. Each row now retires exactly its owned trace on
   destruction, preserving peer observers and repeated teardown behavior.

The four canonical modules add 332 cases: pathless bridge 208, unresolved
identity 32, curses frame gate 72, Tk trace lifetime 20. Before each corresponding
product edit, its original proof failed with the intended assertion traces. A later private
replay of the **exact final 332 test bytes on the exact starting source** gave
137 AssertionError failures / 195 passing controls, zero errors, skips or
deselections. Shared source was never restored to perform this replay.

## Observed verification

| Check | Result |
| --- | --- |
| Starting-source baseline | 3,190 passes, zero skips |
| Fixed focused and adjacent behavior | 1,062 passes, zero skips |
| Lint/types, fake preview, private boot-guard negative mutant | Pass |
| Pinned Go 1.26.8 race, vet, 350,000 fuzz executions | Pass |
| Actual Windows AMD64 test cross-build | Pass; native acceptance not run |
| Canonical main plus separate Orca | **9,544 passes, 14 skips, one failure** |
| All 37 retained audit modules / 3,342 cases in that full run | Pass |
| Bounded four-test GTK timing diagnostic | Four passes; failure not explained |
| Starting/final source, regression archives and incremental/cumulative diff readback | Pass |
| Fresh final runner/cancellation/geometry/report campaigns | **Not run; failed gate** |
| Final ISO/QEMU/native Windows/physical/firmware acceptance | **Not run / blocked** |

Main pytest reported 9,543 passes / 14 skips / one failure in 752.03 seconds;
the separate Orca suite reported one pass. Both fresh JUnit files were checked
for duplicate IDs and errors. The 14 skipped IDs exactly match the prior
image-only skips: two generated live-config cases and 12 ISO/manufacturing
cases. They are not acceptance passes.

The Windows artifact is an actual 9,021,440-byte PE32+ AMD64 test binary,
SHA256 `d05ac4db6463aa6d7f51188f3bcfcfb4891aeab549ab481843538114904a76d9`.
A cross-build is not native Windows execution.

## Unresolved local gate failure

`tests/test_accessible_runtime.py::test_slow_sound_discovery_does_not_block_gtk_or_update_closed_dialog`
failed its **first** 60 ms bound at line 1620:

```text
assert (20522.049777507 - 20521.974844728) < 0.06
```

Observed click time was 74.932779 ms. Complete gate logs, both JUnit reports,
binary, exact source freeze and statuses were preserved before any follow-up
in `primary/failed-candidate-1/`. The raw archive contains their bulky bytes.
No test was cancelled or assertion weakened. The gate remains failed.

One bounded diagnostic ran only after the canonical main/Orca pair exited.
It retained all original test bodies and both timing assertions, wrapping
Python boundaries with in-memory wall/thread-CPU/thread-ID observations.
All four sound cases passed. In that separate execution, opening the dialog
took about 9.50 ms and parent rendering another 4.23 ms; pending-ticket polling
returned promptly. The controlled discovery ran on a different thread and
settled after its barrier was released. These observations **do not attribute
the earlier 74.9 ms delay**. The read-only host load/CPU-pressure sample also
cannot identify its cause. No production optimization is justified by the
available trace alone. A later passing run would not explain this failure.

Source review identified two separate fixture follow-ups, neither changed:

- The first sound timing assertion precedes its `try/finally`, so its failure
  leaves the controlled barrier to time out after two seconds. A future narrow
  cleanup change must also establish owned-worker settlement before mocked
  audio functions are restored. Preserve all timing and closed-dialog checks.
- The new Tk trace test's independent peer observer captures its variable.
  It may retain that fixture's interpreter after root destruction. Prove this
  lifecycle independently, then retire only that exact peer token after all
  assertions, including failure paths. Do not retire product traces or mask
  callback errors. This later test cannot explain the earlier GTK failure.

Exact next action: capture a bounded trace that reproduces and distinguishes
the GTK delay (construction/rendering, thread startup, native display waiting
or scheduling). Prove the fixture cleanup paths before editing them. Re-freeze
and independently review any changed bytes, repeat the affected original/fixed
cases, then rerun the applicable gate after an evidenced correction. Do not
blindly retry or raise the 60 ms limits. Final campaigns remain admitted only
after a passing canonical gate.

## Isolation, retained evidence and remaining limits

All primary runtime work used a no-space interpreter alias and eight immutable
rejecting child-PATH guards. Twelve harmless guard admission probes passed.
Two actual SDK calls (baseline and full gate) performed only the explicitly
allowed offline listing of owned local fixture files. Zero forbidden guarded
fallbacks were recorded. PATH guards are not a universal OS sandbox.
Only the canonical main/Orca pair ran concurrently; diagnostics followed their
completion. Tk/GTK used private X11 at 72 DPI. No physical target or real erase
engine, loop acceptance, guest or hosted job was used this pass.

`primary/source-artifact-verification.json` authenticates all 762 starting
inputs, the 37-module regression archive, exact final patches and private
original proof. `primary/failed-gate-verification.json` explicitly records
`accepted: false`. `primary/audio-diagnostic-observations.json` contains the
bounded trace. `ui-boot/final-cross-review.json` authenticates the three runtime
and four new test files. Runner upstream source notes distinguish direct
official-source observations from unavailable retrieval attempts; they are
not downloaded-byte receipts or ISO execution proof.

Bulky raw JUnit/transcripts/test binaries are compacted with exact byte indexes
and archive readback; `primary/retention-verification.json` and `SHA256SUMS`
authenticate retention. Scripts for the held campaigns are retained but have
no fresh results, fixtures or screenshots; pass17 results are not reused for
this source. Working staging remains `/tmp/pass18-primary` and `/tmp/pass18-ui`.

Historical acceptance remains open: review pass16's native regular-file loop
probe incident, recover pass8's original unexplained SIGTERM/exit143 platform
attribution, and recover pass9's unavailable original timing failure trace.
This new timing result cannot explain those historical events. Public ISO,
QEMU, native Windows, physical reconnect, firmware and real-hardware acceptance
need their prescribed authorized isolated/physical environments. The unattended
development-host constraints remain in force.

The canonical record is `.ai/memory/unfinished-work.md`, item
`BW-BUG-AUDIT-20261017-PASS18`; its checkpoint history is preserved separately.
Source is local and uncommitted; nothing has been pushed, merged, deployed or
released. Full acceptance and the requested exhaustive verification are blocked.
