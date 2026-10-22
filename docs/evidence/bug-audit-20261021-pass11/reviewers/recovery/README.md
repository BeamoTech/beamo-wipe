# PASS11 recovery, report, privacy and signing review

Baseline `b46e5642d4c849d503b41d8bf562cfb1f9fad68b`. No new product defect
was proved and no repository file was edited. Twelve reviewed source files
remain byte-identical to baseline. Prior assertions are intact.

The strict focused suite executes 1,063 unique passes across 66 modules.
Eight adjacent signing, support and result modules execute 449 additional
unique passes. Reports do not overlap: 1,512 unique local review passes, zero
final failures/errors/skips. These overlap the canonical gate and are never
added to its count. Both use child umask022; GUI cases use private72DPI Xvfb.
The first adjacent run lacked X, retaining 447 passes/two explicit no-display
Tk skips as history. Unchanged tests all execute in the final 449-pass report.

`volatile_transaction_matrix.py` uses actual SessionStore/ReportIntentStore
methods, fake disk fixtures and private regular files. It covers 10 contexts
(four wanted/not-wanted preference transitions; arm and disarm for all three
methods), eight transaction/fault points, and normal/1-byte/7-byte I/O. Its
240 cases retain 30 normal positive controls and 210 explicit injected-error
refusals. It verifies 120 old-byte precommit preservations, 90 newly visible
postcommit records, 54 uncertain journals blocking further save, 240 fresh
reopens and successful retries, plus 144 acquired quiescence controls. All
native discovery/process/engine/power callbacks are forbidden. A known-stopped
fake pinned-process probe allows explicit fresh-session rotation; authorization
is never restored. There are zero model mismatches or native callbacks.

Faults cover first/middle writes, file sync, replace, directory sync, published
readback and a descriptor close error after the real descriptor is retired.
The matrix is bounded publication/retry evidence, not atomic filesystem CAS,
physical durability, native hardware or real-erase acceptance. Ephemeral signing
test keys remain local fixtures; no production credentials were read or used.

`review-summary.json` is the machine result; XML/log/status files retain actual
runs, `reviewed-source-sha256.json` binds reviewed code, and the model metrics
bind product, fake helper and exact script bytes for independent root replay.
Pinned-browser/network/native/image/physical/reconnect qualification remains
unverified. Ownership is released.
