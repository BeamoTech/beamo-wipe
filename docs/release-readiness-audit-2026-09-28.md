# Release readiness audit — 2026-09-28 UTC

Audited source: `e8dc56a38dc987cfbf40048fd27070c6c8ddd2b4` on `main`, initially clean. This report consolidates the initial audit and the requested second review. This was a review, not a fix or publication request. No runtime source, disk-selection rule, engine flag, remote setting, release, or physical disk was changed. The initial audit date in America/Chicago was 2026-09-27.

At final checkout verification, a concurrent `AGENTS.md` cost-policy edit was present. This audit did not make or alter it. Its general provider preferences retain project mandates; the project's current Blacksmith workflow and specific CI instructions remain the basis for R7.

**Second-pass assessment:** retain only changes backed by demonstrated behavior, a direct mismatch with an existing requirement, or a verified release-evidence gap. Eleven items pass that threshold. The audio responsiveness defect and physical qualification gap are the highest priorities. The synthetic large-log case from the first pass does not establish a shipped-engine defect and is excluded from the improvement list. Correct implementation of any change still needs verification; this report does not assign artificial percentage guarantees.

| ID | Priority | Improvement | Evidence type |
| --- | --- | --- | --- |
| R1 | P1 | Keep audio work off the UI event loop, especially during erasure | Source trace and fake-backend execution |
| R2 | P1 | Complete physical acceptance for the configurations to be advertised | Unexecuted acceptance records and public manifest limitation |
| R4 | P2 | Include the already-merged kiosk/support fixes in the next qualified release | Published manifest compared with Git history |
| R5 | P2 | Enforce the documented pull-request review requirement | Current GitHub protection API |
| R6 | P2 | Correct the physical Secure Boot test expectations | Contradictory active test instructions |
| R7 | P3 | Remove obsolete Google Cloud CI instructions from development entry points | Current developer guide and doctor output |
| R8 | P3 | Fix the two broken documentation links in the public release notes | GitHub-rendered release HTML |
| R9 | P3 | Make the release manifest describe publisher signing accurately | Public signed manifest and successful signature verification |
| R10 | P3 | Apply the existing GTK dependency skip consistently in two local tests | Repeatable missing-dependency failures and source trace |
| R11 | P3 | Clean up the negative-gate test's owned subprocess on timeout or exception | Unprotected Popen/communicate lifecycle |
| R12 | P3 | Document verification of the compressed USB image actually published | Public download inventory compared with consumer instructions |

P1 means address before broad customer release. P2 means include in the next release or its qualification process. P3 means a concrete correction with lower immediate runtime impact. These priorities are audit judgments, not claims of observed customer incidents.

**R1 — Audio can delay Stop and progress updates.**

The Working screen offers “Hear sounds.” Tk invokes `Wizard.hear_both_sounds()` directly from its button callback; the console invokes it directly from its input handler. Each sound synchronously discovers the output, queries its settings, starts/checks PulseAudio, and runs the player. `play_outcome()` also performs synchronous discovery/startup despite its “Never blocks” docstring, so automatic sound can delay rendering the final result.

A fake audio backend, with no real subprocess or device access, recorded twelve calls on `MainThread` for the console Working-screen action. The artificial calls took 0.426 seconds total. Their sequential configured timeout budgets total 70 seconds; that is not a measured 70-second hardware stall, and earlier failures can return sooner. The demonstrated problem is that the input/event loop cannot process Stop or refresh progress while those calls run. The engine continues independently.

Move discovery, daemon startup, and playback to a bounded worker; prevent overlapping tests and ignore stale callbacks after a session change. Keep Stop and progress polling responsive. Verify with a deliberately blocked fake backend, including automatic Done sound and repeated clicks.

Source: `src/beamo_wipe/sound.py:157,256,343,354`; `wizard.py:3031,3077`; `ui/tk_wizard.py:3824`; `ui/console_wizard.py:1955`.

**R2 — Physical customer workflows remain unqualified.**

The physical acceptance packet and the Windows/Linux desktop-to-USB checklist still mark their cases **NOT TESTED**. The public 0.2.11 manifest explicitly retains physical handoff and Secure Boot acceptance as known requirements. The observed native Windows gate uses Windows Server 2025 fixtures; it does not establish the advertised Windows 10/11 customer journey. QEMU establishes virtual guest behavior, not actual USB controllers, storage firmware, panels, input devices, or lid/power behavior.

Run the applicable existing matrix against the exact candidate image, on named PCs and disposable, explicitly authorized target disks. Record image hash, firmware/trust state, ports/controllers, target identity, result/export readback, and failures. Cover the hardware and OS combinations actually intended for sale; narrow unsupported or untested claims instead of presenting them as passed. Include the manufactured FAT USB's desktop files/launchers, boot-USB exclusion, ordinary cancellation, accessibility/audio, and report removal. Independent physical readback must accompany any claimed physical erase result.

