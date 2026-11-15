# Independent review of merged PR #94 (BeamoTech/beamo-wipe)

> Recorded 2026-11-15 17:49Z by Claude (Opus 5.5). The review was done by a separate
> reviewer agent that was given the code and the safety rules, not this
> session's conclusions. Claude spot-checked LOW-2 and LOW-3 against main
> `93a7c9e9` and both match the code: `sleep_inhibit._xset` runs
> `subprocess.run(..., timeout=5)` synchronously, and
> `corresponding_source._github_tarball` accepts a tarball on its pax
> `comment` header alone. LOW-1 and LOW-4 were not re-checked. No finding was
> fixed in this record; each needs its own reviewed change.

- PR: "Release readiness: LTS 6.12 kernel, hardware support, five languages, report and QEMU gate fixes"
- Merge: d1c85087; base 58c677f7316b5e2fc0cbb3ee4b502681c80338c1; head f00e55ca526c400b4a4a1c75bbd780d79aa9efae (388 files, 100 commits)
- Compared against current main 93a7c9e9a7fe7887705d55b72f1e84b9695edfa8
- Method: read-only git object commands (`git diff`, `git show`) in the clone
  a local clone of the repository. No checkout, no tests, no WSL, nothing posted to GitHub.
- Reviewer: independent agent review dated 2026-11-15. This is a static read of the code only. Nothing was run or tested.

## Summary

| Severity | Count |
|---|---|
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 0 |
| LOW | 4 |

I traced every path I could find from a confirmed disk to the nwipe argv. I found no path where the boot USB or an unconfirmed disk becomes the target. The confirm token, 5 s countdown, owner tick and Erase-now click cannot be bypassed. The owner tick carries over only as #187 intends. The nwipe flags and the log location are unchanged. Between f00e55ca and 93a7c9e9 the only source changes are in
`src/beamo_wipe/ui/accessible_wizard.py` (GTK Done/help rebuild) plus launcher/signing scripts. The safety-critical modules are byte-identical on main, so every finding below still applies on 93a7c9e9.

## Findings

### LOW-1: The Confirm prompt can give the wrong reason for needing more than 4 characters
- Where: `src/beamo_wipe/safety.py:441` and `:446` (`_card_spec`), with `src/beamo_wipe/copy.py:1098` (`CONFIRM_LONGER`) and the matching de/fr/es/it strings. The code is the same on main 93a7c9e9.
- How it happens: `_card_spec` makes the card token longer whenever the 4-character ending is in `banned`. `banned` also holds every other listed disk's size label (from `_cross_disk_tokens`), every listed kernel name and full identifiers. Any token longer than 4 then gets `longer=True`, and the prompt adds "Another listed disk ends with the same last 4 characters, so more are needed."
- Failure scenario: a target with serial `...X1000` is listed beside a 1 TB disk whose size label is `1000`. The token becomes 5 or more characters, and the screen says another disk shares the ending. No disk does, so the owner may doubt the identity. Disk binding is not affected: the token is still unique and longer.
- Confidence: CONFIRMED by reading the code. This is a copy accuracy issue, not a safety bypass.

### LOW-2: `xset` runs synchronously inside the runner's start and finish critical sections
- Where: `src/beamo_wipe/sleep_inhibit.py:83` (`_keep_display_on`), `:122` (`timeout=5`) and `:149` (`_restore_display` in `stop`). They are called from `src/beamo_wipe/nwipe_runner.py:1548` (`self._sleep_inhibit.start()`, under `self._lock` and the wipe flock, after the final identity recheck and target reservation) and from `:2095` (`_release_wipe_lock` → `stop()`). The code is the same on main.
- How it happens:
  - Start: up to 5 s pass after the target has been reserved and rediscovered, before `Popen`. The open target fd from `_reserve_target_under_lock` keeps the kernel name from being reused, so this is not a hotplug safety gap. It does lengthen the time the UI shows "Checking".
  - Finish: the engine-exit branch of `NwipeRunner.poll` calls `_release_wipe_lock()`. `Wizard.tick()` reaches `poll` while it holds `Wizard._lock`, on the Tk/GTK UI thread. A slow or wedged X server can therefore freeze the result screen for up to 5 s while the wizard lock is held.
- Failure scenario: an X server that does not answer (some fbdev/safe-video setups) leaves the interface unresponsive for about 5 s exactly when the erase finishes. The outcome is still correct.
- Confidence: the code path is CONFIRMED; whether it hurts in practice is PLAUSIBLE, because it needs a slow X server.
- Suggestion: run the display restore off the UI thread, or call it after the runner lock and wizard lock are released.

