# Beamo Wipe: twelfth comprehensive local audit

Three independently reproduced defects are repaired on baseline
`b462e62005a752b0e5f2a066bda19bd9c79bbd8b`, branch `fix/safety-audit-20261019`. Audit date:
2026-10-21, America/Chicago. The complete local gate records **11,798 unique
Python passes** (11,797 main plus one separate Orca case), **28 unchanged
unverified skips**, zero failures/errors and zero Python warnings. Every prior
main test ID remains and exactly 28 cases were added. Go and model results are
reported separately.

## Verified defects and repairs

| Baseline trigger | Repair | Exact final regression on baseline |
| --- | --- | --- |
| The report-intent reader compared only device/inode at its final pathname check. A mode, link-count, or same-size content change between final descriptor and pathname snapshots was accepted. | The final named snapshot now matches device, inode, size, mode, owner, link count, modification time and change time before the saved preference is trusted. | 6 failures / 2 normal controls; all 8 pass after repair. |
| Linux launcher inventory used permissive `encoding/json`. Duplicate semantic keys could turn contradictory SATA/path evidence into a direct USB restart plan, while invalid UTF-8 and unpaired surrogates became replacement characters in media identity. | A bounded preflight rejects malformed UTF-8, replacement-decoded strings, trailing values and duplicate exact/case/escaped Unicode-fold keys at every object depth before typed decoding. Normal Unicode, paired surrogates, numeric strings and unknown unique fields remain accepted. | 24 failing leaves / 16 controls; all 40 leaves plus their parent pass after repair. |
| Deeply nested output from the selected local Python made `dev.py doctor` raise `RecursionError` without its promised structured report. | The existing malformed-probe boundary now treats decoder recursion as invalid local probe output and returns the usual structured blocked report. | 8 failures / 12 controls; all 20 pass after repair. |

Root reproduced every issue before the edit, reviewed the complete diffs and
ran distinct probes: preference 6 failures/2 controls, native JSON 5
failures/2 controls, and doctor 2 failures/2 controls. Every probe passes on
the final freeze. Every existing test file is byte-identical, preserving all
old assertions. Only three product files and three new regression modules
change. All **825 frozen source/test/build inputs** match their manifest.

## Completed local checks

The configured syntax, shell, Ruff/security/format and mypy checks pass, as do
preview, private negative mutation, test/desktop doctors, the exact new tests
and independent probes. The uncached Go race run has **459 named passes** and
two unchanged native inventory/platform skips, retaining all 418 prior named
passes and adding exactly 41. Vet, 350,000 fuzz executions, Windows test
cross-compilation and Windows/Linux launcher cross-builds pass.

Checks ran serially in one unprivileged container with child umask 022 and
private 72-DPI display/session contexts. Independent artifact inspection checks
PE32+/ELF64 x86_64 headers, current source/build identity, hashes and executable
modes without executing native launchers. The actual fake-disk Tk welcome was
visually inspected after paint and closed through its registered normal-close
callback with exit 0. Nine supplemental browser assertions pass under system
Chromium; this does not qualify the missing pinned Playwright runtime.

## Five bounded reviews and independent replays

Root independently replayed each final model on frozen source. Discovery covers
720 two-snapshot/precedence states (68 positives, 652 refusals); runner covers
120 states and 360 accepted generations; terminal handoff covers 9,636
scenarios/29,304 events including 64 thread races; recovery covers 288 journal,
lock and fake-engine states; launcher request epochs cover 16 delayed-worker
states and 64 closed-session refusals. Every model has zero mismatches and zero
native callbacks. Reviewer-focused counts overlap the canonical gate and are
not added to unique coverage.

## Remaining qualification

All 28 prior Python skips remain unverified: generated image/artifact cases,
pinned-browser cases, Microsoft-document reachability checks and the legacy
gcloud check. Go's two native platform/inventory skips remain open. ISO/KVM,
actual device/nwipe behavior, native Windows execution, firmware, physical USB
and reconnect qualification also remain unverified. Local development evidence
does not establish complete release qualification.

Blacksmith remains the current hosted provider. No GCP/hosted gate, remote
write, PR, merge, release, real engine/device/mount/firmware/power or guest
action occurred. Publication remains pending the earlier automatic approval
review that rejected operational-backlog metadata export as internal data; no
retry or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass12/verify_retained.py` to
verify every retained hash, the frozen source, prior/current Python IDs and skip
reasons, and prior/current Go named outcomes. Clean post-commit launcher
identity is retained outside Git to avoid a self-reference.
