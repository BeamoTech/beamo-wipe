# Comprehensive audit, pass 7 — 2026-10-16

Baseline: `f102dfbe5a705fda10880fecc24626c7693c10f0`.
Repo/worktree: BeamoTech/beamo-wipe, `/root/dev/Beamo Wipe`.
Branch: `fix/safety-audit-20261015`.
Implementation: `de55b078514e2028a2a22633f1d7aa2941f9e0b6`, committed and pushed after all applicable
local gates passed. Source remains unmerged and unreleased.

Three bounded reviewers freshly inspected discovery/boot/exclusion/classification/
authorization, engine/process/progress/log/evidence/method behavior, and
wizard/Tk/GTK/console/boot/recovery/build/compatibility. The primary independently
reviewed report export/privacy/diagnostics/session persistence and each finding.
Existing passing history was a baseline, not acceptance for this pass.

## Proven changes

- Report export rejected unchanged padded model/serial/WWN metadata that disk
  discovery had accepted and trimmed. The same hardware could reach the erase
  flow but prevent the owner from saving its report. `_fingerprint_node` now
  normalizes harmless hardware padding before applying the existing bounded
  export text parser. Only these three hardware fields normalize padding.
  Device/volume paths, type, transport, parent,
  filesystem/version and UUID retain their exact-edge checks. Controls and
  oversized IDs remain refused; protected hardware changes remain refused.
  The new 65 cases give 30 original failures and 35 passing controls.
- A verification receipt accepted swapped/misclassified skip and expected-failure
  records if the sum of their counts matched. The builder now checks each kind's
  count, and stored-receipt verification applies the same invariant. Ten new
  cases give six original failures/four controls, including a stored receipt
  with a recomputed valid digest but inconsistent classification. No workflow,
  publication rule, required gate or receipt schema was changed.

The final **75 new cases** produce **36 intended regression failures /39 passing
controls**, zero setup errors, on an exact isolated baseline source tree. The
working checkout was never reverted. All **75 pass** on the fixed source.
[Original](original.txt), [reproduction harness](original-proof.py),
[fixed cases](fixed.txt), [four frozen source/test hashes](source-sha256.txt).

A possible duplicate-skip issue was investigated and rejected with a concrete
real-pytest trace: call and teardown can both skip with the same ID/reason.
These are two measured outcomes and must remain supported. The parser and
receipt roundtrip preserve both. [Contract trace](engine-duplicate-skip-contract.txt).

## Fresh independent verification

Counts below overlap the full suite and must not be added as unique passes.

- Discovery/safety: **648 tests**, 53 modules, no skips; [replacement log](selection-tests-x11.txt),
  [module list](selection-files.txt), [review and hashes](selection-review.json).
  **454** controlled order/malformed/permission/retry/override observations
  ([script](selection-matrix.py), [result](selection-matrix.txt)); **160**
  concurrent discoveries across eight workers ([script](selection-concurrent.py),
  [result](selection-concurrent.txt)).
- Corrected export fix: independent **731 adjacent tests** ([log](selection-export-final-tests.txt))
  and **1,120** equivalence cases ([script](selection-export-final-equivalence.py),
  [result](selection-export-final-equivalence.txt)); default parser behavior
  matches baseline, with only harmless hardware-padding normalization added.
  **240** padding/maximum-length/control/protected-change cases
  ([script](selection-export-matrix.py), [result](selection-export-final-matrix.txt)).
  Primary two-scan controller/request/helper-receipt roundtrip: **27** padded
  cases accepted and **27** second-scan hardware replacements refused before
  the fake helper ([script](export-controller.py), [result](export-controller.txt)).
- Engine/evidence/lifecycle: **699** tests ([log](engine-pytest.txt),
  [collection](engine-collection.txt)); final changed-module/adjacent **53**
  ([log](engine-skip-kind-fixed.txt)). **21,600** seeded full-log/projection
  comparisons and **24** readiness/partial-record controls
  ([script](engine-matrix.py), [result](engine-matrix.txt)).
- Receipt fix: independent **59 tests** ([log](surfaces-receipt-review-tests.txt))
  and **2,268** exhaustive kind/count combinations: 63 valid accepted and
  reverified; 2,205 inconsistent refused ([script](surfaces-receipt-matrix.py),
  [result](surfaces-receipt-matrix.txt)).
- UI and boot/build: **1,359 unique UI passes** after resolving two Chromium-PATH
  skips through the complete build replacement. Build/compatibility **487 pass**
  with two expected generated-lb-config skips. The three-review-suite union is
  **1,862 unique passes /2 expected skips**, not their arithmetic sum.
  [UI log](surfaces-ui.txt), [build replacement](surfaces-build-replacement.txt),
  [union](surfaces-combined-summary.json), [source review](surfaces-review.txt).
  **54,000** navigation events plus **54** language/method/review-detour
  combinations ([script](surfaces-navigation.py), [result](surfaces-navigation.txt));
  **40** fake sessions with four simultaneous callers each verify exactly one
  start, blocked shutdown while active, stop cancellation/async stop and terminal
  duplicate/retry handling ([script](surfaces-start-stop.py), [result](surfaces-start-stop.txt)).
  Actual `./preview` at 72 DPI was visually inspected by reviewer and primary;
  [screenshot](surfaces-preview.png), [owned-process teardown](surfaces-preview.txt).
