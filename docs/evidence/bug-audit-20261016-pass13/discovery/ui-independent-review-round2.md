# Independent pass13 Tk review, revised mapped-window implementation

2026-10-16, Codex discovery reviewer. Source-only followup requested by root;
no runtime/GUI/test job launched by this reviewer. The prior approval in
`ui-independent-review.md` is superseded for the focus implementation: the
first actual53-case campaign proved that its initial idle ran before mapping,
losing the intended child in nine cases. Two other failures came from a new
footer fixture mixing pack/grid. Exact failed traces remain with the UI owner.

Reviewed exact final source SHA256
`9d098c65fd501cceabbfa7277037bc3c4225b685e33d3a8b12eed19e3bc05910`
and61-case test module SHA256
`726364bbe995765ce3e869fb8f48d8332b39fee831cef7691600b58406e02648`.
Compared product delta against the exact initial snapshot
`892d9dc27082c84ca5bfa06dc09dc36c90b7b19e23ff402e22c89a861c855fee`.
Read `focus-ordering.txt`, `focus-map-claim-redraw.txt`, original native proofs,
the entire current test module, and relevant renderer/navigation/countdown/
teardown/focus/picker/scrollbar code.

The corrected unmapped path waits for the root's actual Map event, ignoring
descendant Map events. It unregisters only its own Map callback before posting
one idle claim. The already-mapped path posts the same one idle claim without
registering a recurring Map callback. Mapping is assigned before event dispatch
starts, so the closure's binding ID is available when used. Native focus is
claimed once, then the existing renderer restores the intended screen child.
Later tick/configure redraws retain their existing non-forcing focus behavior.
No waits, retries or periodic focus claim are added.

The extra initial `_draw()` rebuilds current view widgets and increments the
existing navigation generation. Captured callbacks from the previous draw
therefore become stale, preserving the navigation guard. It does not execute
button commands, change method/target/ownership/typed token or clear held-key
state. Confirm and keyboard variables are populated from the same wizard state
and their traces write that same value. Owner and Last Chance default focus
remain the checkbox and Back respectively. The constructor has already set
`_shown`, so a same-screen Last Chance rerender does not satisfy
`first_review_draw` and does not restart or consume the clock itself. The added
eight mapped/unmapped × keyboard/owner/confirm/Last Chance cases check intended
focus, exact authorization state and three seconds remaining on the fake clock.

The wheel delta is unchanged from the first review: current-body ancestry,
protected native/nested scroll surfaces, exact once-per-event behavior, footer
exclusion and existing picker/reader handlers remain correctly scoped. The two
footer fixtures now create their label under the existing packed footer column;
the location stays outside the scrolling body and all assertions remain intact.
Native XTest cleanup now explicitly releases its owned button before closing
the private X connection.

Prepared cases total61: previous53 plus eight startup state-preservation cases.
The tests prohibit native application processes and engine/inventory/audio/power
operations. Existing source-level safety gates, pins, claims and build/release
behavior remain unchanged. No unresolved source objection identified. Approved
for these exact hashes subject to primary independent original-source proof,
the UI owner's complete61-case/focused execution and the final frozen local
gate. A previous failed campaign is not relabeled passing by this source review.
