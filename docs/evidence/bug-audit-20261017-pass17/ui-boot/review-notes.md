# Pass17 UI / startup / boot source review

2026-10-17, Codex UI/boot peer. Source review only so far; no runtime, remote, build,
privileged, physical-device, power, or native launcher acceptance invoked.

Reviewed Tk/GTK/curses action dispatch, held-key guards, stale generation callbacks,
refresh worker publication, countdown arrival/overlay handling, authorization/start
claims and interface-loss settlement; Tk/GTK startup presenter lifecycle and app
fallback; live entrypoint, systemd kiosk/recovery supervisor, ISO staging/publication
and current CI surface boundaries. Existing dirty pass8–16 work is preserved.

Supported source candidate: startup Tcl timer lifetime, detailed in
`source-candidate.md`; prepared 16-case native regression remains unrun pending root's
serial runtime admission. No product edit yet.

Rejected or unresolved source hypotheses (not findings):

- GTK modal default actions bypass key-hold guard: pass16 explicitly registers modal
  keypress bookkeeping; same-server-timestamp pairs and held presses are consumed.
  Current generation checks also reject actions from replaced screens.
- A newly enabled final-review button may auto-start: timer only updates sensitive
  state; GTK Return additionally requires a currently focused enabled action, Tk
  requires a physical new press, and shared launch claim rechecks authorization.
- Returning from keyboard/report/advanced detours preserves elapsed review: the
  shared `_return_to_screen_locked` renews Last Chance's full interval; modal review
  depth blocks erase and renews on final exit. Console tracks actual painted review
  lines/pages before releasing its overlay hold.
- Refresh results apply to a replaced screen: shared sequence claim validates its
  current refresh; graphical workers only publish a result, UI timer owns mutation.
- Recovery menu may power down with uncertain engine state: it requires literal
  RESTART/SHUTDOWN and pgrep exactly rc1; missing/broken lookup blocks. No disk
  discovery or nwipe execution exists in the recovery menu.
- ISO local output replacement could discard unowned prior data: source retains
  prior bundle checksum/identity verification, nofollow regular file checks,
  source-input digest binding and same-inode finalization plus scoped rollback.
  This is source review, not isolated ISO acceptance.
- CI silently turns a canceled/native gate into success: Linux/Windows gate needs
  require both exact `success`; CI is secret-free and publication remains separate.
- Preview flags on live image look surprising: explicit live-session override
  deliberately strips fake/gallery/boot override flags before the safety-gated live
  wizard; this is existing documented contract, not a demonstrated regression.

No new safety-law, method, nwipe flag, claim, build or publication change proposed.

Root subsequently authenticated the original startup proof: 10 intended
AssertionError failures / 6 controls, no error/skip, with explicit deleted
`focus_force` / `poll_once` command names and after IDs. The authorized minimal
startup fix now records only its current polling timer and initial focus idle
ID, clears the current poll ID when dispatched, and cancels both IDs in finally.
Cancellation works after external widget destruction because it does not depend
on the deleted widget command registry. It preserves peer interpreter timers and
unrelated scripts. No owner-sweep refactor, toolkit event pumping or review/safety
state change. Exact incremental diff and initial/final hash receipt saved in
`startup-retirement.diff` and `startup-source-review.json`. Final runtime pending
root's sequential campaign. Peer has run no runtime campaign.

Plain TTY typeahead became a second supported candidate in root's initial proof:
Everyday early/middle/late PTY cases reached the fake engine. Initial 18-case run
was 15 failures / 3 passes because 12 Extra/QuickZero fixture cases failed before
PTY creation: changing an already authorized method correctly clears token input.
Fixture now returns to CONFIRM and explicitly re-enters the exact token for every
method before Last Chance. All prior assertions retained; state assertion added.
Corrected proof pending root. Console product source is still unchanged.

Root authenticated corrected plain PTY proof: 9 intended early-ERASE failures /
9 fresh/cancel/EOF controls, no error/skip, with ERASE queued while disabled and
consumed after 5.2 fake seconds despite a later fresh BACK line. Root authorized
minimal fix. `_retire_erase_typeahead(wizard)` now executes immediately before
`_answer` after review. It requires valid fd, canonical TTY input, and successful
TCIFLUSH. Unsupported/unusable terminal controls raise EOFError into existing
interface settlement; a real session refuses a nonTTY stream. Fake dry-run and
preview controllers retain nonTTY injected-input support, already barred from
starting NwipeRunner. There is no terminal-mode mutation or nonblocking raw-reader
path. The fix changes authorization behavior, requiring eventual `safety:` commit.

Original 18-case assertions remain. Three partial-prefix cases, one actual default
canonical PTY METHOD/ERASE buffering control, four fake/real nonTTY cases and seven
unusable-control cases expand to 33. The canonical buffering control must show
METHOD's `readline` does not hide ERASE from kernel retirement; if it disproves
that contract the implementation needs revisiting. Native X11 startup 16 tests are
unchanged. Exact two product diffs and final 4-file hash receipt saved. No runtime
executed by peer; root's sequential affected/final gates remain authoritative.
