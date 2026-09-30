# Continuing work from a fresh clone

This handoff consolidates the outstanding local work at the operator's explicit
request on 2026-09-30 UTC. Clone `https://github.com/BeamoTech/beamo-wipe.git`,
check out `main`, and read `AGENTS.md`, `docs/development.md` and this document.
A source merge is not a release or physical qualification result. Use the PR's
checks for the exact merged source; dated task receipts describe their own
revisions, not this combined tree.

## Included source work

The consolidation starts at main `498e1847e60cd80ab1a2c6c448e4e8dbe2254354`
(PR #81). These original local commits were replayed together; the CI guide
conflict retains both the updated local/hosted workflow and mandatory GTK rules.

| Task | Original commit | Scope |
| --- | --- | --- |
| #115 | `fe5f6151d9f3cea5eac0960d8c829121f00063aa` | Bounded background audio, UI polling, cancellation and fake-backend regressions |
| #120 | `ab228dd7b2ee9c24ab45241bfcce2c88685cc7fa` | Operation-specific doctor and accurate Blacksmith development guidance |
| #121 | `386ede3` | Pinned v0.2.11 release-note links and a separately reviewable public-description patch |
| #122 | `607655b` | Truthful detached-signing metadata and verification tests |
| #123 | `c170c85` | Optional local GTK handling and mandatory hosted execution guard |
| #124 | `cd5e771` | Bounded termination/reaping for the negative-gate test and lifecycle regressions |
| #125 | `9636e05f548629de3ee945e1fddae89caf826e86` | Authenticated compressed/raw USB verification and safe extraction |

The previously uncommitted cost-policy update in `AGENTS.md` and
[dated readiness audit](release-readiness-audit-2026-09-28.md) are preserved.
That audit is historical: its findings are not an assertion that all remain
unfixed. Old feature branch names also remain locally after their equivalent
work was merged; replaying those old snapshots would revert later fixes.
No ISO, USB image, private key or credential belongs in Git.

## Audio integration checks and bounds

The fake slow-audio regression documents the original synchronous baseline
(12 calls at 80 ms each, approximately 0.998 seconds). It requires the request,
progress tick and Stop handler each to return within 60 ms under that controlled
substitute; this is a test bound, not a universal hardware latency guarantee.
The implementation permits one worker and one latest waiting request, a
30-second operation deadline, cancellation/supersession, screen-epoch checks,
64 KiB subprocess output, and bounded terminate/kill waits. A stuck in-process
third-party call can occupy the single daemon; it cannot be forcibly stopped
by Python. Timed-out/stale results are discarded and no extra worker is spawned.
Physical audio and assistive-technology behavior still need their native gates.

During consolidation, controlled selector-creation failure reproduced an
owned audio child left alive with its stdout open. The new cleanup encloses
selector setup and guarantees termination/pipe cleanup even if selector close
fails. Three regressions cover creation, registration and close failures using
harmless children; the focused audio/sound set passed all 26 tests locally.

## Remaining operational work

- **Physical acceptance remains NOT TESTED.** Follow
  [Secure Boot acceptance](secure-boot-acceptance.md) and the
  [physical evidence packet](evidence/physical-acceptance-111/README.md).
  Unknown firmware trust/revocation state cannot qualify as Pass.
- **#118 review enforcement remains incomplete.** The preparatory workflow and
  policy were merged in PR #80. At this handoff, GitHub requires the strict,
  app-bound `CI gate` with administrator enforcement, but no required approval
  rule. The dedicated App review route was not proven operational. Do not infer
  remote enforcement from the presence of documentation or workflow files.
- **#121 public text remains a separate action.** The source fix and exact
  public-description patch are included; do not assume published v0.2.11 text
  was edited. Existing signed bytes and release assets remain immutable.
- **#122/#125 publication:** new source metadata does not change historical
  release bytes. Any future release needs separate authorization and exact
  source qualification through the current release procedure.
- Native Linux/GTK/Orca, Windows and KVM image checks are hosted gates. Local
  macOS skips must not be represented as native coverage. A new clone on
  Windows does not turn the Linux live application into a Windows wipe tool.

## Physical USB and Windows PC handoff

The operator has a spare, unidentified x64 Windows 11 PC. Manufacturer/model,
BIOS version/date, BIOS Mode and Secure Boot State are still to be collected
(read-only `msinfo32` initially). Ordinary Windows remote desktop does not
control firmware or the live USB session. Arrange existing out-of-band access
or operator assistance before rebooting. Valuable disks must be disconnected;
this test stops at the guide and does not run an erase. Do not change Secure
Boot, keys, revocations, SBAT policy or firmware clock to make a test pass.

The already-published **Q12 / v0.2.12** image is the inspected physical-test
input, not a fresh build of this consolidation:

- Source: `e986419379f512f8088f5982ee02a51dc91a9dae`.
- Build: `625971a4-afef-5398-9bec-d96455192ab3`.
- `beamo-wipe-0.2.12-amd64.img.gz`: 601441384 bytes;
  SHA256 `a3d2a65d8941facbd30b794b083419dc694511903281e57cd028db565bdc1972`.
- `beamo-wipe-0.2.12-amd64.img`: 2147483648 bytes;
  SHA256 `1e807895ee643a35d90a0c2302143f02b01de91aec564a3972d86740c55ae10b`.

On the Mac, the inventory and manifest signatures were authenticated against
the repository's approved key registry, and both files' hashes/sizes verified.
Disposable staging was `/private/tmp/beamo-wipe-119-media`; it is not part of
a clone and may be removed. Use [release verification](release-verification.md)
to obtain and authenticate another copy.

Etcher was last observed **ready, not flashing**, with that raw image and only
`VendorC ProductCode Media`, 31457280000 bytes, external USB selected. It was
then `/dev/disk4`, with a BEAMOSD FAT partition and a Linux partition. The
operator authorized overwriting that exact stick. Never reuse a device number
without re-identification. Confirm whether the operator subsequently flashed
it, then complete the documented post-flash readback before boot qualification.
Capture pre/post firmware and shim policy evidence and exact boot/refusal stage.

## Consolidation verification

The full local fake-device suite and the PR's required hosted qualification
must be evaluated on the combined source. The initial main baseline's
[run 36647113738](https://github.com/BeamoTech/beamo-wipe/actions/runs/36647113738)
failed waiting for `BEAMO_WIPE_KEY_SPACE_RELEASED` in the QEMU `bios-extra`
report-export flow, after `BEAMO_WIPE_REPORT_SAVED`; its Windows job passed.
Do not report that baseline run as green. Retained logs show the observation,
not proof of the root cause. The consolidation PR records its own results and
any subsequent correction. No protection or safety check may be weakened to
obtain a passing merge.
