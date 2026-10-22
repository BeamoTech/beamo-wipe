# Beamo Wipe comprehensive bug audit, fourth pass

Four independently reproduced defects are repaired on
`fix/safety-audit-20261019`, starting from
`7f839e50e63db27a787eeabd758579352b6b3a3a`. The audit began October 19 UTC;
fresh verification after environment restoration ran October 21 UTC
(October 20 America/Chicago). All devices, process/firmware inputs and export
media used here were fixtures or ordinary temporary files.

| Trigger and previous behavior | Final behavior | New cases |
| --- | --- | ---: |
| An authenticated launcher request repeats `confirm` or `revision`; JSON decoding silently lets later values replace consent or review state. | Reject duplicate logical fields, including escaped/case aliases, before any action. Preserve unique aliases, bounds, authentication, revision binding and single use. | 4 Go tests, 137 named subtests |
| A French/German controller exports through a fresh English worker; diagnostics are refused and ordinary owner/sharing report headings become English. | Carry an exact supported language in the private request before locale-sensitive validation and rendering. Preserve original evidence bytes, strict request validation and legacy English requests. | 40 Python |
| S is held during progress, then Escape opens Stop; the next S repeat confirms cancellation. | Remember the hold across modal opening and require a full observed quiet interval before another S can confirm. Preserve fresh keys, other key guards and completion precedence. | 17 Python |
| A validated prior desktop receipt is replaced, edited or linked before retirement; the builder deletes another writer's content. | Compare regular receipt metadata and exact bytes across validation, recheck lock/directory ownership, and refuse changed receipts before compilation. Preserve foreign content and unchanged rebuilds. | 40 Python |

Root independently reproduced every defect before authorizing repairs: prior
receipt 6 failures/2 controls, diagnostic locale 2/3, ordinary locale 2/3,
duplicate restart 3 failing/3 passing named subtests, and curses Stop 1/1.
Expanded baseline failures are retained separately. All **97 new Python
regression/control cases** pass; the separate **4 Go tests and 137 named
subtests** pass with the race detector. Original test assertions were unchanged.
The 20 original external proof cases also pass unchanged after repair.

The fresh complete source gate records **11,057 main cases passed, 28 unchanged
unverified skips, and 1 separate Orca case passed**: **11,058 unique Python
passes**, with no failures/errors. Every one of the 10,988 previous main test
IDs remains; exactly 97 were added, with identical skip IDs and reasons.
The earlier complete run passed with the same identities and results. It is
retained as history and is not added to the fresh run's count. Focused and Go
runs overlap canonical coverage and are not added to that count either.

Configured lint/security/shell checks, default mypy (52 source files), preview,
private negative safety mutation, fresh uncached Go race tests, vet, 350,000
fuzz executions, launcher cross-builds and Windows test cross-compilation pass.
Root checked PE32+/ELF64 x86_64 headers, exact launcher hashes/build receipt
and executable entrypoint modes. The actual fake preview was visually inspected
on a private 72-DPI display and closed through its registered window callback
with exit 0. Its image stays outside Git; the receipt retains its hash.
Actual GTK/Tk focused coverage passed 59 cases. Nine supplemental unchanged
browser assertions passed using explicit system Chromium 155; this does not
qualify the absent Playwright-pinned browser.

Discovery/safety review found no additional proved defect: 1,499 existing
guarded cases, 60 identity scenarios, 500 inventories/1,752 views with zero
cross-disk token collisions, and 3 normal/48 malformed argument controls.
Root's runner/completion/cancellation review passed 1,321 existing cases.
A seeded 5,000-log comparison across three methods initially found four strict
dictionary differences on artificial one-line inputs. Independent review
confirmed only unavailable-check provenance differed; outcome, status, summary
and detail agreed. Both the original strict failure and its disposition are
retained. No parser change was justified.

The frozen manifest records **800** runtime/test/build files, SHA256
`9b4c0e6b0be2153e4349c01a61b813518f834da789e1f206df8db260fc515342`.
It matched before/after both complete runs and after environment restoration.
Run `python3 docs/evidence/bug-audit-20261019-pass4/verify_retained.py` to verify
source and retained artifact bytes, exact JUnit identities, baseline skip
preservation and separate Go results. Earlier audit manifests apply to their
own source snapshots. Proof scripts retain their original workspace paths;
the baseline commit and retained reports identify the source used for red runs.

Intermediate results remain visible. An initial new locale-test draft compared
the wrong output filename; the draft assertion was corrected before the genuine
baseline reproduction. An adjacent report fixture initially failed under umask
0077; a process-local 022 control and the complete 523-case rerun passed without
changing product code or existing assertions. An initial combined proof replay
omitted import paths; corrected paths passed all 20 cases. Agent D-Bus/socket
denials were resolved by root's permitted unprivileged container; no shared
display was changed. Optional builder mypy, outside the configured gate, reports
the same pre-existing Path/str loop-variable error on baseline and final.
The configured lint TODO warning matches a placeholder-detection regex.

The 28 Python skips remain open: 14 generated-image/artifact checks, 9 pinned
browser checks, 4 Microsoft documentation network checks and 1 legacy gcloud
check. Full Go additionally skips native inventory (explicitly not opted in)
and a Windows inventory case (PowerShell unavailable); their names are retained.
On restoration the configured HTTP policy remained restricted, while the
managed status reported enforcement as unknown. No policy or proxy bypass was
attempted. Missing runtimes and network checks are not passes.

Remaining qualification requires the supported environment allowlist update
and pinned browser installation followed by affected checks, then separately
authorized isolated ISO/KVM and native Windows/macOS qualification. Actual
firmware, physical media and physical reconnect/readback remain unverified.
Cross-builds, Python 3.10 grammar checks and fake/virtual fixtures do not qualify
those platforms. Receipt checks do not claim atomic filesystem compare-and-delete.

The retained build receipt records baseline HEAD with `source_dirty=true` during
frozen-source testing. After the local commit, development launchers were rebuilt
from clean HEAD; their final identity is recorded in the external delivery receipt.

No actual nwipe, native disk inventory/mount/write, host power/firmware change,
hosted workflow, PR, merge or release occurred. These fixes and their evidence
are committed locally; remote publication remains pending from the prior
approval review. No remote mutation was attempted during this pass. Full local
operational detail and the final delivery receipt are retained under
`/workspace/beamo-tools/audit-pass4-20261019/root/`; the canonical backlog links
this report and preserves remaining work.
