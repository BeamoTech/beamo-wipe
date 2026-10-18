# Pass18 final independent cross-review

2026-10-17, Codex `pass18_runner` peer. Source-only review; no runtime,
subprocess/device probe, product/test edit, subagent, commit or push. Exact
starting/final identities are recorded in `final-cross-review.json`.

Read the complete incremental diff of all three runtime files against
`/tmp/pass18-primary/starting-inputs.tar.gz`, independently hash-checked those
three original archive streams, and read all four new test modules plus their
imported discovery fixture and adjacent alias/authorization lifecycle code.
All seven reviewed hashes match the primary's final 766-input source freeze.

No source objection remains to these exact bytes:

- Discovery projects only hardware fields from an unusable physical path;
  it does not repair the path or validate unrelated invalid display, transport
  or capacity data. Normal target construction still rejects that row. Alias
  traversal uses hardware identifiers, so a pathless observation can bridge
  protected storage without becoming a target or confirmation peer. Meaningful
  parent identifiers and known contrary WWNs retain their prior authority.
- For malformed/conflicting hardware facts, an unknown path is not a shared
  device identity. The new path-set guards prevent two unrelated pathless
  observations from becoming equal through `realpath("")` or `/dev/`.
  Existing valid candidate-key/unknown-WWN checks remain active and can force
  refusal if a malformed observation overlaps a protected component.
- Curses captures readiness before painting. Enter from a slow waiting frame
  cannot acquire authorization merely because the clock expires during output.
  The guard runs after Enter-hold bookkeeping, so rejecting that press does
  not turn its repeat into a fresh action on the next frame. Existing live
  readiness, paging/overlay suspension and five-second countdown remain active.
  A readiness transition during painting may conservatively defer acceptance
  one frame; it cannot bypass the live gate.
- Tk owns one stored variable-trace token per checkbox row. Its Destroy handler
  filters the event owner, retires the token once, and removes only that exact
  write trace. Surviving rows/observers retain their own tokens. Parent/clear
  destruction reaches the same handler; interpreter teardown tolerates Tcl
  removal errors. Pending widget timers are a separate existing lifecycle and
  are not hidden by this product change.

Test-source review found focused controls for protected versus unrelated or
contrary identities, parent authority, row-order/path spelling, malformed and
conflicting hardware alternatives, two independent empty paths, all methods
and Enter spellings, early/crossing/ready frames, Back and EOF, own/parent/clear
Tk destruction, Boolean/Int variables, live peer callbacks and collectability.
The fake discovery fixture rejects native acquisitions and native-path opens;
UI fixtures reject engine/power/audio/subprocess effects. Tk tests require an
explicit private X11 display and preserve unrelated trace/timer controls.

This review does not substitute for the root's original failing proofs or final
runtime verification. Historical incident/trace and native platform/physical
acceptance blockers remain unchanged. No publication authority is implied.
