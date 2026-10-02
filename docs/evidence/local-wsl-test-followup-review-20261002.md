# PR #84 setup review follow-up — 2026-10-02

[PR #84](https://github.com/BeamoTech/beamo-wipe/pull/84) continues the
[original local preparation](local-wsl-test-followup-20261002.md).
Base for this correction: `2d82ec23b3b6f5ed595e98428980e2f1a46e7895`.
Use `git log -1 --format=%H -- docs/evidence/local-wsl-test-followup-review-20261002.md`
to identify this follow-up revision.

Greptile correctly found that `.cursor/install.sh` declared `xvfb` but not
`x11-utils`. Cursor Cloud's full local test route also executes the private
Orca startup and therefore needs `xdpyinfo`. The required-package array now
includes `x11-utils`, so the installer's existing missing-package check and
required installation transaction handle it. The optional Docker path and
test execution policy are unchanged.

The existing setup regression now checks hosted installation, documented
local installation and Cursor's **required**, rather than optional, packages.
Fresh Linux checks after this change: **22 passed**, zero skips/failures, 2.53 s
for the lifecycle/JSON modules; Ruff, Bash syntax and ShellCheck passed.
The runtime helper, production code and previous 5,623-pass local suite's
safety/GTK behavior are unchanged. A fresh full required hosted run must
qualify this updated revision before merge; the first PR run cannot do so.
Actual Cursor VM provisioning was not executed in this Windows/WSL session.

The maintainer explicitly authorized this PR, required Blacksmith CI and
merge after passing checks. Push-triggered qualification replaces the
superseded PR run; no duplicate manual dispatch or production release is
authorized or needed. Raw review-fix output and integration records are in
the operator's `BeamoWipe/local-verification-followup/20261002T175829Z-pr84-integration/`
audit. Physical #119 remains **NOT TESTED**, with physical access unavailable.
