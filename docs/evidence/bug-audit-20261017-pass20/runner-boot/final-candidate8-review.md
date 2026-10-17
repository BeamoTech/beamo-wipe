# Candidate 8 — final selected source review

2026-10-17 / Codex `/root/pass20_runner_boot`; BeamoTech/beamo-wipe,
`fix/safety-audit-20261015`, HEAD35107a8d1a701093eac876a58ab4efd50e291673.
This review covers three runtime files and eight canonical regression modules,
with exact hashes in the JSON receipt. Source/artifact parsing only; no product
imports, tests, GUI, native actions or product/test edits by reviewer.

No additional source objection remains for these exact11 inputs. Current Tk
SHA256 is `3f702e1ac6c3564372f9b633a2dcf0ea3e9d46553e29ceaf4cfa781e181e8ea7`.
All779 current frozen inputs and archived bytes authenticate. Exactly three
of771 starting inputs changed, eight test modules were added, and768 starting
inputs are unchanged. The independently recomputed58-file runtime hash is
`c3a9b4c2145e86203eb7669e5073b0fb7de0a932eb2920b5b881c58fba6af2aa`.
This supersedes the selected-source approval for candidate7; its failed gate
and earlier successful focused evidence retain their original source scope.

Candidate7 to8 changes one native factory and one navigation predicate.
The factory pins every successfully allocated native wrapper before calling
its initializer, together with the caller's interpreter. A later widget
initializer can fail before the caller adopts a successfully initialized
local variable into a widget/field. The earlier failure-only pin omitted that
ownership edge. The new strong record covers it while ordinary local/field/
traceback references still prevent sole-owner retirement. Factory return,
original initializer arguments, callable test factories, creator identity and
asset-before-raw-interpreter release remain intact.

For an Image subclass with no instance `name` yet, the factory establishes
`name=None` before initialization. The installed native Image initializer uses
that same initial state before allocating its Tcl handle; its unchanged
destructor tests that name before deleting a handle. A failure before the
original initializer's first statement therefore remains safe. Successful
initialization still assigns the original native image name. This neither
neutralizes the original destructor nor edits an existing native handle,
exception or traceback. The image probe calls the original initializer and
destructor, observes unraisables without retaining their objects, and retains
the original injected exception until the worker-release boundary.

The navigation guard now uses `getattr(self,"_ui_dead",False)`. Actual TkWizard
dead-state behavior is retained; existing lightweight controllers without that
field regain their established screen/generation guard. The failed candidate7
full gate explicitly proves that compatibility regression. Its original
assertions remain unchanged, and all25 busy-transition cases pass in the fresh
focused run. No owner/token/countdown/erase condition was relaxed.

Only `_new_owned_native` and `TkWizard._nav` differ from7. All other functions
and methods are AST-identical, including pools, native root construction,
teardown, startup, GC callback, timer cancellation and exception preservation.
Audio/discovery still match the earlier independently reviewed exact fixes.
All other768 starting inputs, including the engine, methods, authorization,
completion evidence, recovery, power and export modules, are unchanged.

The expanded constructor module matches the v5 child/assertion proof, adding
only the two row-Frame injection cases to v4. Existing76 assertion ASTs are
unchanged. The new three-case image module matches its child and all30 assertion
predicates; one admission assertion's diagnostic wording is normalized.
Canonical adaptations also include the header, admitted source fallback and
explicit parent-to-child path/hash propagation. The other six canonical modules retain
their reviewed bytes. Original native destructors, external peers, retained
tracebacks, timeout limits and application side-effect guards are preserved.

Independent completed XML readback: candidate7 row-Frame proof2FAIL; candidate7
image proof1FAIL/2controls; candidate8 focused106PASS, zero failures/errors/skips.
The final149 canonical cases replayed on all58 authenticated original source
inputs produce88 failures and61 controls, zero errors/skips. That includes86
AssertionError failures and two controlled unhandled RuntimeError constructor
failures. These are separate original/fixed runs, not a passing full gate.

Candidate8's full nine-phase local gate, fresh campaigns/captures, owned-child
stderr/finalization readback and final retention remain root-owned. Candidate6
pressure/focused results are not relabeled as candidate8 acceptance. Python3.11,
ISO/QEMU, native Windows, physical/firmware/reconnect acceptance remain unrun or
blocked as separately recorded. Historical abort/signal/latency attribution is
unchanged. Source approval does not mark pending or failed checks passed.
