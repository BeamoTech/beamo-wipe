# Independent source review of pass12 UI fixes

Reviewed current source against the pass12-ui `*-before.py` snapshots. This is independent source review only, not a claim of additional runtime or visual acceptance; exact reviewed hashes are in `ui-review-hashes.json`.

No blocking source concern found in the current four-module patch:

- SoundDialog bounds initial geometry to the parent's active monitor, uses native workarea origin, and makes variable-length contents scroll while Close and the live Stop action remain outside that viewport. The existing modal/focus/overlay lifecycle and busy-control guard remain intact. Stop still requests the existing wizard stop confirmation rather than invoking an engine directly.
- A failed remembered-output apply now resolves the backend's actual current default instead of highlighting the rejected preference. The rejected preference is not silently persisted as a new accepted choice. Existing accepted-radio rollback and guarded toggles remain intact.
- Startup graphical refreshes request persistent stall text; default console behavior remains one announcement. Terminal/failed and next-stage transitions clear the persistent condition through the existing state model. No stage is marked done by the note.
- Tk startup retains origin-zero fullscreen geometry by avoiding windowed centering in that mode, and schedules initial keyboard focus on its own mapped root. Escape still runs the existing abandoned-startup flow. Worker thread/poll teardown and success/failure ordering remain unchanged.

No disk discovery, target selection, authorization/countdown/token, nwipe argv/method, engine ownership, boot/USB/host operation or publication behavior is introduced by these UI edits. Runtime regressions, small-screen screenshots, teardown evidence and final exact-source gates remain the primary/UI reviewer's separate evidence.
