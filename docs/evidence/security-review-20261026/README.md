# Security review - 2026-10-26

This is the historical `b7c49d9`-based review record. The later integrated
checkpoint and cross-machine resumption procedure are in the
[current handoff](../../security-review-handoff.md). Its checks must be read
at their recorded source identities; they do not qualify the integrated tree.

**INCOMPLETE / REQUIRED GATES BLOCKED.** Four confirmed defects have source
corrections and focused regressions. This review does not qualify a release,
the live image, a physical USB, or a real erase. Do not commit or push this
candidate as accepted until the outstanding checks below are resolved.

The requested source is `BeamoTech/beamo-wipe`, isolated branch
`codex/security-review-20261026`, based on
`b7c49d949d1dc75eecabdb24ffa534779f674ec3`, tree
`2479bbce0b98a2d51a6f68d628edce03acb7ede6`. The working changes are uncommitted.
The separate October 24-26 broad-audit worktree was preserved; its fixes and
receipts do not qualify this source. Current repository/shared instructions,
claims, development/remote guidance and the current Lab guide were read.
Current CI is Blacksmith/GitHub Actions; the supplied legacy GCP description
does not authorize invoking retired Cloud Build routes.

The baseline census contains 727 tracked functional files. Its recorded
identity is `91bfc39c345f26edba0da21d5f88b01cf52de0c9e717807bcbf35196ec756044`.
The final 729-file census includes the two new regression modules and excludes
documentation, memory, ignored environments and generated evidence. Its
compact sorted-JSON identity is
`d2c2cb5e5f4a91c25aa9263115db885c67055d1269cfb41c304e3979a65feb6e`;
the serialization is defined in the retained `static-final.py`. This is a
dirty-source identity, not a new Git commit or artifact identity.

## Confirmed findings and corrections

| ID / severity | Confirmed behavior at the baseline | Correction and regression |
| --- | --- | --- |
| SEC-01 / P1 | A later damaged target-progress update can leave an earlier final sample available as completion proof. A decimal above 100 can also round to 100 in binary floating point. Fake logs reproduce false successful completion across all three methods. No incomplete real erase was executed. | Attribute damaged progress independently of parsing, invalidate stale completion samples, and require exact decimal 100 for terminal proof. Preserve independent validated Erased-table proof. See [terminal regressions](../../../tests/test_security_terminal_progress.py). |
| SEC-02 / P2 | A damaged progress update can fail to contradict a busy/open/geometry skip report, supporting a misleading outcome classified as nothing erased. | Treat attributed damaged target progress as activity uncertainty independently of valid completion counters. The existing outcome evaluator then refuses the nothing-erased conclusion. Same regression module. |
| SEC-03 / P3 | Replacement decoding expands retained invalid UTF-8 from the 1 MiB raw budget to about 3 MiB returned UTF-8. Deferred progress can bypass accounting as well. Expansion is bounded; this is not an unbounded-memory claim. | Charge normalized UTF-8 plus separators for every retained and deferred record; return indeterminate when the projection exceeds the cap. Exact-limit ASCII remains accepted. Same regression module. |
| SEC-04 / P2 | Real live startup failure constructs a fallback runner while remaining live. A runner-type exemption skips the external-engine query, allowing the modeled final power handler to proceed for busy, unknown or failed inspection. | Remove the runner-type exemption. Preserve dry-run/preview exclusions and fail-closed unknown/error handling. See [startup power regressions](../../../tests/test_security_startup_power_guard.py). Every probe and power callback in the reproduction was fake. |

Production edits are limited to `nwipe_runner.py` and `wizard.py`. They do not
change disk selection, boot exclusion, owner/token/countdown authorization,
engine arguments, method mapping, dependency pins or claims. The 30 terminal
and 11 startup-power regression cases are written for the normal Linux suite.
They have not been executed as actual Linux pytest cases.

