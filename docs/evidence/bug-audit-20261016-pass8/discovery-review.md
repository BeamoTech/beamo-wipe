# PASS8 discovery/safety independent audit

2026-10-16 / Codex reviewer. Baseline35107a8. No source/test changes made.

Reviewed discover.py, safety.py, identity.py, inventory.py and read-only argv/method boundaries in nwipe_runner.py/methods.py against AGENTS.md, unfinished work, ADVANCED.md and fail-closed requirements. Fresh investigation examined tree/flat ownership reconciliation, mounted holders/filesystem members, duplicate paths/metadata, boot source precedence and ambiguous identity, whole-disk/optical/remote refusal, raw-vs-display identity, token uniqueness, strict authorization booleans, rediscovery binding, byte-size handling and log/transport refusal.

No new reproducible actionable defect found in this bounded scope. This does not establish global bug freedom or native acceptance.

Verification:
-542 existing tests across46modules PASS, zero errors/failures/skips; private Xvfb72DPI and D-Bus. JUnit and raw log retained.
-756 controlled discovery cases PASS:256 malformed field observations checking boot/path fail-closed invariants,28 observed mounts,36 remote/unknown transport refusals,7duplicate identity refusals,100bad→good retries,320concurrent independent scans,7changed identity refusals, unchanged identity control and fake production PermissionError refusal.
-5000 seeded inventories (seed381871):9753usable token specs/5276 ambiguity refusals, all usable tokens unique across distinct disk paths, no kernel-name tokens.102 argv mutation/control cases PASS for all3methods; changed method/verify, missing/duplicate flags, boot exclusions, extra targets, control chars and force refused.
-900authorization combinations:6normal controls accepted,894refused. Owner/countdown require exactTrue, missing/boot selection and wrong token refused. Every physical/log-creation boundary stubbed.

Boundaries: injected inventory and sources only. Matrix guards prohibit /proc/cmdline and /proc/self/mountinfo reads and lsblk/findmnt/nwipe execution. Focused suite substitutes fake findmnt exit1 and empty fake /proc when predecessor tests omit injection; counts16/2/2 recorded. No real inventory, nwipe, disk operation, guest, hosted CI or network action.

Harness history retained: first focused wrapper blocked findmnt before2intended lsblk error tests;1GTK case lacked DISPLAY. Retained setup-failed raw/JUnit; corrected fake findmnt plus private72DPI replacement passes all542. First token draft included control-containing serial in a normal-data generator; production parser correctly raisedValueError. Retained setup-failed log, removed invalid control fixture only from normal token generator; malformed controls separately covered. These are harness setup failures, not product findings.

Files under /tmp/beamo-pass8-discovery-* include all scripts/raw logs/JUnit and exact source hashes in review.json. Counts overlap repository full gate; do not add them as unique passes. No real-device/ISO/QEMU/nativeWindows acceptance performed.
