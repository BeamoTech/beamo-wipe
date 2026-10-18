# Pass21 UI source review and prepared proofs

2026-10-17 / Codex `/root/pass21_ui_lifetime`, delegated by `/root`.
BeamoTech/beamo-wipe; branch `fix/safety-audit-20261015`; checkout
`/root/dev/Beamo Wipe`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`
plus preserved dirty work. Read the repository guide, top unfinished record,
pass20 README and selected-source review. `/root/dev/AGENTS.md` is absent.

This child performed source inspection and wrote only these evidence/proof
files. No product imports, Python invocations, tests, GUI, native application
effects, devices, subprocess workers, network, guests, source/test edits,
staging or commits. Root owns all actual proof execution and verification.
Every item below remains a source candidate until root's recorded execution
proves it; later actual reports supersede this preparation record.

Read source identities:

- `ui/tk_wizard.py`: `3f702e1ac6c3564372f9b633a2dcf0ea3e9d46553e29ceaf4cfa781e181e8ea7`.
- `ui/accessible_wizard.py`: `2179d1be8dfa960266e611eb0429b1a33670c3ca25111a899355e39a8ca35fed`.
- `ui/sound_dialog.py`: `9165731d320e6f19de3e6632a7b0c43a4c688a72dbd6558b39ba46c0052aed9e`.

Candidate P21-UI-ROOT: three persistent Variables and the comparison BooleanVar
omit `master=self.root`, although `_new_owned_native` pins the supplied root.
The actual Variable initializer still selects Tk's default root. With a live
independent prior root, variables and their Python traces can belong to that
peer interpreter while an Entry references the same variable name in the new
wizard interpreter. Under NoDefaultRoot, construction can fail despite an
explicit owned wizard root. Fonts and Images already pass their root/master.
Prepared native proof v3 retains v2's five ordinary/peer/no-default routes and
adds ordinary/peer CONFIRM semantics. Actual Entry insertion must reach wizard
typing/confirmation state; peer functionality and its exact trace survive.
Original Font/Variable/PhotoImage destructors run and must actually return on
the creating thread; no unraisables or remaining native wrappers are accepted.
Root reported v1 four failures/one ordinary control; this child did not run it.
V1 remains archived; v2 corrects the finalizer observation so returned=True is
recorded only after the original destructor returns. V3 adds behavioral checks.

Candidate P21-UI-REFRESH: Tk and GTK create the launch Event outside the launch
try and set it after publishing allowed=True outside that try. Event creation
or notification interruption can leave a claimed REFRESHING state; notification
that mutates then raises can additionally release a scan after the caller sees
an exception. The eight-case prepared proof uses exact production orchestration
with fake GI/Event/Thread/root endpoints and no real thread/display. It records
the unmade decision wait, rejected scan, state, queue and original exception
identity. Controls apply one fake rediscovery normally. Root's proposed lock
design is sound: worker waits, then reads permission while holding the same
refresh lock that protects UI notification and final permission publication;
set must return before permission becomes true. A woken worker cannot race an
interrupted set. Run discovery outside that lock; include Event construction in
the try, settle the claim even if failure notification raises, and retain the
first original exception. Runtime validation remains root-owned.

Candidate P21-UI-CLOSE: GTK close marks closed before optional audio cancellation
then performs all independent cleanup sequentially. Cancellation failure skips
dialog closure, timer removal, window destruction and loop termination; a later
close returns immediately. Prepared three-case fake-controller proof covers
normal return, RuntimeError and KeyboardInterrupt with exact original exception
identity and idempotency. It imports the exact admitted source with GI stubs;
no GTK/native application executes.

Candidate P21-UI-TRACE: owned trace token fields are assigned after trace_add
returns. If original Tcl registration succeeds and an interruption occurs before
the caller adopts its returned token, teardown cannot remove the owned trace.
An independent peer retaining the actual Variable keeps that Tcl interpreter
and trace alive after window closure. Later peer writes can invoke closed UI.
Pass20 row-trace coverage injects before registration and does not cover this
composition. Prepared trace proof v2 covers row/typing/confirm registration
then original KeyboardInterrupt, plus a row normal control. It preserves exact
original exception identity/traceback and the independent peer's token/callback,
records remaining owned token and later callback errors, and runs original
native destructors on the creating thread. After recording the boundary, only
the fixture's exact known remaining tokens are removed for fixture settlement.
V1 is preserved but unrun by this child; v2 fixes its row BooleanVar write to
True rather than an invalid arbitrary string. Root must execute v2.

Prepared executable inputs and SHA-256:

- `tk-variable-root-proof.py`: `766283a701bd3173da7963432b8530978dfefab9b080f1df1b8b522ae8b7d22c`.
- `tk-variable-root-proof-v2.py`: `c0f9f728fa06c2ddf1064b68d54fdfce4a0b3d25b628179749853cf0675f55ff`.
- `tk-variable-root-proof-v3.py`: `1f6549dd409148e6fab69fe75c145f78a45bde5461fd356f4e6ff51eba4962a9`.
- `refresh-acceptance-proof.py`: `cc5dcc5f778f6f28ebfc721aac2f6e98acf60984cf73bc8c0bcf243cdf8b390e`.
- `gtk-close-cleanup-proof.py`: `c7ac00e1b72ddcac510a63e3eebf3609a487e2e20d20711ab7ae30cd2c8b1214`.
- `tk-trace-adoption-proof.py`: `765969aa60561088c36a746e1205007e663e23f10e519024d6a48260064dd243`.
- `tk-trace-adoption-proof-v2.py`: `430ec2e4f9993a62bc5cf9a4b93debe3c1852b89fd220965621458e14f99dcb8`.

All native parent/child proofs require explicit immutable
BEAMO_TK_PROBE_SOURCE/SHA256 admission, isolated private X11 outside :1/:99 and
eight-second owned child limits. Refresh and GTK close additionally require
BEAMO_GTK_PROBE_SOURCE/SHA256; fake GI loads only that exact admitted file.
None alters product GC thresholds/modes, clears traceback frames, neutralizes
native destructors or erases data. Current native acceptance is Python3.12-only;
Python3.11/live-bookworm and historical abort attribution remain separate.

Remaining acceptance for each candidate: root executes the immutable latest
proof, authenticates concrete original failure/controls, decides the minimal
root fix, independently reviews it and runs focused/adjacent/full required
gates. Root must retain failed and unrun proof versions distinctly. Candidate
scope is frozen here; this child has no additional proposed source change.