Evidence: `docs/evidence/physical-acceptance-111/README.md:8`; `docs/desktop-hardware-acceptance.md`; public manifest `known_issues`. No physical acceptance was attempted in this audit.

**R4 — The latest public image does not include the current recovery fixes.**

The published 0.2.11 manifest names source `662cf470f9fcedf710d897591560267575745fea`. Current `main` additionally contains the kiosk fixes in `40b71da` and `6c9ff6f`: a single terminal EOF no longer strands recovery, persistent terminal failures preserve readable guidance, and uncertain runner cleanup receives support guidance. It also contains `9b12967`, which fixes draft-release lookup during publication.

Qualify and publish a new version containing the intended current fixes plus accepted audit fixes. Keep 0.2.11's immutable assets intact. A pass on current `main` cannot be described as proof that the already-published 0.2.11 contains these changes. Publication remains a separate authorized action.

Evidence: [public 0.2.11 release](https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.11), its signed manifest, and `git log/diff v0.2.11..e8dc56a`.

**R5 — Required review is documented but not enforced.**

The read-only GitHub API check found strict, app-bound `CI gate` protection on `main`, including administrator enforcement and blocked force pushes/deletion. However, the response has no `required_pull_request_reviews` rule, and the repository ruleset list is empty. `docs/ci.md:98` explicitly calls for pull-request review.

Configure an appropriate required-review rule to match that documented policy, and verify it through the API. This is a process-control mismatch; it does not mean the CI gate is absent or that any particular merged change was unreviewed. The production environment currently restricts deployment to protected branches; this audit does not infer a separate mandatory environment-approval requirement.

Evidence endpoints observed during the audit: `GET /repos/BeamoTech/beamo-wipe/branches/main/protection`, `GET /repos/BeamoTech/beamo-wipe/rulesets`, and `GET /repos/BeamoTech/beamo-wipe/environments/production`. No settings were changed.

**R6 — The physical Secure Boot test procedure has obsolete expected results.**

The physical packet's completion criteria and step 5.3.4 expect firmware to reject the USB whenever Secure Boot is enabled without an enrolled Beamo key. Current product guidance instead describes Debian-signed boot files whose acceptance depends on firmware trust/revocation state; the current desktop acceptance checklist expects boot on a supported Secure Boot configuration. These instructions could classify a regression as a pass or a supported boot as a failure.

Update the active lab procedure and relevant matrix rows to distinguish supported trust states from expected refusal states. Record actual firmware trust and revocation conditions. Preserve old executed receipts as dated history rather than rewriting their results.

Source: `docs/evidence/physical-acceptance-111/README.md:26,122` and `results/firmware.md:13,21`; compare `src/beamo_wipe/compat_story.py`, `docs/desktop-hardware-acceptance.md`, and the current QEMU Secure Boot gate.

**R7 — Developer instructions still send maintainers to obsolete CI.**

`docs/development.md` labels Google Cloud Build as the full acceptance route and instructs maintainers to authenticate gcloud and run `scripts/ci-cloud.sh`. `dev.py doctor` likewise says gcloud is needed for the full amd64 gate. Both contradict the current Blacksmith route in `AGENTS.md` and `docs/ci.md`.

Update the environment table, full-build command, troubleshooting wording, and doctor message to point at the canonical Blacksmith workflow. Keep legacy tooling clearly marked as historical. This prevents wasted authentication/build work and use of the wrong qualification process.

Source: `docs/development.md:12,132,150`; `dev.py:126`; compare `docs/ci.md`.

**R8 — Public release documentation links are broken.**

GitHub renders the release body's relative links as `/BeamoTech/beamo-wipe/blob/v0.2.11/storage-and-controller-limits.md` and `/BeamoTech/beamo-wipe/blob/v0.2.11/release-verification.md`. Both documents actually live under `docs/`. They work in the source Markdown's directory but fail when the same text is used as the GitHub release body.

Use links that resolve correctly in both contexts, preferably absolute links pinned to the release tag, and validate the rendered release body before promotion. Correct the current release description through the normal authorized publication workflow; binary assets need not change for a text-only correction.

Source: `docs/release-0.2.11.md:18`; `scripts/publish-release-blacksmith.sh` passes the notes file to GitHub. Observed rendered body: `GET /repos/BeamoTech/beamo-wipe/releases/tags/v0.2.11` with GitHub's HTML media type.

**R9 — Signed release metadata claims signing is unconfigured.**

`generate_manifest()` unconditionally emits `verification.signing = "not configured; SHA256 detects corruption but does not authenticate the publisher"`. The downloaded public 0.2.11 manifest contains that text even though its detached signature successfully verified against the repository's active key registry. Verified key ID: `93caaf7ca93eff4d`; exact manifest SHA-256: `baa45ec47162388fdd9f8d441084977ee93e0215b1b4fcf2330df6b7e58a3b98`.

