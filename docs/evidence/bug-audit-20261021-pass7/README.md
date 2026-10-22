# Beamo Wipe: seventh comprehensive local audit

Five independently reproduced defects are repaired on baseline
`938fe60347c78f2a745d5d5b04e30dfa013da809`, branch
`fix/safety-audit-20261019`. The final complete gate has **11,525 unique Python
passes** (11,524 main plus one separate Orca case), **28 unchanged unverified
skips**, zero failures/errors and zero Python warnings. All 11,382 prior main
test IDs remain; exactly 170 regression/control cases were added. Focused,
model, browser and Go results overlap or have different scope and are not
added to this total. [Machine summary](final-summary.json).

## Verified defects and repairs

| Trigger and consequence before repair | Result after repair | Exact new baseline proof |
| --- | --- | --- |
| A pseudo filesystem labels its source `/dev/sdb1` or `UUID=…`; live checks and simulated production discovery accept it as real boot media. | Known block filesystem proof accompanies source spelling and visible ancestry; unverified live rows refuse before findmnt fallback. Public mountinfo tuples remain unchanged; Btrfs, FUSE block, loop and typed source routes remain covered. | 30 failures, 34 passing controls |
| Optional diagnostic logging raises KeyboardInterrupt/SystemExit while a failed refresh is being retired; the UI remains REFRESHING. | Optional diagnostics cannot prevent fail-closed inventory replacement and a fresh retry. | 8 failures, 10 controls |
| Plain-console stdout buffers the review warning until the ERASE prompt; the five-second timer expires before the warning is visible. Built-in input may also ignore a flush failure. | Review output must flush successfully while its review hold is active; only then does the five-second review begin. Slow/failed flushes have explicit controls using real buffered I/O and a fake terminal. | 4 failures, 4 controls |
| A same-owner temporary entry is replaced or changed during preference/journal publication; save returns success for different bytes, including lost report intent after a Wizard restart. | Both stores retain the owned descriptor and check private named inode plus exact intended bytes before/after publication. Cleanup preserves foreign replacement entries. Post-publication journal uncertainty invalidates further writes. | 23 failures, 17 controls |
| `/proc/cmdline` contains invalid UTF-8; developer preflight raises a traceback instead of an actionable refusal. | Unicode read failures conservatively refuse live/unknown runtime operations. This is a preflight availability defect, with no unsafe erasure demonstrated. | 18 failures, 22 controls |

The 170 new cases retain 83 original failures and 87 passing controls against
unchanged baseline product source. Root separately replayed eight original
proofs before repair (39 cases), then all 39 pass against the frozen candidate.
Persistent publication checks are bounded observations in a private directory;
they do not provide an atomic filesystem compare/swap or protection from a
continuously hostile same-owner/root process.

## Source and test integrity

Six product files and five new test modules changed. One existing storage
fixture now supplies its already-used fake inode metadata to its preference
branch too. The original candidate failed that fixture before completion;
all old assertions, parameter values and call-count assertions remain intact.
Every other old test file is byte-identical. The verifier checks that exact
metadata-only edit and compares assertion ASTs. The frozen manifest contains
814 inputs, including all five new modules.

Configured syntax, shell/security/full lint, default mypy (52 source files),
preview and private negative safety mutation checks pass. The existing lint
script still prints its literal-pattern TODO notice and default mypy notes;
these are unchanged notices, not new Python warnings or failing gates.
Fresh uncached Go race tests record 338 named pass events and two explicit
native skips; vet, 350,000 fuzz executions, Windows test cross-compilation
and launcher cross-builds pass. All 59 Go/build component inputs match the
start and final freeze. Development test and desktop doctors pass.

Root independently verifies PE32+/ELF64 x86_64 headers, bundle hashes, current
build identity/source digest and executable modes. The real fake-disk Tk
preview was inspected at 72 DPI after welcome content painted, then closed
through its registered WM_DELETE_WINDOW callback with exit 0. The screenshot
stays outside Git; its hash and inspection receipt are retained. Nine unchanged
supplemental browser assertions pass under explicit system Chromium 155;
this does not qualify the unavailable pinned Playwright runtime.

Five bounded reviewers covered discovery/safety, runner/progress, UI/consent,
recovery/evidence/export and boot/build/developer tooling. Runner review found
no new verified defect in 1,509 focused cases or 39,000 parser/projection
comparisons. A fresh seeded baseline authorization model exercised 360
sessions, 9,528 public actions and 102 authorized starts/completions, with zero
native callbacks or assertion failures. These are supporting model results.
An exploratory cross-language re-read of a redacted sharing copy had no
supported in-product consumer; it was not promoted to a production defect,
and the original private evidence stayed verified.

## History and qualification limits

Retained failures include initial import-order setup, a nonexistent focused
path, an earlier plain-flush assertion draft, discovery's lint-only test import
revision, and the original incomplete storage fixture. Root's first final lint
also rejected two assigned lambdas in the new recovery helper. Equivalent
nested functions fixed those style violations without assertion/product
changes; the exact final module was replayed against baseline (23 failures,
17 controls) and all final gates restarted. The original root consent model
missed a fake imported identity alias and emitted missing-fixture diagnostics;
its corrected run has zero native callbacks and identical counts. None of
these historical runs is added to final totals. The canonical full suite
completed once on the final freeze. The first evidence-checker attempt applied
canonical ID uniqueness to a supporting plain-console record: its two external
proof modules share an empty JUnit classname and two test names. That record
has 54 passing executions and 52 unique JUnit IDs. The final verifier checks
those exact collisions explicitly; canonical/new/original root reports retain
strict unique-ID checks. The failed checker is retained as ledger history,
not a test or product failure.

All 28 previous skips retain exact IDs and reasons: 14 image/artifact cases,
nine pinned-browser cases, four Microsoft-document reachability checks and
one legacy gcloud check. Go's two native inventory/platform skips remain open.
ISO/KVM, real nwipe/device operations, native Windows execution, firmware,
physical USB/reconnect and independently disposable-worker acceptance remain
unverified. Blacksmith is the current hosted provider; no GCP gate was invoked.
No hosted CI, remote write, PR, merge, release or actual disk/firmware/power
operation occurred during this pass. Publication remains pending the earlier
automatic approval review that rejected operational-backlog metadata export
as internal data; no remote-write retry was attempted.

Run `python3 docs/evidence/bug-audit-20261021-pass7/verify_retained.py` to verify
source/artifact hashes, exact new/prior IDs, unchanged skip reasons, original
assertions and separate Go/model results. Baseline proofs retain original
workspace paths, identified by commit and hashes. The retained development
build receipt has baseline HEAD and `source_dirty=true` during candidate
checks. Clean development launchers are rebuilt after the local commit;
the final commit/build delivery receipt remains outside Git to avoid a
self-referential commit identity. This is local development verification;
qualification gaps remain open in the canonical backlog.
