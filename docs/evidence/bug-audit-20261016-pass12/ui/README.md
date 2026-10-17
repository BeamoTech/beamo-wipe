# Pass12 UI/startup evidence

2026-10-16, Codex bounded UI/boot reviewer. Repository
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, starting HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Current dirty pass8/pass10/pass11
source was preserved. No staging, commit, push, host/device/engine/power/audio
operation, hosted CI or VM operation. Runtime campaigns were serialized with
the primary's explicit single test slot. All native displays were private
72DPI Xvfb sessions with separate D-Bus/runtime directories.

## Five independently proved UI defects

1. Failed remembered audio-output restoration left the refused sink selected
   although the actual default and volume came from another sink. Clicking
   the same refused radio could not retry. Original fake trace recorded
   default `speakers`, chosen `headphones`, active `[false,true]`, one restore
   request after a same-radio retry. Fixed trace records chosen `speakers`,
   active `[true,false]`, and two requests after retry. The stored preference
   is retained; only accepted/current dialog selection changes.
2. Unscrolled sound content expanded past a small monitor. At800x600, eight
   outputs made the WORKING dialog560x764, Stop y621 and Close y750; sixteen
   made it560x1004. Even two WORKING outputs put Close's lower edge at604.
   Original full-root PNG visibly lacks the modal's Stop/Close controls.
   Scrollable content, monitor workarea placement, and fixed Stop/Close keep
   those controls visible. All eight one/two/eight/sixteen-output Owner/Working
   traces now fit560x480. Actual keyboard-focus tests also bring the last
   output and lower speech control into view and preserve Stop confirmation.
3. Tk startup lacked native focus on bare X11. Corrected native trace records
   actual window rectangles and pointer coordinates: outside-window Escape
   was ignored, inside-window Escape worked. Fixed startup takes native focus
   after mapping and handles the first Escape without the rescue timer.
4. Unconditional Tk PlaceWindow centered the empty widget's requested200px
   size, replacing configured geometry. Original1600x1000 fullscreen origin
   was700,400; at800x600 it was300,200. The original windowed640x440 at300,200
   also overflowed the800x600 root. A private source restore proved the800
   case without reverting shared source. Explicit configured-size placement
   centers windowed startup and keeps fullscreen at0,0.
5. Both graphical startup presenters erased the stall notice one100ms frame
   after displaying it. Deterministic fake-clock, post-render frame traces
   show original `[false,true,false,false,true,false]` across two stages.
   Fixed graphical state is `[false,true,true,false,true,true]`. Default
   one-shot API/serial marker behavior remains unchanged; persistent state is
   requested only by graphical presenters and resets at a stage/terminal
   boundary.

## Original proof and setup history

- `source-before.json` and `*-before.py` preserve exact starting UI sources.
- `original-sound-trace.json`, `original-capture-sound-trace.json` and the
  original800x600 PNG prove refused restoration and offscreen actions.
- `original-tk-startup-trace.json` is the initial trace with inaccurate
  descriptive pointer labels. It is retained. Corrected native coordinates
  and pointer-inside booleans are in `original-corrected-tk-startup-trace.json`.
- `original-windowed800-tk-startup-trace.json` uses the private UI source
  restore described in `original-ui-import-root.json`; no shared source was
  reverted. It proves windowed and fullscreen placement at800x600.
- `original-stall-trace.json` is the initial wall-timer capture. Its callbacks
  were offset from actual GTK polls and do not prove all frame identities.
  `original-stall-frames-trace.json` replaces it with exact post-render frame
  instrumentation and proves both presenters. Both scripts/results retained.
- `fixed-initial-*trace.json` records repaired bounded native behavior. The
  primary independently runs all final regression modules against the exact
  starting application source; its report owns that combined original proof.

## Regression/check results

Three new regression modules contain99 cases:

- `test_sound_dialog_state_pass12.py`:78 cases covering accepted output state,
  same-output retry,1/2/8/16 outputs, Owner/Working, en/fr/de,800x600 and
  1600x1000 workareas plus a nonzero workarea origin, keyboard-visible lower
  controls/last output, and guarded Stop confirmation.
- `test_startup_notice_state_pass12.py`:11 cases covering one-shot serial
  events, persistent state boundaries, and exact actual Tk/GTK frames in all
  three languages. Graphical cases require the isolated-display flag.
- `test_tk_startup_focus_geometry_pass12.py`:10 actual native XTest Escape and
  mapped rectangle cases, fullscreen/windowed and all three languages.

First selected adjacent campaign:350 cases,348PASS/2FAIL/0ERROR/0SKIP,
1 Orca case deliberately deselected for the canonical separate session,
50.66s. All99 new cases passed. Both failures were the existing
`test_startup_exception_closes_its_window[start/mainloop]`: its MagicMock root
returned a MagicMock for screen dimensions, so the configured geometry failed
before the intended injected exception. Only two realistic integer return
values1600/1000 were added; injected failures and both raises/destroy assertions
are preserved. Exact original fixture/hash retained. Affected full TK-GC
module subsequently5PASS(1.78s). No passing adjacency repeated solely for
confidence; the primary's final full gate reruns final source.

Actual800x600 new sound/Tk selection:88PASS/0SKIP/0ERROR(17.22s).
`final-check-summary.json` derives counts directly from JUnit, separates the
first fixture failures from passing checks, and records all99 regression passes.
Ruff/full local gate and combined exact-source original proof are owned by the
primary, not claimed here.

## Final native artifact review

`final-capture-800x600.json` and `final-capture-1600x1000.json` record six
unedited full-root PNGs, actual server DPI, dimensions/origins, native focus,
image hashes, and owned window/worker teardown. All six were opened and
visually inspected by this reviewer: sound16-output modal shows Stop/Close;
Tk windowed startup is centered; fullscreen fills the root from0,0; stage text
is readable without clipping. Native keyboard tests prove reachability of the
scrolled controls. Physical monitor/media behavior is not tested here.

Final owned file hashes are in `final-source-test-hashes.json`. Exact pass12
increments, including the fixture input update and three new modules, are in
`pass12-ui-changes.diff.txt`. Source/test freeze honored after the primary's
request; remaining work is primary independent source/artifact review,
combined original proof and final required local gates. Historical SIGTERM
and timing attribution remain unresolved and are not explained by these runs.
