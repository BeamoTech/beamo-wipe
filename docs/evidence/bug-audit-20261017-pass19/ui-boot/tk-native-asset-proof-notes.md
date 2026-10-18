# Prepared native-asset owner-boundary proof

2026-10-17, Codex child `/root/pass19_ui_boot`. Preparation/source review only;
the child author has not executed this proof. Root must review and admit every
run serially after its current diagnostic ends. No product or test source edit.

`tk-native-asset-lifetime-probe.py` contains eight evidence-local cases:

- Four structural controls use the full actual `TkWizard` constructor and
  actual `_teardown`, validate live keyboard input and an independent variable
  observer, and distinguish repeated teardown and a retained app from no
  external app owner. Automatic GC is disabled locally and its previous state
  restored. The no-external-owner controls explicitly show the remaining
  Python cycles/native assets before manual owner-thread fixture cleanup.
- Four owned-child cases exercise actual `run_tk`, actual constructor, actual
  `run()` and actual Tk mainloop. A fixed after callback invokes the supported
  `_teardown` boundary. Cases cross retained/unretained app ownership with normal
  return versus a controlled exception immediately after that actual mainloop.
  The exception case preserves normal propagation through `ui.run` and
  `run_tk`; its caller records only scalar traceback locations and then leaves
  the except scope. It does not clear traceback frames.

The child then invokes real `gc.collect()` on one positively owned later worker.
`Font.__del__` observation writes scalar font ID/name/thread entry/return records
and always calls the original destructor unchanged. The constructor records the
same 17 app-owned font IDs for matching. No Font operation, GC collection or
thread wait is neutralized. A retained app is a positive control: it should
prevent its resources becoming unreachable during that worker collection.

Only this diagnostic child's main thread may exit it with code 91 when its
collector remains alive after two seconds; normal interpreter shutdown could
wait on the same finalizer under examination. Parent `subprocess.run` has an
eight-second bound and may terminate only that positively owned child on timeout.
The parent records stdout/stderr/exit or timeout in test properties. Success
requires a zero exit plus both worker-collected and child-complete markers;
abort, hang and the controlled timeout exit are failures, not skips or passes.

Private Linux X11 opt-in is mandatory; shared `:1` and `:99` are refused.
All application process, engine, inventory, shutdown, audio and network effects
are rejected inside the child. The parent admits one fixed local Python script
and fixed arguments only; the child cannot start another process. Images are
ordinary repository preview assets and disks come from canned demo JSON.

## Why a narrow cleanup proposal needs both routes

The current `run_tk` constructs an app and directly returns `ui.run()`. The app
keeps root/button closure cycles and native assets after `_teardown` as detailed
in `font-lifetime-source-review.md`. On a normal return, an outer finally that
retires the UI, drops its local app reference and explicitly collects on the
owner thread could potentially release otherwise-unreachable cycles there.
That is a proposal for a bounded private source variant, not an approved fix.

On an exception, the propagated traceback contains the actual `TkWizard.run`
frame and its `self`. Dropping only `run_tk`'s local `ui` and collecting while
that exception is propagating cannot collect the app still owned by that frame.
The app may become unreachable only after a caller handles the exception,
after the proposed finally collection has already ended. The prepared exception
case distinguishes that route. Do not relabel a normal-return-only correction
as complete or clear traceback frames as a shortcut.

The direct `test_tk_runtime.ui` fixture has a separate ownership boundary:
`created` and the `build` closure retain apps through yield, then the loop's
`app` local retains the last one while every `_teardown` executes. Collection
inside that loop cannot collect the current app. Normal fixture cleanup could
potentially drop only its own created list and loop reference before owner-thread
collection; failure tracebacks may still retain a consumer's app. This fixture
route needs its own exact original/fixed proof and must not replace the real
production boundary proof. No fixture edit is proposed before that evidence.

Avoid broad arbitrary-attribute clearing, destructor suppression, global GC
changes, detached resource ownership or shortened assertions. A genuine lifecycle
correction must preserve live rendering, return/exception behavior, independent
variable observers, resource ownership and failure recovery. The existing
stop-on-blocker instruction permits retaining this as a proved lifetime gap
with prepared next steps if a complete bounded correction is not established.