### LOW-3: GPL corresponding-source fetch ties the nwipe tarball to its commit only through the archive header
- Where: `scripts/corresponding_source.py:279-292` (`_github_tarball`), used at `:351` and `:356`. Same on main.
- How it happens: the codeload tarball is accepted when the pax global `comment` header equals the pinned commit. The file contents are never checked against the commit tree. The comment admits GitHub's tarball bytes are not stable, so no fixed hash is possible. As a result, the archived nwipe source is only as trustworthy as the TLS session plus a header that anyone can set.
- Failure scenario: a substituted or proxied tarball that copies the header would be archived and recorded in SHA256SUMS as the corresponding source for the pinned nwipe commit. This affects licence-compliance archives only, not the shipped image. The Beamo source is taken from a local `git archive` when one is available.
- Confidence: CONFIRMED by reading the code. This is partly by design, so it is listed for awareness only.
- Suggestion: fetch nwipe with `git fetch` at the pinned commit and `git archive` it, or check the extracted tree hash.

### LOW-4: The "ready to pass on" claim on a verified result also appears for SSD/NVMe
- Where: `src/beamo_wipe/outcomes.py:132` (`NEXT_ITEM_GIVE_VERIFIED`), shown by `plain_result` whenever `view.code == "verified"`, whatever the disk kind. Same on main.
- How it happens: the note just above it (`NOTE_VERIFIED`, `:115`) says that on an SSD the controller decides what remains. The checklist line then says without qualification that the disk "is ready to pass on". `docs/claims.md:14,48,54` limit SSD claims to the storage the drive exposes.
- Failure scenario: an NVMe owner reads the bold checklist line as a guarantee that nothing can be recovered.
- Confidence: PLAUSIBLE that owners will be misled. The source says the copy was owner-approved on 2026-11-03, so it may be intentional. Raised so the owner can confirm.

## Checked and found sound (no finding)

