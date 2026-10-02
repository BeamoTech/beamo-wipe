# Report key-release investigation — 2026-10-02

PR #84 was qualified and merged as
`f21cdf17b67744df95aeffa2fdd76e85e5808091`. Its successful
[PR run](https://github.com/BeamoTech/beamo-wipe/actions/runs/37045385234)
tested an identical source tree. The subsequent
[main run](https://github.com/BeamoTech/beamo-wipe/actions/runs/37048194285)
failed twice: attempt 1 at `bios-quick_zero-repeat`, then the one bounded
failed-job retry at `bios-quick_zero`. Both reached `REPORT_SAVED` and
`EXPORT_READBACK_VERIFIED`, but lacked a fresh
`BEAMO_WIPE_KEY_SPACE_RELEASED`. Native Windows and CodeQL passed.
These failures do not qualify main for release.

The failed evidence archives are preserved outside the checkout. Attempt 1:
SHA256 `ef2b1e32ec69f9e5b97e87f9f47417f892758a6bd78485de4d75f4ecbd0e66ca`;
attempt 2:
SHA256 `2cfbc0b584af4b0cce5a62ccdff4a25df1d29f328419b3c8877f19478cdf4555`.
Both downloaded hashes match GitHub's artifact digests. The run retains the
serial traces and manifests with the exact source/build/image identities.

## Reproduction and correction

A controlled real-Tk regression schedules continuous timer activity, delivers
a Space release, and inspects held-key state before permitting the idle queue
to run. The old `after_idle` callback leaves the hold set. A queued `after(0)`
timer clears it while that activity continues. This reproduces an idle
starvation defect; correspondence to the QEMU failures remains an inference,
not an established root cause.

The correction changes only Space-release scheduling. Queued repeat presses
still cancel the pending callback; same-timestamp X11 repeat presses remain
rejected even if cleanup ran first. Release receipt emits a fixed diagnostic
marker, distinct from the existing completed-release acknowledgment. No
marker is fabricated and QEMU still requires a new completed acknowledgment.
No QEMU timeout, retry budget, safety confirmation, disk selection or nwipe
flags change.

An additional isolated-X11 test uses real server-delivered Tab navigation,
Space press/hold/release and the fake-device runner. It checks report redraw
destroys the initiating Save control, the hold clears after release, and
shutdown never occurs from the arriving key. This follows the existing
explicitly isolated X11 injection policy; it never injects into the user's
desktop. The fixture exports only a simulated report receipt.

On WSL2 Ubuntu 24.04 x86_64 / Python 3.12.3, the corrected targeted Tk and
QEMU synchronization suite passed **314 tests**. The full fake-device
`scripts/test-all.sh` suite passed **5,629 tests**, with **57 expected local
skips**, zero failures/errors, in 777.44 seconds. All six new cases ran.
Ruff and mypy passed. All 580 tracked source/test files and gate scripts in
the Linux snapshot matched the candidate worktree byte for byte. The
same-timestamp regression now processes timer events, preserving its refusal
and separate-press assertions; its mock still proves pending cleanup is
cancelled by a queued repeat.

Hosted results will be recorded in the follow-up PR handoff before qualified
merge. Physical Secure Boot task #119 remains
**NOT TESTED**; no physical disk, USB, firmware or release was modified by
this investigation. See the [physical acceptance procedure](../secure-boot-acceptance.md).
