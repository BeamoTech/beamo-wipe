# Independent pass13 Tk source/test review

2026-10-16, Codex discovery reviewer, source-only. No runtime, GUI or test job
was launched for this review. Approved subject to original-source independent
proof and focused/final gates owned by the primary/UI reviewers.

Reviewed exact `tk_wizard.py` SHA256
`8bb8f29eef05e9caba7a41dadafeb30be5cb932afbf2498fedfaae0f3b121c90`
against the pass13 starting snapshot SHA256
`892d9dc27082c84ca5bfa06dc09dc36c90b7b19e23ff402e22c89a861c855fee`.
Reviewed exact `test_tk_input_scroll_pass13.py` SHA256
`615bd14d7d90af70b2e34afa4263bd314447daf852a2fab61e816a927864dd05`.
Read the original focus and hit-tested native wheel traces/test sources and
their retained setup-error correction in `/tmp/pass13-ui/review-notes.md`.

The new native focus request runs once after the actual main loop starts,
preserving the screen's existing intended child via `focus_lastfor()`. It does
not clear held-key/repeat state, schedule recurring focus claims, forward key
presses or invoke a wizard action. Existing child focus, held Return and no
reclaim controls exercise these constraints.

The wheel fix uses the toplevel bindtag reached by descendant labels; the
current canvas ancestry check limits routing to the active body's descendants.
It removes the old canvas/inner handlers so a wheel event cannot apply twice.
Decorative child canvases with no scrollregion can route to the body. Native
Text/Listbox/Treeview/Scrollbar, custom `_Scrollbar` and nested scrolling canvases
keep their own handling; current picker/empty-reader handlers remain unchanged.
Footer and other toplevel widgets do not acquire body scrolling. Redraw uses
the current canvas rather than a captured destroyed one. Existing MouseWheel
integer step semantics and X11 Button4/5 direction are preserved.

All53 prepared cases accounted for:16 native first-key combinations, one held
Return/one-shot focus case,16 prose/canvas/inner/panel wheel cases, five sub-step
delta controls,12 independent-surface/footer cases, one redraw/picker case and
two actual XTest hit-tested directions. Initial native tests park the pointer
at the actual monitor's far corner before window creation, so mapping cannot
accidentally acquire focus and mask the original failure. Tests use fake wizard state and forbid
native application process/discovery/engine/audio/power operations. They verify
unchanged focus/consent/selection and exact single-scroll movement. The private
display opt-in skip is appropriate for ordinary user desktops; the canonical
gate must provide the flag and require execution, which the primary validates.

No authorization, disk identity/eligibility, token/countdown, method/argv,
completion/evidence, build/publication or claims behavior is changed by this
delta. No unresolved source objection identified in this bounded review. This
approval applies only to the exact hashes above; later edits require rereview.
