# Beamo Wipe comprehensive bug audit, third pass

This fresh pass fixes four independently reproduced defects on
`fix/safety-audit-20261019`, starting from
`fa2ca72b648ef373c6215699e883296bc8db551d`. All devices, process/firmware inputs
and recovery media in these checks are fixtures or ordinary temporary files.

| Trigger and previous behavior | Final behavior | New cases |
| --- | --- | ---: |
| Discovery protects boot aliases or system-mounted peers; recovery journal rejects the otherwise valid unrelated-target confirmation. | Journal preserves every protected flag, requires the actual boot protected and the chosen target unprotected, and retains contradictory-context refusals. | 48 |
| Peer inventory changes only during the runner's final under-lock rescan; target/boot-only request loses the wizard's inventory-bound consent. | Authorized requests carry the whole confirmed inventory; changed peers refuse before process launch. Unchanged ordering and legacy target/boot guards remain covered. | 86 |
| Stop signals fail, then the engine exits naturally; cancellation reports an owner abort. | An undelivered stop preserves the actual terminal result. Delivered kill, uncertain liveness and retry ownership retain their existing contracts. | 54 |
| Launcher or receipt changes during final source hashing or receipt publication; builder reports success with an immediately invalid receipt. | Revalidate launcher bytes around receipt creation, verify owned receipt content and metadata across its read, and remove only an unchanged owned receipt on late failure. | 46 |

Root independently reproduced each original defect before repairs: journal
6 failures/3 controls, inventory 3/1, stop delivery 3/6, desktop 4 defects/2
controls. Expanded tests were also run against baseline source. The final
234 new regression/control cases all pass. Original test assertions were not
changed. The UI reviewer found no additional proved defect; its 196 focused
cases include actual GTK/Tk cases on private 72-DPI displays.

The complete final source gate records **10,960 main cases passed, 28 unchanged
unverified skips, and 1 separate Orca case passed**: **10,961 unique passing
cases**, with no failures/errors. All 10,754 prior main test IDs remain and
exactly 234 were added. Focused runs overlap the full suite and are not added
to its count. `final-summary.json` and the compressed JUnit files preserve
exact identities, skip reasons and hashes.

Configured lint/security/shell checks, default mypy (52 source files), preview,
private negative safety mutation, uncached Go race tests, vet, 350,000 fuzz
executions, launcher cross-builds and Windows test cross-compilation pass.
Root verified PE32+/ELF64 x86_64 headers, exact launcher hashes/build receipt,
critical executable modes, and the actual fake preview's normal close at
72 DPI. Nine supplemental unchanged browser assertions pass using explicit
system Chromium; that is separate from the missing pinned browser runtime.

The source manifest contains **796** runtime/test/build inputs. Its SHA256 is
`0a559c0f6f9e60cd082b9b84d669d892f3240987ec7e5ec5ed1b5b2f721b2539`.
It remained unchanged through final verification. Run
`python3 docs/evidence/bug-audit-20261019-pass3/verify_retained.py` from the
repository to verify source and artifact bytes, exact JUnit identities and
unchanged baseline skips. Older audit evidence applies to its own earlier source.

Failed intermediate evidence is retained. The desktop repair's first candidate
changed an existing error message; production wording was corrected without
changing that assertion. Independent review then found receipt edits during a
read could be accepted or removed; four failing cases plus four controls drove
the final metadata-span check. This is a rejected intermediate candidate of
the same repair, not a fifth original defect. Missing-display failures/skips
were resolved using private sessions. An optional `--check-untyped-defs`
diagnostic still reports the same three pre-existing Optional-record errors
on baseline and final; the prescribed default type gate passes. The existing
lint TODO warning is a match inside a placeholder-detection regex, not an
untracked source TODO.

The 28 skips remain open: 14 generated-image/artifact checks, 9 pinned-browser
checks, 4 Microsoft documentation network checks and 1 legacy gcloud CLI check.
Managed policy still excludes the browser/documentation hosts; it was not
bypassed or changed. Generated ISO/KVM, native Windows/macOS, actual firmware,
physical media and physical reconnect qualification remain unverified.
Cross-builds, grammar checks and virtual/fake fixtures do not qualify those
platforms. Final receipt checks do not claim atomic filesystem compare-and-swap.

No actual nwipe, physical inventory/mount/write, host power/firmware change,
hosted workflow, PR, merge or release was performed. These locally verified
changes are prepared for the existing feature branch. Public delivery is pending. `delivery.json`
records the delivery boundary; the exact local/pending-publication Git/ref/status receipt
is `/workspace/beamo-tools/audit-pass3-20261019/root/final-delivery.json`.
The canonical backlog preserves remaining acceptance work.
