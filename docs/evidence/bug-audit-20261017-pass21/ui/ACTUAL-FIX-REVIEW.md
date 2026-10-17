# Pass21 selected Tk/GTK implementation review

2026-10-17 / Codex `/root/pass21_ui_lifetime`; BeamoTech/beamo-wipe,
`fix/safety-audit-20261015`, HEAD35107a8d1a701093eac876a58ab4efd50e291673,
checkout `/root/dev/Beamo Wipe`. Source-only review; no application imports,
Python invocation, tests, native runtime or source/test edits by this child.

Reviewed exact implementation bytes:

- `src/beamo_wipe/ui/tk_wizard.py`: `5b1fc0e16f95176ae706a9677d082d2daae7eb3d70a43ce244ce77363e35f9f5`.
- `src/beamo_wipe/ui/accessible_wizard.py`: `dd2484ff669d1d08f4fa7927200517de07b420708094cd3249af5406fd0aac97`.

The four previously unbound Variable call sites now pass master=self.root:
the two persistent StringVars, persistent IntVar and comparison BooleanVar.
Existing report preference/share locals, Fonts and Images retain their explicit
owner binding. This uses the existing owned native factory and ordinary native
initializers; it does not replace Tk's default-root policy or touch peers.

The new `_new_owned_trace` implements the reviewed plan. Native Variable type
admission uses the captured real Variable base. The temporary shadow belongs
only to that exact instance and delegates its previously resolved `_register`
callable. The first registration with the exact callback object adopts its
token into the supplied owner's known field before trace_add can fail after
native registration. Subsequent peer registrations do not replace that token,
including another registration of the same callback object. Finally restores
the previous instance value or deletes an absent-before shadow only if its own
shadow is still installed. A peer replacement is preserved. The ordinary
trace_add return/error remains; fakes retain the ordinary API branch. The three
owned bindings use this helper and the existing teardown retires only their
known exact tokens. No token-difference deletion or peer cleanup is introduced.

Retained original exception frames can retain the helper's native Variable,
owner and original callable. Pass20's unchanged native asset/raw interpreter
pools already own those resources until the creating thread can settle them.
No destructor, traceback, product GC mode or threshold is neutralized/changed.

Both refresh launch methods now construct the Event within the failure-handled
scope. The actual worker waits, then reads permission under the refresh lock.
The UI holds that same lock while notifying and publishes permission only after
set returns. A notification that wakes the worker then raises therefore still
leaves permission false when the worker obtains the lock. Actual discovery runs
after releasing the lock. Thread launch/registration and Tk poll scheduling
remain in the guarded scope. Rejection wakes a late-spawned worker while
permission remains false, clears Tk's selected thread registration and resolves
the existing claim through finish_refresh using the original exception.
Additional wake failure is reported without bypassing claim settlement. Event
constructor failure has no worker to wake. This does not add real-device I/O or
change discovery/authorization rules.

GTK close now runs optional audio cancellation, dialog closure, exact timer
removal, window destruction and main-loop exit independently, collecting their
BaseExceptions. It clears the owned timer before attempting removal and keeps
close idempotent. After all independent cleanup, it raises the first exact
exception object and notes later cleanup failure types. A cancellation failure
can no longer prevent window/loop cleanup or make the early closed flag block
all remaining cleanup. Engine settlement remains the caller's established
responsibility; no erase launch, completion or power rule is changed here.

Compared these four canonical UI modules against their immutable proof inputs
using complete textual diffs:

- `tests/test_tk_variable_interpreter_pass21.py`: `a1adfa3427496bdb425dd780cef667d4ed5ae3eb10b76230848a84a3086f0e7d`.
- `tests/test_refresh_acceptance_interruptions_pass21.py`: `44b5083fff5432658f4a943354789c891e43d94fd66ea3986caa1858c8906b24`.
- `tests/test_tk_trace_adoption_pass21.py`: `c042b2cb2a99996fc4796e2a07ea3e661adeac01daccef33a11494ddd2385d44`.
- `tests/test_accessible_close_cleanup_pass21.py`: `17d33a6646acf8471570be2696aafe00cc5b12a754492ccc37d2f4ab55af59a8`.

Differences are canonical headers, normal repository source/hash admission
fallbacks, private-native platform/display skip admission, and explicit
parent-to-owned-child source/hash propagation. Child behavior, controls,
original native destructor observation, exception identity, exact peer traces,
original source failure assertions and eight-second child limits are unchanged.

Read root-owned status/JUnit headers, without executing them: corrected native
original11 cases have8 failures/3 controls; fixes-focused338 and canonical213
cases have zero failures/errors/skips and exit0. This is limited evidence
readback, not this child's runtime result. The old invalid BooleanVar string
proof and less strict original finalizer observer remain separate history.

Last requested bounded interleaving proof is prepared, not executed by this
child: `realthread-refresh-proof.py`, SHA-256
`c843f143e4d0b4b2fa78e97c0adfbcbec7df52a8f8bfd7e98d1a7f2080dbc1dc`.
Its six cases use only actual owned Threads/Events, fake controllers and fake
discovery. Only the first UI launch gate is controlled; Thread._started uses an
original Event. set-after/normal wait for the worker to pass its real wait
before its production lock acquisition, forcing the interleaving under review.
First result/state/scan/alive data are captured before fixture release. Cleanup
uses only captured original inner Events and positively owned Thread handles.
Rejection checks exact original exception, resolved fail-closed state and retry.
No GUI, process, native disk operation, signal or external service is invoked.

No additional source objection to these exact two implementation and four
canonical UI test inputs. Root still owns actual six-case original/fixed
interleaving proof, adjacent and final full gates, complete artifact/source
freeze/readback, independent broader review and qualification. This selected
source review does not mark pending checks passed or establish Python3.11,
native Windows, ISO/QEMU, hardware or historical incident attribution.
