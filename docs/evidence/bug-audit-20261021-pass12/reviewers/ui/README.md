# PASS12 UI bounded review

Baseline: `b462e62005a752b0e5f2a066bda19bd9c79bbd8b`, branch
`fix/safety-audit-20261019`, `/workspace/beamo-wipe`. No repository files edited.
No newly proved product defect. Existing assertions remain unchanged.

Fresh focus: finished result to report/new-session/shutdown handoffs; current and
stale discard generations; duplicate and concurrent admissions; busy cleanup
and restoration; toolkit close/startup/failure ownership; console and accessible
result/copy equivalence. Source review included static helper/gallery boundaries.

`terminal_handoff_model.py` independently predicts terminal actions for all 11
result outcomes and all report-preference/verified-receipt combinations. It
checks 9,636 event words with 29,304 events, 4,884 stale-generation refusals,
88 busy initial-admission refusals, 88 busy current-confirmation refusals and
88 restored positive controls. It also checks 64 admissions raced by three
fresh harmless Python threads. Positive outcomes include 2,728 shutdown and
2,057 new-session terminal states. Zero model mismatches and native callbacks.
All process, actual inventory, engine, power and sound boundaries refuse.
Threads start before any GUI is imported; this process runs no native GUI.

`focused-ui.xml` contains 665 unique strict passing IDs from 33 existing modules,
zero failures/errors/skips, and no warning/error/critical log matches. The
receipt records a private 72-DPI Xvfb, `BEAMO_ISOLATED_X11_TEST=1`, private XDG
runtime/cache, cleared inherited D-Bus/AT-SPI selectors and child umask 022.
`:1`, `:99` and peers were preserved. Exact module list and invocation are in
`focused-modules.json`, `run_focused.py` and `focused-ui.status.json`.

These focused IDs overlap the canonical suite. The model's states, events and
thread races support invariants and add no canonical test IDs. No actual Orca,
pinned-browser, native-OS, engine, device, image, mount, firmware, power,
VM/network or physical/reconnect qualification was attempted. Finite checks
cannot establish absence of every defect.

Machine-readable findings/source hashes: `review-report.json`,
`reviewed-source-sha256.json`, `terminal_handoff_model.json`. Root independently
validates this evidence and owns the final gate and any release decision.
UI ownership is released; no helper, GUI or model process remains running.
