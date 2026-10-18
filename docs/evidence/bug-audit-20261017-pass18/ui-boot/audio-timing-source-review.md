# Source-only review of pending GTK sound timing failure

2026-10-17. The primary's full canonical main/Orca gate is still running.
This review ran no test, probe, GUI, process, native inventory, engine or
auxiliary campaign and changed no source/test. The exact failed assertion
has not yet been supplied; no cause or passing result is asserted here.

Reviewed `tests/test_accessible_runtime.py` lines 1490-1670,
`AccessibleWizard.button`, `open_sound_check`, `_focus_active_window`,
`render`, `tick`, `ui/sound_dialog.py`, and `audio_jobs.py`.

## What the two 60 ms intervals measure

The first interval covers `app.actions[SOUND_CHECK_BUTTON].clicked()`:

1. The generic button handler invokes `open_sound_check`.
2. `SoundDialog` constructs labels, scroll containers and buttons, sets the
   transient/modal relationship, computes monitor geometry, and calls
   `show_all` and `grab_focus`.
3. `_submit` creates a ticket and calls the shared audio worker's `submit`.
   A previously retired worker requires `Thread.start`, which synchronizes
   with the OS thread bootstrap before returning.
4. The utility focuses/presents the dialog; the generic button handler then
   unconditionally rebuilds the parent wizard screen via `render`, which
   presents/focuses the modal again.

The controlled `slow_outputs` function is reached only through the queued
`_discover` action. `AudioWorker._run` releases its condition lock before
calling that action; no source path here calls `list_outputs` on the GTK
thread or holds the worker condition across its two-second wait. A stuck
audio call therefore does not itself explain a slow GUI call from this
source trace. A real timed trace must establish whether construction,
thread startup/locking, redundant parent rendering, native display work, or
an unrelated delay consumed the interval.

The second interval measures both `app.tick()` and `drain()`. The latter
processes GTK's default-context events until none remain; it has no event
count bound and includes queued layout, focus, accessibility and existing
100 ms timer work. The pending sound ticket is polled without waiting.
This broad interval does not isolate the sound poll cost by itself.

The three current fixes in discovery/curses/checkbox destruction have no
direct call in this GTK SoundDialog path. This is source separation, not
proof that unrelated changes cannot affect global scheduling or resources.
The observed host load/pressure alone does not attribute an assertion.

## Failure cleanup detail

The first click-duration assertion precedes the test's `try/finally`.
If it fails, the explicit `release.set()` does not run. `ui` fixture cleanup
closes/cancels the dialog ticket, but the controlled `slow_outputs` ignores
ticket cancellation and remains in its own two-second Event wait. It can
occupy the process-shared audio worker until that timeout, potentially
affecting later sound tests. This is a source-confirmed consequence of the
assertion's placement, not the cause of the first timing violation.

## Instrumentation proposal, after canonical gate completion

- Preserve the failing full-run transcript, fresh JUnit, exact assertion,
  elapsed value, source hashes and host timestamps before any follow-up.
- Keep both `< 0.06` assertions and all closed-dialog/safety assertions.
  Put release/owned-worker cleanup around the whole measured operation in
  a separate fixture/instrumentation layer, so a timing failure cannot
  leave its controlled barrier pending. Do not accept an isolated pass as
  an explanation of the original failure.
- For one focused diagnostic execution, wrap only the relevant Python
  boundaries (`open_sound_check`, `SoundDialog.__init__`, `_submit`, worker
  `submit`, `render`, `_focus_active_window`, `tick`, `poll`, `_destroyed`).
  Record in-memory entry/exit wall time, current-thread CPU time, thread ID,
  nesting and render generation; write receipts only after the interval.
  Record existing GLib tick invocations rather than adding new timers.
- Record when the controlled worker enters, its release is set, it returns,
  its ticket is canceled, and the dialog closes. Distinguish the cost of
  `tick` from `drain`; count already processed drain iterations without
  removing work or changing any timing limit.
- Large wall time with small thread CPU time narrows the issue to waiting
  or descheduling, but does not distinguish scheduler delay from a lock,
  native display round trip, or another wait. A native stack/owned-process
  trace would be needed before naming one as the cause.

If the trace isolates unnecessary parent reconstruction while the modal
already owns focus, that is a specific optimization candidate to prove and
review separately. It does not justify changing production code now or
weakening the existing latency assertions. No blind retry is proposed.
