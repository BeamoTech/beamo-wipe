# Plain TTY early Erase input candidate

2026-10-17 source review only. At `console_wizard._plain_loop_body` Last Chance,
the presenter sleeps until countdown expiry without draining canonical terminal
input, then `_answer` calls `input`. A fully entered ERASE line could therefore
arrive while erase is disabled and be consumed only when the gate opens. This
would start the fake runner without a new action after review expiry.

Prepared `tests/test_plain_erase_typeahead_pass17.py` uses ordinary private PTY file
descriptors with default canonical settings, a fake monotonic clock, in-process
fake runner and all native application/process/discovery/power/audio effects denied.
It writes ERASE at early/middle/late countdown times, and writes a fresh BACK action
only after the enabled prompt. If stale ERASE is consumed, the fake runner records
that start instead. Fresh ERASE, prequeued BACK and prequeued canonical EOF are
controls across all three methods. No host terminal settings or physical devices
are changed. Eighteen cases prepared, still unrun; product source unchanged.
