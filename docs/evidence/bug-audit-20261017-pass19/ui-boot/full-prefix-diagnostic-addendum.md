# Full-list versus truncated-prefix diagnostic distinction

2026-10-17, Codex child `/root/pass19_ui_boot`. Source and existing evidence
review only; no application/test runtime or product/test edit by this child.
Source remains the root's frozen 771-input candidate. Root owns all execution,
acceptance and incident attribution.

The second canonical attempt omitted the extra observer and `PYTEST_PLUGINS`
and still aborted. Its receipt records seven visible failure glyphs, no main
JUnit, a GC stack on an audio worker inside pass14's `active()` barrier, and
one separately passing Orca case. Those observations establish neither the
failed test IDs nor the native abort cause. The parent thread happened to be
in a different later case on each attempt. Repeated stack location is not
proof of why the interpreter aborted.

The root independently proved the earlier inherited-plugin child import
failure. That explains an additional defect in the first diagnostic harness;
it cannot explain a repeat with no inherited plugin. Original pass18's
74.932779 ms GTK click also remains separately unexplained.

## What the passing prefixes establish

Both bounded prefix observers first collect the normal modules, then mutate
`items[:]` and report later items deselected. The canonical prefix retained
1,061 cases after the separate-Orca rule and deselected 8,711; all 1,061 pass.
The initial hook selection counted 1,062 before that rule. Preserve that
distinction when reporting results.

This is useful evidence against a defect reproduced simply by importing the
later modules. It does not retain the complete `session.items`, every later
item's active lifecycle, fixture scheduling graph, or the same retained-object
and garbage-collection pressure as the full run. No examined early fixture
reads `session.items`; remaining item retention is an observation variable,
not a demonstrated cause. Separate Orca is another execution difference;
private process isolation does not eliminate host scheduling differences, but
there is no evidence attributing the abort or failures to scheduling.

Root's next admitted run therefore keeps the complete item list untouched,
uses the canonical main environment and private 72-DPI display/session, removes
the collection hook entirely, retains `--maxfail=1`, and immediately records
the actual first failure. It is a bounded diagnostic, not final acceptance.

## Observational constraints and useful next evidence

- Write each failed setup/call/teardown report immediately as scalar JSONL:
  exact node ID, phase, wall time, exception text and thread identities/stacks.
  Keep the active node ID as a string. Do not keep raw frame, exception,
  traceback, widget, Variable or interpreter objects in the observer.
- Keep plugin loading parent-only using `-p`, not inherited
  `PYTEST_PLUGINS`; do not patch Event, Thread, GC, GTK or toolkit classes in
  this first-failure capture. Do not increase timing bounds or release a test
  barrier early to manufacture a pass.
- If the first failure is confirmed as pass14 launch ownership, inspect its
  exact assertion and cleanup stack. That test's own `finally` sets both
  barriers, closes the worker, joins every spawned thread, and asserts none
  survives. A normally completed pass14 case is not supposed to leave its
  `active()` worker alive. The fatal stack alone does not show that cleanup
  completed, which worker instance it belongs to, or when it became active.
- If the six suspected checkbox collection failures are confirmed, retain
  their `local_trace_release` properties and actual alive-reference statuses.
  Observe only `id` and type names for immediate referrer summaries, and
  discard temporary referrer lists on the UI thread before continuing.
  Do not retire product traces before the existing assertions.
- If a native abort recurs before a useful failure report, preserve an
  available owned-process native crash/core trace and native stderr first.
  Python's faulthandler stack names the thread collecting, not the C destructor
  or interpreter that caused the abort. Do not label this a Tcl wrong-thread
  destruction without a corresponding native diagnostic or controlled proof.
- A later, separately admitted observer may append a minimal `gc.callbacks`
  callback recording only phase, generation, current thread ID/name and the
  active node ID. It must never call `gc.collect`, disable collection, inspect
  all live objects, retain referents, or touch a toolkit. This would establish
  collection-thread timing; it still cannot identify a C-level tkapp destructor.
  Optional weak-reference finalization logs for already-owned Python roots or
  Variables must capture only IDs/strings and avoid retaining those objects;
  they are additional diagnostics with measurable observer effects, not proof
  of actual Tcl interpreter destruction by themselves.

The source audit also identifies failure-cleanup risks in several older
`test_audio_responsiveness.py` cases: barrier releases follow assertions rather
than being guaranteed by `finally`, while the shared worker fixture only
performs its bounded `close()` wait. Those risks need exact forced-failure
cleanup proof before any fixture correction. They are not an attribution of
the canonical failure or abort. No speculative source fix is proposed here.
