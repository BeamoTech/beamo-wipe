# Pass19 UI, state, boot and build source audit

Author: Codex child `/root/pass19_ui_boot`, 2026-10-17. Repository
`BeamoTech/beamo-wipe`, branch `fix/safety-audit-20261015`, parent commit
`35107a8d1a701093eac876a58ab4efd50e291673`, shared worktree
`/root/dev/Beamo Wipe`. Read current AGENTS and unfinished record. The referenced
shared `/root/dev/AGENTS.md` is absent. Root owns GTK latency investigation,
fixture cleanup proofs, runtime admission and the final canonical record.

## New candidate awaiting root-run proof

`TkWizard.__init__` in `src/beamo_wipe/ui/tk_wizard.py:1240` and `:1241`
registers `_confirm_var_written` and `_typing_var_written` as write traces and
discards both returned tokens. `_teardown` at `:1629` retires widget-owned
pending `after` commands and destroys the root at `:1651`; it does not retire
those variable-owned trace commands. The callbacks contain no `_ui_dead`
guard (`:2589`, `:3504`). The typing callback can still mutate the old Wizard;
the confirmation callback additionally paints the old control tree.

This is separate from the pass18 `_CheckRow` trace fix and the independent
observer in its regression fixture. It is a candidate for retained bound owner
references and callbacks on a destroyed UI. No application was run by this
child and no defect is labeled proved yet.

Prepared `tk-owner-trace-probe.py` has eight fake-only cases using the actual
full constructor, actual trace registration, actual callbacks and full product
teardown. Four cases retain both variables, add independent peer observers,
destroy once/twice, then check old state and exact remaining trace ownership.
Two cases require working live input. Two check weak references to the app,
root and both local variables after teardown and main-thread collection.
Fixture cleanup follows assertions/evidence and removes only the exact tokens
it observed before probing plus its own exact peer token; no broad sweep.
It rejects subprocess, inventory, engine, audio and shutdown effects, requires
an explicitly isolated X11 display and refuses shared `:1` / `:99`.

All `trace_add` sites in this file were searched: `_CheckRow` at `:986` now
stores and retires its token at `:1015`; these two app-level registrations are
the only remaining discarded tokens. No proposed product patch was applied.

## Adjacent source paths examined

| Area | Evidence and judgment from source |
| --- | --- |
| Final authorization | `wizard.py:1745` claims under the lock, rejects stale operation identities and preview/NwipeRunner combination, then moves to CHECKING before work. `:1903` rediscovery compares boot and target identity and rechecks the whole listed inventory context before runner start. No new bypass found in this review. |
| Refresh and stale completion | `wizard.py:1484` clears owner/token/selection/method authorization before I/O. `:1523` rechecks scan ownership after validation outside the lock. UI result paths drop late completions after teardown. No new stale commit found. |
| Review detours and overlays | `wizard.py:699` / `:707` suspends Erase and restarts the five seconds after final overlay exit. Tk `:1817` and GTK `:804` restart first-review timing after construction. The pass18 curses displayed-frame guard remains at `console_wizard.py:1875` and does not replace the live gate. No additional demonstrated issue. |
| Stale UI actions | Tk `_nav` at `:1607` binds screen and draw generation. GTK `button` at `accessible_wizard.py:177` binds generation and rejects insensitive controls. Return/Space/Escape auto-repeat guards and modal-held key forwarding inspected. No new state-advancing key route identified. |
| Stop confirmation | `wizard.py:2105` opens a distinct object identity; `:2116` rejects stale object consent and atomically claims stop. `_perform_stop` preserves a prior terminal engine outcome and returns to WORKING with a warning if status/cancellation cannot establish terminal state. |
| Interface loss | Tk `_tick` at `:1655`, GTK `_runtime_failure` at `:1090`, app `_run_one_session` at `app.py:523`, and console outer guards settle the owned engine before releasing normal UI ownership. Source-only review does not establish native failure acceptance. |
| Power and unsaved reports | `wizard.py:1283`, `:1313`, `:1359` check local runner, possible pinned engine, recovery, pending report/diagnostic/evidence operations and discard generation. `app.py:290` rechecks immediately before the actual request. No native power command invoked. |
| Plain text consent | `console_wizard.py:586` rejects real piped/noncanonical consent and flushes typeahead after review, `:675` settles terminal loss. Curses F5 opens refresh wording; repeated F5 does not confirm it because Enter is a separate path. |
| Kiosk recovery | Shipped shell contains no inventory command or nwipe launch. Fixed choices invoke only UI entrypoints or guarded power. `pgrep -x nwipe` at `:159` must return exactly 1 before power; missing/error/running cases block. Auto retry budget remains three, normal exit goes to menu, EOF does not auto retry. No kiosk script executed. |
| Live wrapper and tmpfs | `usr/local/bin/beamo-wipe` clears test overrides and loader variables, fixes path, changes to `/`, and invokes Python `-sP`. Kiosk service uses tmpfs `/tmp` and `/var/tmp`, private mounts/network, no login shell, no restart loop. `app.py:132` strips live test flags. |
| ISO build output handling | `scripts/build-iso.sh` validates regular owned prior bundles, uses private staged output and same-inode rollback evidence, and publishes with exclusive `os.link`. The privileged Docker/ISO path was read only. This review does not qualify an image or authorize that path here. |
| CI/publication | Current `ci.yml` triggers on main push, main PR and manual dispatch, includes all source/image/QEMU/native-Windows required phases and has read-only contents. `release.yml` is a distinct manual main-only production publisher after verification. Neither was invoked or modified. |
| Preview/hardware/copy | `scripts/preview.sh` exports fake mode and invokes `--preview`. `compat_story.py` limits x64/Intel/AMD support, excludes Apple Silicon/Chromebook and states firmware-dependent signed-boot acceptance without bypass. `recovery.py` preserves the three required failure sections; approved claims and support contact were read. No new overclaim established. |

## Limits and next action

This result is a source audit and prepared proof, not passing runtime or hardware
acceptance. Root must review and run the bounded Tk module serially on its owned
private display; preserve original failing evidence before any source change.
If proved, a fix should retire exactly these two owned trace tokens at the
authorized app teardown boundary, preserve peer observers and all live behavior,
then run the original/fixed cases, adjacent Tk teardown and full required gates.
Direct external `root.destroy()` can be examined separately if root decides it
is part of the supported lifecycle; it is not conflated with this teardown proof.
No product/test file, claim, pin, automation, credential or host/device setting
was changed by this child. No runtime, network, build, engine or power action ran.
