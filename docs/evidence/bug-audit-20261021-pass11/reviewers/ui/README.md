# PASS11 bounded UI review

Baseline `b46e5642d4c849d503b41d8bf562cfb1f9fad68b`. No new product defect was
proved and no repository file was edited. All 59 reviewed source/test inputs
are byte-identical to the baseline. Machine evidence: `review-report.json`.

The final strict focused run executes 444 unique cases across 44 modules:
zero failures, errors, skips or Python warnings. It uses a private 72-DPI Xvfb,
D-Bus session, XDG runtime/cache and child-only umask022. Assertions are unchanged.
The first run also passed 444 cases but emitted a shared AT-SPI cache bus
diagnostic. That history remains in `initial-focused-ui.*`; the final isolated
run has a functioning AT-SPI registry and no such warning. Actual Orca speech
acceptance belongs to root's separate clean container gate.

Fresh model `review_detour_layout_matrix.py` uses actual public wizard actions
and actual DryRunRunner starts, with injected clock/layout/device metadata and
forbidden native boundaries. It covers 360 composed review scenarios and 63
layout cases across all three methods. Results:

- 720 detours and 975 fresh-countdown checks; nested keyboard, advanced/report
  help, refresh cancellation, diagnostics and unsaved-report shutdown returns.
- 360 nested overlay claims and 360 held-overlay refusals; duplicate old close
  callbacks cannot authorize or extend a completed overlay timer.
- 18 successful layout changes revoke owner/target/token/operation consent;
  45 unchanged/unsupported/malformed/failed changes preserve prior context.
- 63 absent-owner and 63 wrong-token refusals; 3,132 blocked Erase calls.
- 423 positive fake starts only after an explicit fresh Erase action, plus 423
  expiry ticks that enable the gate without auto-starting.
- Zero model mismatches/native callbacks. Controlled `/dev/` lstat failures
  prevent even fake paths from reading host device metadata. Expected rdev
  diagnostic lines document that fake-only refusal path.

The initial all-green model and later pre-lstat-guard version are retained as
history. The final script/metrics/status and source hashes identify the version
for root replay. These model observations and overlapping focused tests are
supporting evidence, not additions to canonical unique coverage. Native media,
firmware, pinned browser and physical acceptance remain unverified.

Ownership released; no source edits pending.