Three existing report/startup test fixtures now explicitly model an absent
external engine. Standalone engine guards remain fail-closed. AST comparison
preserves all 128 original definitions except the documented setup addition
to the `blocked` fixture, and all **314 original assertions** unchanged.

## Verification and evidence level

| Check | Actual result | What it establishes |
| --- | --- | --- |
| Corrected-baseline completion reproduction | Exit 1; 15 mismatches in 24 cases | Causal baseline failure, including all methods and activity conflicts. An earlier incorrect geometry fixture remains retained separately. |
| Corrected completion probe | Exit 0; 24/24 matching | Exact parser/scanner AST with fake POSIX paths, metadata and log I/O. |
| Projection budget pair | Baseline exit 1, two failures/three controls; corrected exit 0, 3/3 | Normalized/deferred budget refusal and exact-limit ASCII control. |
| Startup/power pair | Baseline exit 1, four mismatches/16; corrected exit 0, 16/16 | Fake probe/power boundaries. Three baseline mismatches allowed uncertain/busy poweroff; the fourth failed to perform the required clear-engine query. |
| New regression-body replay | Exit 0; 41/41 | Unchanged bodies of all new parameterized cases, extracted with fake OS/FD/path/process/power adapters. Not actual product-module/Linux pytest execution. These overlap the focused probes above. |
| Portable Windows developer-tool gate | Exit 0; 77 passed, 3 existing skips | `py -3 -B dev.py test --native` in a new checkout-local environment. Two POSIX descriptor cases and one legacy POSIX script case remain skipped on Windows. Not the live wizard or native launcher binary. |
| Full Ruff and both prescribed security selections | Each exit 0 | All production Python and tests satisfy the project's applicable Ruff rules. |
| Final mypy | Exit 0; 52 source files | Linux 3.11 typing stubs from the existing read-only tool environment. Existing notes identify unchecked untyped bodies in `audio_jobs.py` and `session_recovery.py`. Not native Linux execution. |
| Python syntax and preservation | Exit 0; 575 files compiled without execution | Tracked Python plus new tests parse/compile; fixture assertions preserved; production change scope checked; `git diff --check` passes. |
| Signature/privacy composition | 29 distinct cases resolved | Actual pure signing/privacy modules on Windows with cryptography 50.0.1, ephemeral in-memory test keys and fake identifiers. Initial exit 1 had 28 passes and one adapter diagnostic mismatch; a one-case unchanged-source replay exited 0 and confirmed explicit duplicate-JSON refusal. No extra cases credited for the replay. |
| Python advisory inventory | Exit 0; 15 exact public package/version pairs, no reported vulnerabilities | pip-audit 2.10.1 against explicit installed-tool and declared dev/CI pins. The first query warned about unhashed inputs; a final query used official PyPI release-file hashes and exited 0 without that warning. No dependencies were resolved or fixed and no advisories were suppressed. This does not qualify the complete Linux graph, installed wheel bytes or Debian image. |
| Launcher JavaScript syntax | Node `--check`, exit 0 | Static launcher script parses; no browser API, firmware or restart action exercised. |

No aggregate test count is claimed across overlapping model runs. The selected
Windows Python initially lacked pytest (doctor exit 1/BLOCKED); a new
checkout-local native environment fixed that prerequisite. Setup and repeated
doctor exited 0. Other check prerequisites were not relabeled as passes.

Private working evidence is under
`C:/Users/Jack/beamo-release-evidence/security-review-20261026`. It retains
before/current source, commands, actual exits, failed adapters/inspection
attempts, bindings, manifests and readback. `verification.json` supplies a
compact record. `packet/` is the sealed handoff, with its manifest/readback
receipt; cache directories and native temporary fixtures are outside the
sealed payload and are not acceptance evidence.

