# PASS9 UI review

No new verified UI defect; no repository edits.

Fresh private 72 DPI Xvfb/D-Bus execution: 29 existing modules, 310 unique passes, no failure/error/skip, Python warnings treated as errors. See `focused-ui.status.json`, `focused-ui.xml` and `focused-ui.log`.

Fresh independent fake sequence model: 399 sequences, 4,233 blocked Erase calls, 396 explicit DryRunRunner positive starts, 117 nested-overlay checks, zero automatic/native callbacks. See `visible_consent_sequence_model.py`, `.json`, `.status.json` and `.log`. Models are supporting overlap, not canonical totals. The script patches native process, inventory, engine, shutdown and sound boundaries to fail if called. Fake /dev path metadata is checked by normal dry-run safety code; absent fake nodes produce informational rdev diagnostics.

Reviewed owner/token/explicit-action consent, visible countdown after ten detours with repeated actions/delays, overlay depth, interface retirement, stale callback and held-key guards, Stop confirmation, evidence/result ownership and power affordances. The model has real positive starts for all methods and detours; elapsed time alone starts nothing.

This bounded review does not qualify real disks/engine, firmware/power/reconnect, ISO/KVM, native Windows or the full Orca route. Parent owns independent replay and final complete gates. Two guessed inspection paths were absent and corrected via file search; these were read-only setup lookups, not suppressed failed tests. No old assertion changed. All UI ownership is released.
