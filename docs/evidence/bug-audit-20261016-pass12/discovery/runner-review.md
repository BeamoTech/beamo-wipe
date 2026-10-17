# Independent source review of pass12 runner candidate

Reviewer: discovery child, 2026-10-16. Reviewed exact starting-source diff against
`/tmp/pass12-runner/nwipe_runner-before.py`, the new 101-case regression module,
positive/negative completion paths, scanner relevance/record preservation,
`engine_checks` consistency, no-erase contradiction detection and poll/cancel
callers. Hash receipt: `runner-review-hashes.json`; exact diff retained.

Result: source change approved, subject to the parent's original-source proof
and the still-required serialized focused/final validation. No blocking source
objection found. No test campaign was run by this reviewer for this review.

The root cause is specific and supported by the code: Error Summary headers
already consume an engine record body, but target column matching/count parsing
and the table delimiter used the raw record. A prefixed nonzero or malformed
matching row could be ignored before a later genuine Erased row supplied success.
The change computes one body per record and uses it at those three negative
classification points, matching the header's interpretation.

The change does not normalize stored records or exact positive Drive Status
proof. `_target_reported_success` still requires the exact unprefixed LF-delimited
banner; CR, arbitrary model phrases and a bare Erased row cannot gain completion
provenance through this patch. The scanner already retains the raw row based on
normalized relevance; no cap, record/order logic, argv, method or launch path is
changed. `_target_has_erase_activity` calls the same corrected conflict parser,
so a skip/open/geometry report cannot claim untouched media in the face of such
negative activity. Headerless nonzero counts remain indeterminate, shared cells
remain unassignable, foreign rows remain irrelevant and an actual normalized
closing delimiter ends the error table. Natural exit through poll and late Stop
uses the same completion assessment.

The new tests cover the failure and controls across three methods, blank/level/
stamped prefixes, all count columns and malformed counts, small/large ordinary
fake-process logs, late Stop, exact 1MiB boundaries, headerless/shared and no-erase
contexts, prefixed close/model text, zero/foreign controls and unchanged positive
CR rejection. The expected reason assertions are consistent with the code's
conservative outcome rules. No new test opens a device or launches an engine.

Existing advisory parsing may classify a prefixed blank-leading zero row as
unavailable because its level prefix consumes the blank marker. That behavior is
outside this root cause, is conservative, and this patch does not change it.
No speculative change is proposed from that observation.
