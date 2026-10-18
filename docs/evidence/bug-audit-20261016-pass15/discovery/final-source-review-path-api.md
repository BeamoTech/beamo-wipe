# Pass15 final physical-path API source review

Reviewer: `/root/pass15_discovery`; 2026-10-16 23:52 UTC.
Result: **APPROVE exact current discovery/model/safety delta**, pending the
primary's focused and full reruns. This supersedes
`final-source-review-revised.md` for the latest source bytes. No runtime
campaign or product/test edit was made by this reviewer during this review.

## Exact reviewed bytes

Repository/worktree: `/root/dev/Beamo Wipe`; branch
`fix/safety-audit-20261015`; HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`.
Starting archive: `/tmp/pass15-primary/starting-source.tar.gz`, SHA256
`a8d57369704ca71daf701a53641ca73f76d32076583d330ffa9dc96716f979cc`.

- discover.py: `b08767b2e921779f53e62de67ac4c3fbaa281ea6ab90f9f6c682e3be96f9991e`
- models.py: `9fb0bcb97d35b1ee0f041f8ccb728fe8a2b9f173242a904bf2af6f7b5f42b95c`
- safety.py: `ba07089fa9ed77e3616af67147201a16b15b8c8582ca0ca9724e58ef980ecd9b`
- test_physical_observation_context_pass15.py:
  `319d7195e4a80be9c77ee00d5829da28d6680401352dc4dff6457b7ee3742323`

## Trigger and correction

The primary reports the prior full main session had1 failure,7566 passes and14
unchanged skips, with Orca1 pass. The failure was the existing direct-parser
contract `test_control_character_device_path_is_rejected_not_repaired` in
tests/test_accountable_audit_2026_09_03.py. The early physical-context loop
called node_path outside the per-row display skip and allowed ValueError to
escape for a path containing NUL. That run remains failed evidence; this source
review is not a replacement for rerunning the gate.

The current physical loop catches only ValueError around that node_path call.
It immediately returns a fresh DiscoveryResult with IDENTIFY_ERROR and
boot_identified=False. Default disks/selectable/physical_observations are
empty. The malformed text is never cleaned into `/dev/sda`, no other target or
partial safety context survives, and no exception escapes at that new API
boundary. This satisfies the existing test's no-selectable-target contract
while conservatively refusing the entire inventory.

An isolated empty/pathless row still reaches the separate empty-path branch
and skips, preserving the ordinary valid-sibling behavior. The narrow catch
does not swallow other parsing errors, does not relax path validation and
does not convert malformed paths into absent IDs. Mounted physical metadata
still receives full node_to_disk validation before this branch, retaining its
prior behavior. Names and structural checks earlier in the parser are
unchanged. The later `_physical_observation` call sees a path already validated
from the same immutable input row during this synchronous operation.

## Adjacent safety and API assessment

The earlier fieldwise serial/WWN extraction, per-field invalidity flags,
tri-state-RO duplicate signature, retained-context boot/mount closures and
defaulted model field are unchanged from the revised review. Valid contrary
WWNs, malformed-ID nonselectable projection, full mounted refusal and hidden
out-of-peer behavior retain that assessment.

The new defaulted context is still consumed only by guard/closure code and
does not enter session recovery or report serialization, which explicitly
uses discovery.disks. No token/method/argv/countdown/owner/build/claims/device
access boundary change was introduced by this correction. Source whitespace
check over the reviewed paths returned clean; no runtime assertion is claimed.

No source objection remains. Primary owns the focused regression and exact-
source full gate reruns. Any later source-byte change needs updated review.