Make the metadata accurately describe the detached-signature verification requirement, including the distinction between preliminary build provenance and a published signed release. Add a release-contract assertion so the misleading text does not recur. This finding concerns metadata accuracy; the checked signature was valid. Do not alter an already-signed immutable manifest in place.

Source: `src/beamo_wipe/release_manifest.py:496`; public 0.2.11 manifest and `.sig`; `packaging/release-keys/keys.json`.

**R10 — Two local GTK tests bypass the existing dependency skip.**

Two GTK/ATK tests import `gi` directly before reaching the existing GTK helper's skip mechanism. Both fail with `ModuleNotFoundError` on this documented Mac development setup, while the rest of the GTK-dependent suite explicitly skips. Reuse a platform/dependency fixture for these tests, preserving mandatory GTK execution in the supported Linux gate.

Source: `tests/test_compat_story.py:310`; `tests/test_separate_footer_actions.py:98`; compare `tests/test_accessible_runtime.py:15` (`pytest.importorskip("gi")`). Verify that these tests skip cleanly on the documented Mac development setup and still execute under the required Linux GTK/ATK gate.

**R11 — A timed-out negative-gate test can leave its child running.**

`test_negative_gate_mutates_only_private_source` launches `bash scripts/ci-hosted.sh negative`, polls for a marker, then calls `communicate(timeout=30)`. There is no `finally` cleanup if that wait, the marker inspection, or a prior read fails. A `Popen.communicate` timeout does not itself terminate and reap the child. This failure path occurred during the first audit's local checks.

Give this test bounded cleanup of its own process and owned descendants, preserve bounded diagnostic output, and verify the cleanup path with a harmless slow child. Do not kill unrelated processes, extend the safety-check timeouts, or weaken the negative assertion. This recommendation concerns deterministic resource cleanup; it does not assume a cause for the intermittent timing failures.

Source: `tests/test_boot_pipeline_pass5_negative.py:66` and `:81`; negative child execution in `scripts/ci-hosted.sh:189`.

**R12 — The consumer verification guide omits the downloadable USB image.**

The public 0.2.11 release publishes `.img.gz`, its checksum, raw-image metadata/checksum, and a separately signed `release-downloads.json`. That inventory binds both compressed and raw image hashes to the qualified source/build. The canonical verification guide's artifact table lists only the raw `.img`; its consumer commands verify the ISO and ISO manifest. It provides no procedure for authenticating the download inventory or checking the compressed USB image and decompressed bytes. The old 0.2.8 notes mention gzip, but do not supply this missing authentication procedure.

Extend the existing guide with the actual asset names and a copyable verification sequence using the trusted key registry and existing signature verifier, then validate the requested version/source, compressed hash and size, decompressed raw-image hash and size, and metadata's ISO binding. State one consistent working directory or use explicit source/download paths: the current signature example says to run in the release directory while importing `src` and opening `packaging/release-keys/keys.json` relative to that same directory. Clearly distinguish downloadable `.img.gz` from the reconstructed `.img`. This is a documentation correction using the existing publication mechanism, not a proposal for another signing system.

Source: `docs/release-verification.md:5,124,214`; `docs/release-0.2.8.md:7`; `scripts/prepare_release_assets.py:89,116`; `scripts/publish-release-blacksmith.sh:63`; downloaded public `release-downloads.json`. Its detached signature also verified against active key `93caaf7ca93eff4d`, with acceptance floor `0.2.11`; exact inventory SHA-256 is `b316027eef91dc8552bfe7433ba8fe4bbdcf081e12e7fec7177943592605b94f`. The large image bytes were not downloaded or independently verified during this audit.

**First-pass recommendations excluded or narrowed by the second review**

