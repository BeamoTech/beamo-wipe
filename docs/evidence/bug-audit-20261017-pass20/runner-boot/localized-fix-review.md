# Pass20 localized discovery/audio review — candidate 1

2026-10-17 / Codex `/root/pass20_runner_boot`. Source-only independent review
requested by root after its original-case proofs and localized correction.
Branch `fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. No runtime or product/test edit was
performed by this reviewer. The exact candidate hashes and inspected XML/log
hashes appear in the companion JSON. This dated review is superseded by any
later exact-input review, without changing the original proof history.

## Blocking adjacent audio candidate

Audio candidate `8b8eb823699099572c49fae867984c8f6fb6981a1f8929abc49e6a4f784263b0`
fixes Thread constructor/start rejection cleanup, but the acceptance event is
set inside the same broad try. An exception after `launch_allowed.set()` has
mutated its flag leaves that flag true. The except branch retires the thread
and selected queue; the finally branch then opens `launch_decided`. The old
handed-off target can enter `_run` even though the caller rejected its launch
and a replacement can acquire the worker slot.

This is source-supported, still UNPROVED at review time. The adjacent six-case
`audio_acceptance_boundary_candidate.py` injects failure after the fake event's
mutation, invokes the old target only after the decision is released, and
uses `_run` as an admission sentinel. It creates no OS thread. Root must
independently review/run before any correction; it is unrelated to native
abort attribution. An authorized correction must revoke the allow flag before
releasing the decision, preserve RuntimeError's failed ticket and propagate
other interruptions, then prove original and corrected adjacent cases.

## Discovery correction

Exact pass19-to-candidate diff changes only `_node_type` to strip before
lowercasing and adds `dm` to `_UNRESOLVED_HOLDER_TYPES`. No newly selectable
malformed physical TYPE was found in source review:

- `disk_nodes` now retains padded disk observations, but `should_hide` still
  requires the original exact `disk` token for a nonboot picker row. Padded
  rows remain excluded from selectable disks. A matched boot exception is
  marked protected and cannot become a target.
- Normalized observations now participate in contradictory path/type checks,
  mounted alias coverage and final duplicate physical path accounting. A
  padded duplicate cannot hide behind the display filter to leave one normal
  selectable observation: repeated physical paths require multiple selectable
  copies or refuse a manufactured unique target.
- Normalized part/loop/rom and holder tokens enter their existing ancestry and
  refusal rules. Nontext TYPE still raises and public discover catches it as
  an empty fail-closed result; this change does not repair unknown tokens into
  a known eligible physical device.
- `dm` now follows the existing unresolved-member rule both directly and
  through a mounted opened child. Recursive `_node_mountpoints` carries child
  mounts to a nested holder; the flat pending-parent walk visits every
  ancestor and uses the same unresolved-holder predicate. Thus the nested and
  flat correction does not depend solely on filesystem metadata being present.
- A blank unmounted mapping still introduces no invented mount/content claim;
  ordinary crypt remains single-parent and preserves unrelated targets. Final
  disk identity and authorization gates are unchanged.

No discovery correction objection remains from this source review. Its exact
source SHA is `9f5a5a36ddf9dad77c7195920ed6290ed745d4684d63beeac103882fb6198f65`.

## Root evidence independently read

The reviewer parsed actual retained JUnit XML without importing product code,
read the original failure logs and root status/review JSON, and compared each
canonical new module byte-for-byte with its original root-run proof module.

| Root campaign | Independently measured result |
| --- | --- |
| Original candidates | 42 cases, 22 failures / 20 controls, zero errors/skips; mounted TYPE 28 cases, original six audio cases and prior eight Tk lifetime cases. |
| Expanded original audio | 18 cases, 14 failures / 4 controls, zero errors/skips. Two RuntimeError constructor cases escape as RuntimeError; other failing cases establish incomplete cleanup. These are call failures, not fixture/import errors. |
| Original ancestor mounts | 44 cases, four assertion failures / 40 controls, zero errors/skips; only generic dm fails, across both placements and both guarded acquisition routes. |
| Fixed/adjacent localized | 657 cases, all pass, zero failures/errors/skips. All 90 new canonical cases execute: mounted TYPE 28, ancestor mounts 44, audio interruptions 18. Six adjacent modules provide the remaining 567 cases. |

The three canonical modules are exact copies of their root-run proof bytes;
assertions, parameter values and controls were not weakened. They exercise
Thread constructor/start rejection, both selected queues and opposite-queue
retry, generic/padded holder refusal, nested/flat ancestors and ordinary/blank
controls. They do not cover the newly prepared acceptance-event mutation
candidate, and 657 passing cases therefore cannot resolve that objection.

Root's pre-edit source receipts report unchanged starting source during the
original campaigns. This reviewer authenticated source archive bytes and the
exact current incremental diff, but did not replay any campaign. Final full
gates, Tk correction, source/artifact readback and platform/hardware acceptance
remain root-owned and are not established by this review.
