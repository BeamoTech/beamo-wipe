# Pass15 exact current patch review — source only

2026-10-16, Codex delegate /root/pass15_runner. No source/test edits or runtime
campaign occurred during this review. Compared every member of the primary's
58-file starting-source.tar.gz against current source; seven files differ.
Read the complete seven incremental diffs and four new regression modules.

**Disposition: approve the runner/evidence/advisory changes at the exact hashes
in patch-review.json; no source-level objection found.** Runtime acceptance
remains primary-owned; this review does not substitute for final required gates.
Discovery and Tk changes were additionally inspected for effects on runner,
recovery, export and authority boundaries, with no source-level objection; their
primary focused/native evidence and independent safety review remain necessary.

## UTF-8 snapshot bound

- Only a documented constant is added to nwipe_runner; raw capture, scanner,
  assessment, signal/stop/lock/launch and completion marker paths are unchanged
  relative to the exact starting archive. The old larger git diff contains
  retained prior fixes and is not this pass's change.
- 3*raw bytes is a tight upper bound on UTF-8 re-encoding after errors=replace:
  one invalid raw byte may become one U+FFFD encoded in three bytes. Complete
  valid UTF-8 is unchanged; a cut codepoint can expand only at its boundary.
- outcomes keeps strict int/not-bool, positive size, checksum shape, exact method,
  completion reason, exit, interruption and verification consistency checks.
  The cap remains finite. The import is lazy and occurs inside the semantic
  interpreter after normal module setup; no initialization cycle is introduced.
- The bound is below existing export limits. read_export_log already reconstructs
  and authenticates the exact normalized raw capture; no optional log or digest
  bypass is added. recover_result and successful export still independently
  require exact snapshot bytes and method-aware completion markers. Quick zero
  retains unverified presentation and cannot become verified.
- tests/test_utf8_log_snapshot_bounds_pass15.py covers30valid source/cut cases,
  three actual near3x normalization cases and five invalid/over-cap metadata
  controls through real fake-process poll and evidence/recovery/export readiness.
  It proves meaningful behavior without mirroring a newly imported constant.

## Positive hidden-storage record

- Only the positive _HIDDEN_NONE body regex changes: ordinary ASCII horizontal
  spacing is retained, the complete device token must end the body, and trailing
  horizontal spaces/tabs remain compatible. Slash/junk/NUL/Unicode line breaks
  and appended uncertainty cannot be interpreted as a passing positive record.
- Timestamped INFO provenance remains required; broad negative/unknown/hdparm
  detection and contradictory evidence precedence are untouched. Genuine
  separate negative records retain unavailable status. Positive fields do not
  alter completion or disk selection; an unavailable advisory does not rewrite
  an independently proved verified/completed result.
- tests/test_hidden_positive_record_pass15.py covers42positive-body variants,
  12separate negative/foreign precedence controls and18actual small/large fake
  runner/evidence cases across methods/device families. Exact logs/checksum and
  unchanged raw bytes are checked. No engine process is launched.

## Adjacent source/test inspection

- DiscoveryResult.physical_observations is default-empty safety-only context;
  it is not a picker or token peer source. SessionStore serializes Disk records
  from discovery.disks and reconstructs a non-authorizing recovery context, so
  the new DiscoveryResult field does not change journal Disk schemas or restore
  erase authorization. Export continues to recheck fresh physical/rdev evidence.
- _physical_observation deliberately omits display/layout fields yet validates
  safety identity/size/bus/readonly/mount facts; contradictory same-path facts
  refuse instead of allowing a filtered row to hide them. Existing mounted
  metadata refusal is retained. The final boot guard includes retained facts.
- Physical regression module exercises omitted alias bridges, all orders,
  contrary/unrelated controls, final guard reset, same-path conflicts, clean
  retry, isolated pathless row and partition identity fallback. Native path and
  process boundaries are explicitly guarded; no actual target can be opened.
- Empty Tk prose traversal now stops at Text/Listbox/Treeview/native/custom
  scrollbars and nested scrolling canvases. Those controls retain their own
  wheel handlers. Plain prose still routes to the outer canvas. No focus,
  authorization, token, countdown or state mutation is added by this edit.
- Wheel regression module verifies native XTest button dispatch plus platform
  MouseWheel, reader vs outer ownership, immutable text, preserved focus/state,
  redraws, text sizes/resolutions and custom scrollbar behavior on isolated X11.
  It forbids shared :1/:99, source/native effects, and cleans owned Tcl timers.

## Verification boundary

Primary reported an early574-case check with all38UTF8 and72hidden cases passing;
this delegate did not rerun those tests and does not relabel that report as an
independent runtime pass. Tk placement correction rerun was still active when
this source review was requested. Use the primary's final exact-source receipts.
