# Runner source change ready for primary verification

2026-10-17 / Codex `pass17_runner`. Product edits were made only after the primary
authenticated a stable 448-case original replay: 250 AssertionError failures,
198 passing controls, zero errors/skips. The earlier 396-case central run loaded
the prior module before the approved controls were expanded; it must remain a
separate result and does not authenticate the final test bytes.

Only `src/beamo_wipe/nwipe_runner.py` was changed in this product scope. The
`runner-pass17.diff` compares against the primary's archived starting source;
the archive's runner SHA matches `reviewed-start-sha256.txt`. Accumulated previous
runner fixes are preserved in `runner-accumulated.diff`. The first proposed source
hash remains in `proposed-final-sha256.txt`; it is superseded by the correction
record below and `negative-origin-final-sha256.txt`.

The parser now recognizes the complete timestamp/severity prefix already
emitted by nwipe v0.42. If any such record exists in the provided log, skip/open/
geometry attribution requires that prefix on the matching line. A bare or
short-prefix continuation inside a device model therefore cannot support an
unchanged-disk claim; the ordinary exit/missing-completion reasoning applies.
Entirely bare legacy parser inputs keep their existing behavior. Genuine full
records retain case/whitespace forms that the existing prefix parser supports.

Large-log projection retains the first timestamped original record at the
point where it occurs. That record is handled by the existing relevant-line
byte counter and limit, so lost initial metadata cannot turn a continuation
into a legacy bare diagnostic. No synthetic trusted record, out-of-order append
or extra uncounted native-context bytes are introduced.

Source review checked method completion remains separate; negative failure and
abort parsing was intended to stay conservative; the later full-gate result
found a negative-context regression described below. Log identity, process status, ownership,
cancellation, authorization, command flags and pins are unchanged. This child
has run no runtime tests, native engine, subprocess campaign, network or device
action. Primary verification remains required for final source acceptance.

## Corrected negative-context regression

The first candidate's runner SHA was
`ddfc855a50cb06816f1f094caefef53acdec562039e9171b163273d396d13441`.
The full canonical primary gate found three existing failures in
test_runner_prefixed_error_context_pass12.py: an unattributed bare skip marker
plus genuine timestamped target-error activity must remain indeterminate. The
first origin filter discarded that bare marker from the contradiction check
and returned engine_failed instead. The failed gate and candidate patches are
preserved; this is a regression in the first proposal, not a test defect.

Before correction, the primary authenticated all108 AssertionError failures in
the exact evidence-local negative-origin-proof.py plus the three existing
failures / three adjacent controls, zero errors/skips. Those108 bytes were copied
unchanged to tests/test_runner_mixed_log_origin_pass17.py; the earlier448 module
and every existing assertion remain unchanged. New coverage combines three
guards, three methods, canonical progress/error-summary/status activity, both
record orders and short / actual >1MiB ordinary-file fake-process paths.

The correction adds only the internal enforce_origin keyword to the record
helper. Its default keeps the original no-erasure proof requirement. The
negative-only contradiction gate also searches for raw guards with origin
enforcement disabled: such a sentence cannot prove an unchanged disk, but still
blocks a positive completion or a definite no-erasure explanation when actual
erase activity contradicts it. A lone forged marker with no activity still
follows the ordinary nonzero-exit/missing-completion path. Projection context
retention, order and byte-budget handling remain unchanged.

Corrected runner SHA:
`465d3495bd36b3be2507798ad3b57930645c165ba025a2afbe2ea0ca6c45e39d`.
The old failed-candidate source and incremental patches are retained separately;
candidate-lineage-sha256.txt and negative-origin-final-sha256.txt authenticate
them and the corrected source/test bytes. This child ran no runtime verification;
the primary owns the affected regression and final full-gate outcomes.
