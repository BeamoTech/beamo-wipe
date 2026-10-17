# Pass10 independent modal lifecycle review — 2026-10-16

Read-only review requested by parent after mapped GTK sound dialog was observed
behind its parent in bare Xvfb. No tests launched by this reviewer; no source or
repository test writes. Existing discovery/integration reports preserved.

## Current source and shipped environment

`AccessibleWizard.button` calls action then render even when action opened a
modal. `render` unconditionally calls parent Gtk.Window.present, parent native
Gdk.Window.focus and arrival.grab_focus. SoundDialog currently only show_all and
grab_focus on its status; Gtk.set_modal and transient_for provide relationships
but do not implement native stacking enforcement without a window manager.
A periodic tick also rerenders when report/sound revisions change while the sound
dialog remains on the same wizard screen/epoch.

Shipped kiosk invokes `startx /usr/local/bin/beamo-wipe --accessible -- ...`
directly. The launcher execs the Python application and does not start a window
manager. Thus a proof on bare72DPI X11 is relevant to intended kiosk startup;
transient/modal relationship properties alone are insufficient acceptance.

## Review criteria for the eventual patch

1. Direct sound utility opening must leave native X stacking and keyboard focus
   on the live sound dialog after the button's generic render, not just GTK
   `get_mapped()`/modal property true. Prove actual top-level/focus on bare X11.
2. Report/sound revision rerender while a same-screen sound dialog is active must
   preserve its stacking and its current child focus, including no-audio/error
   status. Repeated timer ticks must not refocus the first modal child or parent.
3. Closing by button/response/escape/destroy must restore native focus to a live
   parent heading/control. The opener button may have been destroyed by render,
   so do not retain a stale widget pointer. Ordinary no-modal arrival focus and
   Orca heading announcements must remain unchanged.
4. Screen/epoch transition must close/cancel an obsolete sound dialog before new
   screen focus, even if navigation happens before the next periodic tick. Stop
   from sound dialog must still request Stop, destroy sound, and render current
   running confirmation without reopening or refocusing a stale dialog.
5. Closing the app must not refocus or resurrect its parent; ownership of timer,
   late worker cancellation and widget destruction remains as existing lifecycle.
6. LAST_CHANCE review overlay depth must stay held throughout the modal. Normal
   close must release it once and require a new full5s countdown with separate
   Erase action. Refocusing a modal must not release/reacquire consent or reset
   review continually. Ordinary review screen arrival behavior remains intact.
7. Use the existing GTK/GDK focus boundary; no window-manager dependency or kiosk
   boot/host configuration change is needed or authorized by this narrow bug fix.

Awaiting the UI author's original proof, final diff and regression tests. Parent
owns test slot coordination and independent reruns.

## First implementation review (before final child-focus proof)

The new `_live_sound_dialog` at render entry closes screen/epoch-stale dialogs
before choosing a top-level. `_focus_active_window` selects the current modal
when live and otherwise parent, preserving ordinary parent arrival.grab_focus
only in the no-modal case. New close handler runs after SoundDialog's own
_destroyed handler clears its dialog/ticket/overlay; this avoids recursive stale
close and releases review once. The closed guard prevents parent presentation
while the application itself is closing. Stop still requests its existing
confirmation, closes sound, then rerenders.

No blocker found for native stacking ownership or teardown in this draft. One
review concern sent to parent: `_sound_closed` only focuses native parent; the
opening generic render destroyed its old focused child and skipped the new
arrival focus, so Gtk/ATK focus restoration is not guaranteed. Requested a real
close regression asserting a live mapped focused arrival, and only then the
minimal explicit arrival grab on close when active top-level is parent. This is
a review concern pending concrete failure proof, not a separately proved bug.

New draft tests now cover actual sound-revision tick with nondefault modal child
focus, Stop confirmation cleanup and application close without re-presentation.
No test job was started by this reviewer. Awaiting final child-focus result/diff.

## Final review approval

Re-read final accessible_wizard.py diff and all14 modal regressions after the
author's test process retired. The close-focus concern was concretely proved:
author's modal-live-parent-focus run shows2 expected failures (get_focus None
after native focus restored) and1 application-close control pass. The final
_sound_closed now grabs the current arrival only if the active-window helper
returns parent; app.close's closed guard returns None, so it cannot refocus or
present the closing app. Final tests require exact live mapped app.arrival, not
only a non-null stale widget.

Checked author's final-modal-adjacent.xml:87pass/0failure/0error/0skip, including
all14 new modal cases. The final test hash matches modal-summary.json. Source changed afterward only
by adding the helper comment "Bare X11 has no window manager to keep the modal
above its parent"; removing precisely that comment in memory reproduces the
author-tested4a381276 hash. Current source is43839785 and needs the parent final
gate on its exact frozen bytes. These
are independently inspected artifacts, not a fresh test execution by this
reviewer. Parent still owns its independent original proof, screenshot acceptance
and full final gate. Source review finds no remaining blocking issue in this
narrow patch. Native stacking+focus and current child focus are covered across
open/reopen, direct rerender, sound-revision timer rerender and repeated ticks;
response/direct close, epoch transitions, Stop, app close and LAST_CHANCE review
countdown remain covered. No WM installation/dependency or kiosk change was made.

Reviewed SHA256:
- `src/beamo_wipe/ui/accessible_wizard.py`: `43839785353f5f3d644112d28645a7c7c8c950e23df92323ee3b42cc894f7758`
- `tests/test_accessible_sound_modal_pass10.py`: `526853280c9c737ab84fb4735b6b122f982125b7fd7cc8a7d0e03456daab8dce`
