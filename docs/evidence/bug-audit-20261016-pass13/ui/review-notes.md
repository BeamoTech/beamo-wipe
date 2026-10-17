# Pass13 UI / boot source review

2026-10-16, /root/pass13_ui_boot. Worktree /root/dev/Beamo Wipe,
branch fix/safety-audit-20261015; base HEAD35107a8d1a701093eac876a58ab4efd50e291673.
Current AGENTS and pass13 unfinished item read. Shared /root/dev/AGENTS.md absent;
root's recorded owner continuation governs. No native application effects used.

Source-only checks covered Tk/GTK render generations and stale callbacks, held
Return/Space/Escape/F5 bookkeeping, focused Last Chance actions, native input
handoff between startup/main/modal, modal screen epoch and countdown overlays,
Tk body/picker/footer layout, curses and plain confirmation/cancel/EOF/retry/
report commands, startup worker/outcome transitions, kiosk retry budget and
fail-closed nwipe process power checks, hardened live entrypoint, build input
copy validation, CI native acceptance/required job boundaries, desktopweb session
and readiness expiry/error logic. No additional safety bug proved in these paths.

Two defects were proved on a private1600x1000x24 Xvfb at72DPI with D-Bus, fake
wizard only and every native engine/discovery/audio/power subprocess forbidden:

1. Tk main windowed preview ignores first actual Escape when pointer remains
outside its1280x820 mapped rectangle. Native focus and Tk focus both remain
unclaimed. Pointer inside and both fullscreen controls succeed.
2. Tk general scrolling body ignores mouse wheel over descendant prose. Root
is in the normal Tk bindtag chain but canvas/inner are not. Actual XTest button5
with hit-tested label leaves yview unchanged; event on canvas moves it. Existing
picker already solves descendant wheel handling in its separate path.

Proof history (no source edits yet):
- original-proof.xml:8cases3intendedFAIL/5controls,2.48s.
- original-native-proof.xml/txt:10cases5FAIL/5PASS,2.76s; one extra setup failure
  assumed an uncovered native canvas gutter, but the label covers that pixel.
  Retain this failed setup separately; it is not evidence of an extra bug.
- original-confirmed.xml/txt:9cases4intendedFAIL/5controls,2.71s. Corrected native
  label proof confirms hit widget and compares a working canvas control. No skips
  or errors. All owned windows/private display and processes retired.
- tk_wizard-before.py SHA256:
  892d9dc27082c84ca5bfa06dc09dc36c90b7b19e23ff402e22c89a861c855fee.

Requested fixes require root source ownership/review before edit. Suggested:
one native input claim at actual run after idle, retaining existing desired
child; root wheel route scoped to current body canvas/inner ancestry. Existing
child handlers, picker behavior, keyboard focus, selection and consent gates
must remain unchanged. Final tests should cover direction, redraw, unrelated
footer controls and native hit-tested wheel input as well as keyboard focus.
