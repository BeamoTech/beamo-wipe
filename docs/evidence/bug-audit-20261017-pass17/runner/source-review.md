# Pass17 runner source review

2026-10-17, Codex child `pass17_runner`; branch
`fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Source-only review initially;
no runtime, real engine, network or privileged/device activity.

Reviewed scope: start preflight and lock ownership, argv construction, process
status polling, concurrent poll/cancel, bounded tail identity and whole-log
projection, method-bound completion, advisory checks, saved-evidence semantic
presentation, shutdown liveness gate, three-part recovery copy. Reviewed source
and adjacent regression hashes are in `reviewed-start-sha256.txt`.

Candidate awaiting an admitted pure fake-log test: a model's internal LF can
forge a bare `Unable to open device '/dev/sda'.` or
`No sane device geometry for '/dev/sda'.` record. Each phrase plus its leading
LF fits in ATA's 40-byte model. This is the same established input mechanism as
`tests/test_nwipe_model_status_injection_pass38.py`, which documents bookworm
libparted preserving the LF and nwipe's initial device-info logger emitting it
verbatim. The current `_target_has_record` strips optional prefixes and accepts
the continuation line. With nonzero/signal exit and no logged progress/status,
the result is classified before the exit-code failure as `open_failed` or
`geometry_unusable`. Recovery then says `Nothing was erased. This disk is
unchanged.` Absence of progress does not prove the engine never wrote. The
existing activity contradiction guard prevents this only when recognizable
activity survived in the log. Existing pass14 model tests use same-line text,
so they do not cover internal LF continuation.

Potential remedy must preserve conservative handling of actual failure records
and existing bare-log public fixtures. Options need primary review: keep such
bare records as non-success evidence but require genuine timestamped engine
record provenance before making the stronger no-erasure claim; or recognize
device-field continuation context without weakening existing parser contracts.
No product edit is proposed until the original case is proved and the exact
contract is agreed by evidence.

Rejected / non-findings so far:

- A wait/status error retains registered process and locks; exception paths do
  not publish a clean cancellation.
- A launch interruption with no Popen handle retains the wipe lock, and
  `Wizard._runner_is_active` explicitly checks it before shutdown/retry.
- A close/unlock failure blocks terminal publication and future runner starts.
- A complete Erased row is method-bound separately; incomplete or conflicting
  initialized counters invalidate completion. Quick zero never sets verified.
- Status-column collisions, partial UTF-8 tails, truncated final records and
  altered log identities already have conservative handling and regressions.
- An advisory unavailable check does not rewrite an independently validated
  erase outcome; advisory missing/malformed data alone is not a completion bug.

Prepared regression: `tests/test_runner_model_lf_noerase_pass17.py`, 448
parametrized cases expected; no runtime performed by this child. The primary
must authenticate actual collection and result counts. Expected original result
is 250 assertion failures / 198 passing controls. The file is frozen at the
hash in `pre-proof-test-sha256.txt` pending primary original-source proof.

Coverage includes all three methods, three fictional device spellings, four
terminal exit values, actual >1MiB regular-file logs with an exited fake process,
canonical timestamp/severity prefix case and whitespace forms, seven forged
optional prefix forms that still fit the 40-byte model, legacy entirely bare
parser inputs, activity contradictions, original projection order and the
existing evidence-byte budget. Fixtures reject subprocesses, native inventory,
rediscovery and native path opens; `/dev` realpaths are fixed fictional strings.

Primary-approved proposal for proof review: detect the presence of any complete
timestamp/severity engine record, and in that context attribute no-erasure
markers only to timestamped records. Entirely bare legacy input behavior remains
explicit. The first canonical original record must remain in large-log
projection at its original location and count toward the existing evidence-byte
budget. Do not invent a synthetic trusted line or append context out of order.

Evidence callers independently rerun `completion_for_method` on the assessed
whole-log view, and authenticated recovery reruns no-erasure reasons against the
retained exact snapshot. No schema change is required. Generated/saved semantics
should be exercised after the source fix if the primary confirms the candidate.
