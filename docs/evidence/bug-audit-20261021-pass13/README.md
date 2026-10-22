# Beamo Wipe: thirteenth comprehensive local audit

Six independently reproduced defects are repaired on baseline
`7fcd706b44c0d63cf5f2959bcd235968e8300274`, branch
`fix/safety-audit-20261019`. Audit date: 2026-10-21, America/Chicago.
The complete local gate records **11,968 unique Python passes** (11,967 main
plus one separate Orca case), **28 unchanged unverified skips**, zero
failures/errors and zero Python warnings. Every previous main test ID remains;
exactly 170 Python cases and eight named Go outcomes were added.

## Verified defects and repairs

| Demonstrated baseline behavior | Repair | Final regression bytes on baseline |
| --- | --- | --- |
| A CI execution log could be rewritten in place without changing inode or length. `run_gate` then issued a receipt containing the original output hash beside different retained bytes. | Flush before capturing the final descriptor snapshot; reopen without following links, verify complete metadata and bounded readback against the collected output digest, then recheck the descriptor and pathname before issuing a receipt. | 16 failing cases / 20 controls. |
| Local evidence publication closed its only descriptor before linking and checked only device/inode afterward. Changed bytes, public permissions, and extra hardlinks could be published successfully; the public API could checksum the changed bytes. | Pin a duplicate descriptor through publication and cleanup, retaining the existing pre-link close-failure boundary. Verify exact bytes and full private metadata before/after linking, temporary-name removal, and directory synchronization. Retire only owned entries on refusal. | 44 failing cases / 19 controls. |
| Canceling an outcome audio ticket during final preparation or binary resolution still launched a new fire-and-forget player. | Check ticket cancellation before resolution and immediately before spawning. Normal playback and existing reaper behavior remain covered. | 8 failing cases / 12 controls. |
| Failed GTK construction and an externally returned/interrupted main loop left the main window and timer alive. Queued input could still reach the retired view. | Initialize retirement state before GTK setup; retire partial construction and every loop exit, preserve primary exceptions and restore the exception hook. Bind loop quitting to the owned nesting level and invalidate queued actions on close. | 28 failing cases / 4 controls. |
| KeyboardInterrupt/SystemExit during the final launcher build check released the build lock but retained the build's success receipt, including when launcher bytes changed. | The existing owned-receipt cleanup also runs for BaseException, then propagates the original interruption. Foreign receipt and launcher replacements remain preserved. | 4 failing cases / 15 controls. |
| Media hashing accepted a changed same-inode file after hashing, including same-size bytes with restored mtime. The returned fingerprint described earlier bytes. | Compare opened/named inode, mode, size and modification time; perform a second bounded, cancellable hash through the pinned descriptor and compare contents before accepting the fingerprint. | 5 failing Go leaves / 2 controls. |

Root reproduced every original finding before authorizing its edit, reviewed
the complete product/test diffs, and independently replayed the exact final
regression bytes on archived baseline source: **100 Python failures / 70
controls**, plus **five failing Go leaves / two controls**. All 170 Python
cases and seven Go leaves pass after repair. All 18 separate root Python
probes and three root Go leaf probes also pass. These supporting results
overlap canonical coverage and are not added to its unique count.

Six product files and six new regression modules change. **Every existing test
file is byte-identical**, preserving all previous assertions. All **831 frozen
source/test/build inputs** match their recorded hashes.

## Completed local gates and artifacts

Configured compilation, shell checks, Ruff/security/developer formatting and
mypy pass. Preview, private negative safety mutation, test/desktop doctors,
uncached Go race/vet, 350,000 fuzz executions, Windows test cross-compilation
and Windows/Linux launcher builds pass. Go records **467 named race passes**
and two unchanged native platform/inventory skips; every prior named outcome
remains and exactly eight pass events were added. Cross-builds do not establish
native acceptance.

Checks run serially in one unprivileged development container, with child-only
umask 022 and private 72-DPI display/session contexts. Independent artifact
inspection checks PE32+/ELF64 x86_64 headers, bundle/source identity, hashes and
executable modes without executing native launchers. The actual fake-device
Tk welcome was visually inspected after paint and closed through its registered
normal-close callback with exit 0. Nine unchanged supplemental browser cases
pass under system Chromium; the missing pinned Playwright runtime remains
unqualified. Clean post-commit launcher identity is retained outside Git to
avoid self-reference.

## Five bounded reviews and root model replays

Each fresh model was independently replayed against the final source freeze,
with positive and refusal controls and zero mismatches/native callbacks:

- Typed live-source ownership: 332 states, 132 positives and 200 refusals;
  typed/udev sources, case collisions, duplicate owners and link agreement.
- Audio queue arbitration: 128 states, 56 accepted actions, 328 canceled
  tickets and 64 closed-worker refusals, using captured worker callbacks.
- Terminal provenance: 72 method/identity/evidence/log/context scenarios,
  six normal accepts, 66 refusals and 72 restored controls using owned files.
- Review/discard epochs: 108 scenarios and 1,926 events, including 216 old
  epoch refusals, 90 busy refusals and 108 fresh elapsed-gate controls.
- Media mutation epochs: 40 states, 17 accepts and 23 refusals; each accepted
  fingerprint matches the current owned file's bytes.

Reviewer-focused counts overlap canonical tests. Their initial failures and
oracle corrections remain historical evidence. A proposed escaped UTF-8 label
issue was rejected after the local libudev encoder showed that valid Unicode
is preserved literally. The first media-model oracle incorrectly refused an
edit completed before the first read; its corrected positive control requires
the returned hash to match current bytes. GTK reviewer history retains an Orca
startup failure and a geometry failure reproduced with baseline source; the
complete final container gate executes the original cases and separate Orca
session successfully. No existing assertion was changed for these histories.

## Practical limits and remaining qualification

Readback detects the demonstrated changes before acceptance. It does not make
an unlocked file immutable after verification. The second media read uses the
existing overall context deadline and may consume more I/O time on slow media;
the existing manual-boot fallback remains available.

All 28 Python skips remain unverified: 14 generated image/artifact cases, nine
pinned-browser cases, four Microsoft-document reachability checks and one
legacy gcloud check. Go's two native skips remain open. Exact-source ISO/KVM,
actual nwipe/device behavior, native Windows execution, firmware, physical USB
and reconnect qualification remain unverified. Local development evidence does
not establish complete release qualification.

Blacksmith is the current hosted provider. No GCP/hosted CI, remote write,
PR, merge, release, actual engine/device/mount/firmware/power or guest action
occurred. Publication remains pending the earlier automatic approval review
that rejected operational-backlog metadata export as internal data; no retry
or bypass was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass13/verify_retained.py` to
verify every retained artifact hash, the frozen inputs, preserved existing
test bytes, exact baseline failures, previous/current Python IDs and skip
reasons, and previous/current Go named outcomes. Remaining acceptance and next
actions are recorded in the canonical unfinished-work backlog.