- **R3 is excluded from the actionable list.** The synthetic check remains reproducible: a valid target completion row followed by more than 1 MiB of ordinary trailing messages gives a verified live result but indeterminate recovery and refused export. However, the exact pinned nwipe source joins wipe/temperature workers before emitting its final Drive Status summary, then emits final status/cleanup. Beamo disables PDF reports and discards process stdout/stderr. This review did not establish a normal shipped path producing the required trailing megabyte in the logfile. Reworking authenticated completion storage on that evidence alone does not meet the requested near-certain practical-improvement threshold. Preserve it as an unqualified edge-case observation, not a release blocker. Sources: [pinned nwipe.c](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c#L1342), [pinned logging.c](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/logging.c#L987), and `src/beamo_wipe/nwipe_runner.py:386,1139,1263,1389`; first-pass consumers at `evidence.py:552` and `support_export.py:1496`.
- **R10's broad timeout recommendation is removed.** The first full suite timed out five subprocess cases and encountered one sandboxed Unix-socket denial. Focused reruns resolved the socket and three timeout cases; the remaining two cases passed together with plugin autoload disabled (2 passed in 20.15 seconds). An instrumented evidence-reader child completed in 0.248 seconds. The second full suite, outside the sandbox with plugin autoload disabled, failed only the two GTK imports. These conditions do not identify a particular plugin, prove a production reader hang, or justify larger timeouts. Keep only the independently proven GTK skip correction (R10) and missing owned-child cleanup (R11).
- **R5 is limited to the existing documented review policy.** Do not invent extra mandatory production-environment reviewers or weaken the already enforced CI gate. R2 is similarly limited to physical configurations and claims actually intended for release.

Original IDs are retained for traceability; the gap at R3 is intentional. R11 splits the concrete cleanup defect out of the original R10, and R12 is the additional documentation finding from this pass.

**Scope and validation**

Across both passes, review traced the startup and dependency gates; boot-media identification and disk eligibility; identity rechecks and owner/token/countdown flow; runner flags, locks, progress, stop, and completion; evidence persistence and same-boot recovery; report USB selection/export/readback and privacy; Tk, accessible GTK, console, and desktop-launcher control flow; audio, keyboard, power/sleep; live-image staging and boot configuration; release qualification, transfer, manifest/signing, publication; and active release/acceptance instructions. The second pass specifically challenged prior findings against actual call paths, pinned upstream logging order, current remote settings, and shipped asset contracts, and reread the shutdown/recovery and platform launcher paths. Relevant regression tests and earlier dated audit evidence were consulted. This does not claim every line or every physical fault was independently exercised.

- **Observed hosted qualification:** [run 36359514845](https://github.com/BeamoTech/beamo-wipe/actions/runs/36359514845) passed for exact source `e8dc56a38dc987cfbf40048fd27070c6c8ddd2b4`: Linux image gate, native Windows launcher gate, and aggregate `CI gate`. The Linux gate includes source checks, ISO construction, and QEMU validation. The audit reused that exact-source result and did not start another paid hosted run.
- **First full Python suite:** **4,604 passed, 698 skipped, 8 failed in 1,301.20 seconds**. Command: `BEAMO_WIPE_DRY_RUN=1 python3 -m pytest -ra`, Python 3.10 / pytest 9.0.3 on macOS arm64. Failure triage is recorded above: the six timing/socket failures passed focused reruns under the stated conditions; two GTK imports are unavailable locally. This original run remains a failed run. Local log: `/private/tmp/beamo-release-audit-pytest-20260928.log`, SHA-256 `42df0f076782668a272471f8cef0ec2bf0cf622958c361e6bb5512bf1efaaf2b`.
- **Second full Python suite:** **4,619 passed, 689 skipped, 2 failed in 1,086.22 seconds (18:06)**. Command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 BEAMO_WIPE_DRY_RUN=1 python3 -m pytest -ra`, same Python/pytest and source, run outside the execution sandbox. The only failures are the two `ModuleNotFoundError: No module named 'gi'` cases in R10. Four Microsoft-link checks and five Tk display cases that had skipped in the initial sandboxed run executed successfully here, accounting for the nine fewer skips. The six original timing/socket failures also passed. This is still not an all-green local run. Linux/GTK/firmware-dependent coverage must be assessed from the hosted gate, not inferred from local skips. Local log: `/private/tmp/beamo-release-audit-round2-pytest-20260928.log`, SHA-256 `c8b0aeac41b725ae993078765ef2a190cb5e4acd0e0668089fc3ac4a5cc984d4`.
- **Local Go:** `go test ./...` passed in `desktop/` with Go 1.26.8, reported package duration 13.080 seconds. This is macOS logic coverage, not a replacement for native Windows/Linux testing.
- **Second-pass Go:** `go test -race -count=1 ./... && go vet ./...` passed in `desktop/`; the test package reported 6.849 seconds. Native platform-specific code still depends on its native gate.
- **Additional checks:** the two fake reliability checks described above; current branch/environment settings; release identity and rendered notes; public manifest and download-inventory signature verification. Relative Markdown file-link targets were checked in tracked repository documentation (excluding `.ai/` and `.cursor/`); no additional missing file target was found. This was not an external-link or anchor audit. Only small public metadata/signature files and two pinned upstream source files were downloaded. The ISO and USB image were not downloaded or independently rehashed in this audit.

No real erase, hardware restart, firmware change, ISO/QEMU build on this Mac, or publication occurred. The findings are a release-readiness work list, not a certificate that all defects have been found.

The required shared Beamo Brain handoff was attempted in both passes through its serialized `update` command. The context reader/writer stalled in the first pass; that owned writer was stopped and readback found no new handoff. The second attempt exceeded a bounded 20-second wait and its owned process was terminated and reaped. Completion of that latest handoff is unconfirmed. This repository report is the durable handoff for the audit.
