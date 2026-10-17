# Pass21 runner, report, recovery and build source review

Date/author: 2026-10-17 20:53 UTC / Codex delegate `/root/pass21_runner_reports`.
Repo `BeamoTech/beamo-wipe`; branch `fix/safety-audit-20261015`; commit
`35107a8d1a701093eac876a58ab4efd50e291673`; worktree `/root/dev/Beamo Wipe`.
This is a source-only review of the existing dirty pass20 state. No app imports,
tests, displays, devices, inventory, signals, mount helpers, guests, hosted jobs,
network, commits, pushes or publication were run by this delegate. Source/tests
were not edited. The parent owns runtime validation and acceptance.

## New candidate BW-P21-DIAGNOSTIC-SEPARATORS — PREPARED / UNPROVED

`diagnostics._sanitize_detail` maps Unicode C* categories to spaces but preserves
U+2028 (Zl) and U+2029 (Zp). `log_diag` serializes with `ensure_ascii=False`, while
`read_diagnostics` uses `str.splitlines()`. An event accepted and written as one
valid JSON document can therefore be split inside its JSON string by the public
reader, which silently discards both fragments. The same sanitizer feeds stderr
fallback, whose message then occupies multiple visible lines. The declaration
that diagnostics are sanitized and single-line does not hold for these inputs.

Prepared proof `diagnostics-unicode-boundary-probe.py` SHA256
`7ac355a282ea210431914c5dd9798520ee86604bd343a89dfcbe0c497013f578`.
29 cases: 16 writer/reader round trips (two separators across area, code, detail,
device, logfile, request_id, extra key/value); two sanitizer cases; two fallback
cases; eight existing control-separator controls; one normal Unicode/order/limit
control. No runtime result exists yet. Source predicts 20 failing assertions and
nine controls; this prediction is not verification. Every file touched by the
proof is an ordinary private pytest temporary file; the fallback uses a missing
subdirectory and captured stderr.

Acceptance: root executes the unchanged probe against authenticated current
source and records exact failures/controls; apply a minimal sanitizer correction
only if demonstrated; rerun original cases, existing diagnostics/privacy tests,
and applicable local gates. No safety gate or method/argv behavior should change.
Likely correction is to replace Zl/Zp with spaces alongside C* categories, rather
than alter the JSONL framing or suppress the reader's failure. Parent must review.

## Boundaries checked with no additional defect established

- Runner launch: duplicate rejection before truncation; final identity checks
  under exclusive lock; inherited lock; uncertain Popen ownership retains lock;
  request identity bound to active process and no terminal publication before
  confirmed cleanup.
- Progress/completion: complete LF records, target-specific counters and known
  phases, final pass/method denominators, exact Drive Status banner, conflicting
  skip/activity/failure/error rows, bounded tail identity and large-log projection.
- Cancellation: status-probe ownership, pre-signal natural completion, terminate/
  kill waits, live uncertainty preserving process/lock, stale poll result guards,
  large-log warning assessment, successful natural completion retained.
- Reports: baseline required/optional identities, WWN/serial ambiguity, fresh
  protected descendants, two scans on each side of private worker boundary,
  parent/partition rdev proof, immutable evidence/log suffix, one new FAT32 USB,
  exclusive file creation, completion marker after content sync, read-only
  remount/readback and exact safe-to-remove receipt.
- Recovery: interface and wipe inode ownership, immutable journal envelope,
  source/boot/session provenance, arm/preflight distinction, quiescent process
  check, terminal identity/timestamp/log evidence corroboration. Stored state
  contains no authority to resume or restart erasure.
- Diagnostic report schema: strict fields/duplicates/depth failure handling,
  identity allowlist, no raw logs/serial exports, monotonic and unverified wall
  clock declarations. Result-summary HTML escapes values and plain text flattens
  controls and visual separators.
- Build scripts: private regular-file ISO snapshot and final manifest digest,
  extraction rejects links/special entries, FAT/MBR/readback, staging/output inode
  ownership and no-overwrite publication, cleanup only owned current inodes.
  `identify-boot-usb.sh` delegates to Python identification. Canonical local
  tests retain separate Orca and main reports; negative safety uses private copy.

These observations are source review, not a claim of executed boundary coverage.
Existing pass20 gate/campaign evidence remains distinct and is not reused as a
fresh pass21 run. Python 3.11/live bookworm, ISO/QEMU, native Windows, firmware,
physical reconnect/readback and hardware remain untested/blocked here. No old
SIGTERM, native abort or GTK timing incident is attributed by this review.

## Reviewed input SHA256

| Input | SHA256 |
|---|---|
| `nwipe_runner.py` | `465d3495bd36b3be2507798ad3b57930645c165ba025a2afbe2ea0ca6c45e39d` |
| `support_export.py` | `23308f130079eb98cc8f77c597e227efbbf1cdb06234dd1336b2e034660bcc04` |
| `session_recovery.py` | `128c5daa4c53197437682c637d3078917a79037a9edf5d1796fc9916cdd4ba53` |
| `report_intent.py` | `f147d8840ae6f8f9d58d07111b2f6c4db9e8792e1e30beb1f96f82afdb482c25` |
| `diagnostic_report.py` | `fc01e84c6f917d679ea743bc104c5c5d6031de34bd9d68b6f6ee43f63986a1dd` |
| `diagnostics.py` | `274af6f2c094f2a2320cf26025f6fde4de463e47324aba8298ea1e96da8f9963` |
| `evidence.py` | `512c9b024b3231bf2625b6c802a8dc2282c275153b62e2995d4d01ba9466b5c5` |
| `engine_checks.py` | `858da2ba9ac347df0b4a92bc196e90949d4279f155e21c98f0ac01b8caa743f3` |
| `outcomes.py` | `4af35b516e728d1b46fd8b242346c7ded29e61a0bbb9e827a617d155267bd8ba` |
| `result_summary.py` | `b059c558e913348887a24b2ade36b8e34bfa01aa7acb1e64ee8a47e996cdb430` |
| `privacy.py` | `bcb9c6ce4764a7e6df54b970aede4003c3f90357535fc42530b831eeef0face2` |
| `sleep_inhibit.py` | `b7df5b80f7d87ae0bcac0be2ddcf082ff887e5492fb8da088237b5b02a9bf11d` |
| `recovery.py` | `2c9d7994872173b92225efb953d48ad25e3a77c4824632530b400d86005f5aa7` |
| `scripts/build-iso.sh` | `e5fc440e065fbb33ea1d6a580584aa0537390ba92e60e3cd331e9622cfb48a00` |
| `scripts/build-usb-image.sh` | `0d1be5f4154bf1fa84c75c6e9dd385696a0ff44eda42fd66479f69f0beca984f` |
| `scripts/identify-boot-usb.sh` | `8537f456c4c9b6d86f2c9e3cb9c82e9f2b3a8c933f18c345e86091a6086dd31f` |