- Primary malformed-report sweep: **5,760** calls across result rendering,
  sharing creation, text and HTML APIs, with no unhandled exception
  ([script](malformed.py), [result](malformed.txt)).

## Final local acceptance

The first complete gate caught **two genuine draft regressions** in unchanged
Unicode report-destination tests: 6,200 passed /14 expected skips, with private
Orca separately passed. Reusing discovery's stricter identity parser rejected
model separators which export safely renders with a generic label.
[Failed full gate](failed-draft-gate.txt), [focused proof](unicode-draft.txt),
[draft diff](draft.diff). The correction preserves the original export parser
and receipt sanitization, normalizing only harmless hardware padding.
All 75 new and five existing destination cases pass; no existing test changed.
The earlier narrow independent export approval missed this separate destination
module and is superseded by the expanded corrected-source review above.

Final corrected frozen-source gate passed:

- [Main pytest](final-tests.txt): **6,202 passed /14 expected image-only skips**,
  no failures/errors, in 476.19s; mandatory GTK result guard passed.
- Separate private Orca: **1 passed**, giving **6,203 unique passes**. The
  [JUnit-derived summary](final-summary.json) confirms no duplicate IDs and
  lists every skip: two generated lb-config and twelve manufacturing-ISO cases.
- [Lint/types/security/shell/developer formatting](lint.txt), [preview](preview.txt)
  and [private negative safety mutation](negative.txt) passed after correction.
- Pinned [Go1.26.8](go-version.txt) [uncached race](go-race.txt), [vet](go-vet.txt)
  and [350,000 fuzz executions](go-fuzz.txt) passed again after correction;
  native inventory override stayed unset.
- All [four frozen source/test hashes](source-sha256.txt) match the tested bytes.
  Runtime source digest: `ff52fe2414436c9bec18cee235ee8a104fe16f567f7cd4237dabe62dcbdc0d42`.

The unchanged TODO-regex warning in `release_manifest.py:40` and mypy
untyped-body notes are informational. No material lint/type warning remains.
The local `ci-hosted.sh tests` invocation used `BEAMO_GATE_CHILD=1`, pinned Go
and the no-space Python-venv alias on PATH, `GOTOOLCHAIN=local`, and explicit
scratch JUnit paths. The suite and Orca used private XDG/D-Bus/Xvfb sessions at
72 DPI. Dependencies were already installed; no hosted execution or dependency
upgrade was involved. No source or test changed after the final freeze.

## Setup history and limits

Initial reviewer discovery/build subsets lacked a private DISPLAY, and build/UI
subsets lacked Chromium on PATH. Original failures/skips are retained in
[selection setup](selection-tests.txt), [build setup](surfaces-build.txt),
and [UI log](surfaces-ui.txt). Complete private-72-DPI replacement runs and
explicit browser-case reruns resolved those environment issues; they were not
source bugs or passing original runs. An initial permission harness allowed
predecessor read-only mount/cmdline probes; the corrected harness mocks all
production reads and reran successfully. No native lsblk inventory was taken.

The primary controller harness initially omitted preview mode and correctly
refused its regular-file evidence directory via the live tmpfs guard before
writing ([setup refusal](export-controller-setup-failure.txt)). The corrected
harness explicitly uses fake preview mode and mocks all block/process/marker
boundaries; the guard itself remains unchanged.

Only fake devices/process boundaries and ordinary temporary files were used.
No actual nwipe, connected-disk/USB operation, host power/firmware change, guest,
ISO/QEMU, native platform acceptance, hosted CI, PR, merge or release occurred.
ISO/QEMU, native Windows and physical media/firmware/reconnect qualification
remain separate, unrun acceptance. No method/argv/token/countdown/boot-exclusion/
claims/pinned-version/surface boundary was relaxed. This audit does not prove
an absolute absence of bugs. The canonical [unfinished-work record](../../../.ai/memory/unfinished-work.md)
retains qualification and current task state. Scratch names in reviewer logs
refer to this run's `/tmp/beamo-pass7-*`; retained local copies are adjacent here.

Final complete-diff, artifact and frozen-byte checks found no further
reproducible actionable defect in the reviewed local scope. All four tested
source/test hashes match the implementation commit. Only evidence and handoff
documentation changed afterward. GitHub read-only checks found no branch PR
or hosted run; no merge or publication was performed.

Readable transcript copies have trailing spaces/tabs and extra blank EOF lines removed for repository
whitespace checks. [Original transcript bytes](original-transcripts.tar.gz)
preserve every affected log and the original draft diff without normalization;
this formatting step changes no source, test, verdict, or measured count.