Lab doctor, sync, plan and report commands and their verifiers exited 0 at
Lab source `d3d0959bb26b17531464dbd1ba233d4d842ad581`. They establish preparation
and receipt integrity only. Exact product adapters do not qualify this dirty
source. The offline report loaded with the expected title, but two browser
snapshots timed out. The computer-use fallback found no targetable browser
window; its API cannot request a fresh profile, and Lab forbids personal-profile
reuse. Visual QA remains incomplete. The temporary loopback-only report server
was explicitly stopped and exited 0; it served only the report bytes.

## Reviewed trust boundaries and coverage limits

Source review covered argv allowlists and subprocess environments; explicit
owner/token/countdown and separate start action; final rediscovery and boot
exclusion; local whole-device classification; private volatile logs, ownership
and symlink checks; diagnostic redaction and support codes; export metadata,
FAT32 mount options, private namespace, readback and receipts; session recovery
and power guards; launcher HTTP Host/Origin/token/JSON/plan checks and inert
preview boundaries; release signatures, active trust keys, rollback floor,
transfer inventories and publication ordering; build quoting and pinned
inputs; kiosk entrypoint, fixed boot choices, root-owned assets, tmpfs and
systemd restrictions. Search and syntax coverage are not a line-by-line proof
of every reachable path. No additional confirmed injection, traversal,
privilege escalation or key-disclosure finding was established in this pass.

Runtime enforcement of permissions, symlinks, mount namespaces, process
ownership, signal delivery, actual boot assets, package versions and firmware
policy still requires the relevant native/image tests. Root is necessary for
the shipped block-device operation; source service hardening is not evidence
of isolation from a hostile same-UID/root process. No real disk identifiers,
production private keys or raw customer erase logs were used in the probes.

## Dependency review and remaining acceptance

The explicit Go 1.26.8 pin remains unchanged. Go 1.26.9 and 1.26.10 include
later security fixes. [Official Go release history](https://go.dev/doc/devel/release).
For example, GO-2026-6809 affects `crypto/x509.Certificate.Verify` before
1.26.10. [Official advisory](https://pkg.go.dev/vuln/GO-2026-6809).
The inspected launcher is a plain HTTP loopback server; TLS/HTTP2 and outbound
proxy advisory reachability was not established. This is an unresolved
dependency assessment, not proof that a particular launcher exploit is
reachable. Exact-source/artifact vulnerability and callgraph checks plus any
authorized pin decision remain required.

The cryptography 50.0.1 pin is later than the 50.0.0 fix for the specifically
checked PKCS#7 advisory; signing here uses Ed25519, not that decryption API.
The bounded Python advisory inventory found no known issue in its 15 exact
package/version pairs. It does not constitute a complete dependency scan.
[Upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5).
Debian's Xorg tracker lists open bookworm issues, but no candidate image/package
database was built in this task. Installed-package attribution remains unknown.
[Debian security tracker](https://security-tracker.debian.org/tracker/source-package/xorg-server).

Before acceptance, run the applicable full Linux pytest with GTK/Orca and
72-DPI Xvfb, real-module focused regressions, preview, ShellCheck, remaining
format/type/security gates, negative safety mutation, pinned-Go race/vet/fuzz
and native launcher checks, vulnerability scans, ISO inspection and the entire
isolated x86_64 BIOS/UEFI/QEMU matrix. Preserve each phase's receipt and exact
source/config/artifact binding. No suitable isolated worker has been supplied;
Go and ShellCheck are not on this task's PATH. No WSL/host/firmware or physical
device workaround is authorized. Unavailable gates remain BLOCKED/NOT RUN.

The next useful action is to supply the name/access reference for an existing
approved isolated x86_64 Linux worker with no host-disk passthrough. Review the
Go advisory reachability there before deciding whether the explicitly frozen
pin needs separate authorization to change. A newer source or artifact must
be rebound and reverified. No staging, commit, push, hosted dispatch, release,
production key operation or physical media action was performed. Task119
remains **NOT TESTED/BLOCKED** under its original physical prerequisites.