- **Owner carry (#187)** (`owner_carry.py`, `wizard.py` `continue_owner`, `_apply_owner_carry_locked`, `take_handoff`, `_request_new_session_locked`, `app.py` session loop):
  - The carry exists only in memory in `_run_session` and is handed over only by Erase another disk.
  - It is applied once, at the first Keyboard→Owner step.
  - It requires that the new session's own discovery lists only erasable disks covered by identity (serial/WWN, size, model). It fails closed when a disk has no identity, has a duplicate key, or when discovery is blocked or empty.
  - It is cleared by every rescan (`begin_refresh`), by layout invalidation, by Change and by recovery.
  - It never replaces the token, method, countdown, Erase now, or the rediscovery and `_authorization_matches` check in `_perform_start`, which binds the whole listed inventory.
- **Card confirm token (#129)** (`safety.confirm_spec` / `_card_spec`):
  - The token is the last 4 or more ASCII characters of the serial/WWN shown on the card.
  - It is unique against every listed disk's serial/WWN ending, including the boot USB through `listed_disks`, and against size labels and kernel names.
  - It falls back to the older rule, or to `SafetyError`, and never to a weaker token.
  - `token_ok` is recomputed from the current discovery at every check.
- **nwipe_runner target reservation**:
  - The read-only, non-inherited (`O_CLOEXEC`, not in `pass_fds`) handle is opened under the wipe lock and checked with `S_ISBLK` and rdev before `_recheck_identity_under_lock`.
  - It is closed in `_release_wipe_lock` on every failure path.
  - The argv builder and flags are unchanged.
  - The new PRNG log lines are display-only and retained without affecting the verdict.
- **Pick order (#151)** in Tk, curses, plain console and GTK: rows and number keys map to disks by path from the same `pick_order` tuple. `move_selection` follows the same order. The boot USB is never in `selectable`.
- **Review/Erase keys**:
  - Tk focuses Back on LAST_CHANCE, and Enter on a disabled primary does nothing.
  - Curses (#165) moves focus to Erase only on an enabled, painted frame and resets focus to Back on arrival or restart. A bare Enter in `_handle` no longer erases.
  - The GTK LAST_CHANCE Enter path is focus-only and has held-key suppression.
  - A Tk/GTK disk double-click or activation goes only to Confirm; the token is still needed.
- **Check disks again (#136)**: `begin_refresh` refuses a direct scan from screens that hold confirmations. All UIs go through `open_refresh_confirm`. In the guarded dialog, Enter or Esc keeps the answers.
- **Keyboard layout change from Confirm (#155)**: keeps the owner tick and the disk, and keeps a typed entry only if it still matches. It clears `_authorized_operation` and the countdown.
- **Report USB probe (#135)**: read-only and uses the export's own selector, baseline and generation guard. The exFAT export mounts with the same `nodev,nosuid,noexec,nosymfollow` options and checks fstype/rdev/options in mountinfo.
- **Live image**:
  - Ctrl+Alt+Del is masked and burst handling is set to none. SysRq is 0. The QEMU gate asserts all three.
  - The troubleshoot entry drops `noapic`/`nolapic`/`nosmp`/`vga=`.
  - The kiosk tmpfs over `/sys/class/graphics` is confined by `PrivateMounts=yes`.
  - There is no auto-start erase path.
  - The launcher's `xrandr` helper runs in a subshell and never fails the session.
- **QEMU gate (`scripts/qemu-verify.sh`)**:
  - `set -Eeuo pipefail` is kept.
  - New checks: Secure Boot signers, kernel and shim version floors, firmware/microcode/keymap presence, absence of radio firmware, unfilled GRUB markers.
  - New journeys: SATA, NVMe and exFAT, plus a writable boot USB, which shows the boot USB is excluded by identity.
  - No existing check was removed or turned into a soft failure, apart from the intended `vga=`/legacy-flag change.
- **Windows launcher "Restart to boot options" (#183)**: runs a fixed `%WINDIR%\System32\shutdown.exe /r /o /t 0` (no `/f`, no BootNext). Each request is token- and revision-bound, single-use, refused in preview and refused inside `go test` binaries.

## Coverage

**Reviewed (traced end to end or diff read in full):**
- `src/beamo_wipe/`:
  - Full diff, safety-relevant paths traced: `wizard.py` (whole 1,748-line diff, plus unchanged claim/start/countdown code), `safety.py`, `nwipe_runner.py`, `discover.py`, `owner_carry.py`, `disk_order.py`, `models.py`, `identity.py`.
  - Full diff: `app.py`, `evidence.py`, `privacy.py`, `power.py`, `recovery.py`, `sleep_inhibit.py`, `support_export.py`, `outcomes.py`, `methods.py`, `engine_checks.py`, `diagnostic_report.py`.
  - Key logic: `report_panel.py`.
  - Skimmed: `keyboard.py` and `lang.py` diffs, `inventory.py` diff (eligibility untouched), the header of `erase_record.py`, and the write surface of `hidden_storage.py`.
- UI key, focus and action paths only:
  - `ui/tk_wizard.py`: `_on_return`, `_on_key`, `_on_escape`, LAST_CHANCE, Pick rows, double-click review, Done footer.
  - `ui/console_wizard.py`: curses `_loop`/`_handle` for Pick, Confirm, Review, Refresh and Keyboard; plain-console Pick, Confirm, Method, Review; `_answer` command words.
  - `ui/accessible_wizard.py`: Pick activation, LAST_CHANCE Enter, F5, held-key guard.
- Locales: only Confirm prompts, console command words and owner-carry strings (de/fr/es/it).
- `packaging/live/`: whole diff (GRUB, hooks, kiosk, launcher, sysctl/systemd, package lists, backports pin, `inside-docker.sh`).
- `scripts/`: `qemu-verify.sh` (whole diff, skimmed), the diffs of `publish_release_gcs.py`, `stage_wrapper_sources.py`, `ci-hosted.sh` and `release_manifest.py`, the fetch section of `corresponding_source.py`, and the header/claims of `verify-usb-stick.py`, `rescan_release_packages.py` and `gen_boot_keys.py`.
- `desktop/`: `advanced_startup.go`, and the diffs of `platform_windows.go`, `main.go`, `boot.go`, `web/app.js` and `web/index.html`.

**Not reviewed (skipped or only glanced at):**
- `tests/`, about 64% of changed files: all new or changed tests, `tests/goldens/`, `tests/fixtures/pci_185/`.
- `docs/` and `docs/decisions/` (only `docs/claims.md` was grepped), and `.ai/memory/`.
- `helper/*.html` (en/de/fr/es/it boot helper pages) and `helper/README.md`.
- Locale tables `src/beamo_wipe/locales/{de,fr,es,it}.py`, beyond the spot checks above. Translation accuracy of safety copy is not verified.
- `src/beamo_wipe/gallery.py` (web preview, +1,112 lines) and `demo.py` / `demo_lsblk.json`.
- Most of the rendering code in `ui/tk_wizard.py` (+3,754 diff), `ui/accessible_wizard.py` and `ui/console_wizard.py`. Layout, painting and screen-reader text were not read.
- `copy.py` (only the confirm/owner/refresh strings were read), `progress.py`, `compat_story.py`, `audio_jobs.py`, `sound.py`, `help_menu.py`, `token_feedback.py`, `storage_limits.py`, `result_summary.py`, most of `erase_record.py`, the `hidden_storage.classify` logic and the `lang.current_text` reverse mapping.
- `desktop/bootkeys.go`, `bootkeys.json`, `readiness.go`, `platform_linux.go`, `platform_other.go` and the Go tests.
- The bodies of `scripts/verify-usb-stick.py`, `rescan_release_packages.py`, `gen_boot_keys.py`, `stage_live_assets.py` and `build_desktop.py`.
- Runtime behaviour on real hardware or kernels: kernel 6.12 package availability, firmware pins, and nwipe's open semantics while Beamo holds its read-only target handle. These were reviewed statically only. The QEMU gate exercises them.
