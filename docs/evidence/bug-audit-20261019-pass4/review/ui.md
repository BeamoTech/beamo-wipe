# PASS4 UI/state audit

Date/agent:2026-10-19, /root/runner_audit. Repository:/workspace/beamo-wipe.
Baseline:7f839e50e63db27a787eeabd758579352b6b3a3a.
Scope was rotated from prior runner/evidence and discovery/safety passes. No subagents were spawned.

## Confirmed and repaired defect

While curses shows WORKING, S has no action. If S is already held, Escape opens the Stop confirmation, and the next S repeat immediately stops the fake runner. That repeat belongs to a key pressed before the confirmation appeared. The owner did not supply a fresh confirm key. Both lowercase and uppercase spellings exhibit this, as do interleaved unrelated keys and quiet gaps shorter than the terminal release interval. This is unintended cancellation; no unsafe erase-start claim is made.

The docs/screens.md Stop contract requires a separate confirmation control and says repeated initiating clicks/keys cannot confirm a stop. Wizard.confirm_stop already binds consent to a unique live modal object, but curses was passing that current object for every S repeat. Its shared loop guarded Enter, Escape, owner/report Space, and report-sharing S, while lacking the corresponding stop-confirm S history.

The parent independently replayed the isolated original case and fresh-key control before approving edits. Approved ownership was limited to src/beamo_wipe/ui/console_wizard.py and tests/test_console_stop_hold_pass4_20261019.py.

The 20-line product addition remembers S presses throughout WORKING, across opening/closing the Stop confirmation. Repeated S aliases remain suppressed until a full observed quiet interval. Other keys interrupt that interval. Rejection occurs after the existing Enter/Escape bookkeeping so a suppressed S still prevents those guards from falsely inferring release. State resets after WORKING. A fresh Escape followed immediately by a fresh S still confirms.

The 17 committed-candidate regressions use the actual curses loop, real Wizard, and DryRunRunner. Native application/device actions have explicit fail sentinels. Cases cover lowercase/uppercase aliases, unrelated interleaved keys, short/full quiet gaps, Escape and S guard interaction, a preexisting open modal, keeping the erase running, repeated Escape, and genuine fake-runner completion before dispatch. The parent owns final integration and commits; this agent did not stage/commit/push.

## Evidence and replay

Immutable pre-edit source:baseline/console_wizard.py, SHA256
7cce42435bc5d87021bb52628fd0cf220c1872941e7cd3b3ddca0f357f7b73a0.

Original minimal proof:test_curses_stop_key_origin.py, stop-key-origin-original.{log,xml}:1FAIL/1PASS.
First real-controller regression version:real-wizard-before.{log,xml}:7FAIL/9PASS.
Final exact regression file replayed against archived source:final-regression-before.{log,xml}:8FAIL/9PASS, no errors/skips. The replay swaps only the imported console module in its own process and does not rewrite current repository source.

Run the final exact baseline replay from the repository:

```bash
source /workspace/beamo-tools/activate.sh
python /workspace/beamo-tools/audit-pass4-20261019/ui/replay_baseline.py
```

Run the repaired regressions and original proof:

```bash
source /workspace/beamo-tools/activate.sh
python -m pytest -q tests/test_console_stop_hold_pass4_20261019.py /workspace/beamo-tools/audit-pass4-20261019/ui/test_curses_stop_key_origin.py
```

After repair:regression-after.{log,xml}:19PASS, no errors/skips.
Adjacent suite before:focused-original.{log,xml}:180PASS/1display skip.
Adjacent suite after:focused-after.{log,xml}:197PASS/1display skip, no failures/errors.
The only skip is tests/test_keyboard_layout.py::test_rendered_keyboard_screen_keeps_check_field_and_layouts because this agent has no permitted display. Parent separately reports its owned container GUI selection passed all59cases, including that test; root/gui-focused.{log,xml} is parent-owned evidence.

The adjacent suite covers Wizard flow/authorization/countdown/lifecycle, busy transitions, stop/completion/failure/retry, language/keyboard, curses literal confirmation/utility tokens, report toggle/Enter/Escape guards, pagination, review visibility, plain-console review, and failed-interface cleanup. Exact pytest command can be reconstructed from the198 testcases in focused-after.xml; all baseline181 testcases were retained and the17 new cases added.

Python ast.parse(feature_version=(3,10)) passed for both changed files. git diff --check passed. Final product diff:console-final.diff. New final regression copy:test_console_stop_hold_pass4_20261019.final.py.

Frozen final SHA256:

- src/beamo_wipe/ui/console_wizard.py:86aaf67d0bbce045b2fb461e8f1e583837a33af8ac957bec04a9fe194eaba7f9
- tests/test_console_stop_hold_pass4_20261019.py:4e8258b50fa61eada5930a55f19dff63d4f0bbb79229bef9231c7b98e1b2c974

## Reviewed invariants and remaining boundaries

Read/reviewed src/beamo_wipe/wizard.py, ui/console_wizard.py, ui/tk_wizard.py, ui/accessible_wizard.py, and the related modal/review tests. Examined:

- Screen/epoch/generation-bound callbacks, current-screen gates, stale navigation and token/owner callbacks.
- Owner consent, exact token entry, method selection, explicit countdown action, snapshot handoff, and safe keyboard arrival focus.
- Review overlays, delayed/partial render, language/layout detours, countdown reset, and paged curses review visibility.
- Refresh claim/reset/sequence commit, retry rearming, busy-state rejection, and interface-loss settlement.
- Modal key carryover, X11 same-timestamp press/release repeat handling, focused Enter behavior, Escape stop/keep behavior, and stop-modal identity/completion precedence.
- Tk/GTK callback lifetime and sound modal state/focus/countdown behavior; curses/plain dispatch, diagnostic/report literal prompts, inventory overlays and cross-screen scroll resets.

No additional verified defect was found in these bounded checks. Earlier speculative low-resolution and constructor-cleanup observations were not reported as bugs without a reachable reproduction. Prior pass1-3 repairs remain baseline, not new findings.

GUI environment history:direct local D-Bus binding returned EPERM (gui-preflight.log); this agent's allowed invocation of /workspace/beamo-tools/beamo-dev returned Docker-socket EPERM (container-gui-preflight.log). Parent advised no permission retries and independently ran the isolated container GUI tests successfully. These are environment execution-context differences, not product failures. No shared :1/:99 displays or peer sessions were modified. No native inventory, real nwipe, physical-device writes, power/firmware changes, hosted jobs or publication were performed.

All source/test changes are frozen and handed to root for independent review, canonical final gates, unfinished-work checkpoint and any authorized publication follow-up.
