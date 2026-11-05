# Operation progress and timing

The pinned nwipe source (`6082bde060091e66365d852a1877f2ee80c67105`,
`src/nwipe.c`, `signal_hand`) supplies job-wide `round_percent`, round/pass
counters, an engine ETA, and an explicit pass-type marker. These observations
are presentation data; the existing process-exit and completion-log checks
remain the only completion decision. No engine flags, signal cadence, device
checks, or cancellation waits change. Log reads remain outside the runner
lock; publishing progress, phase, and signal-readiness state checks the captured
process identity under that lock. A late poll cannot update a replacement run.

## Phases

Preparing means no engine percentage has been reported since launch. Writing
and Verifying require explicit target-bound engine markers. Blanking is a
write. Syncing and Retrying retain their names because either can happen
between passes. Missing/unknown markers say Phase not reported.

Freshness uses the monotonic time of each **accepted** engine update (a new
parsed target-bound record). Incomplete or malformed log tails are parser
errors, not updates, and do not reset that clock. The runner still requests
SIGUSR1 every 2.0 seconds after the handler is armed. Five missed pulses
(10 seconds) after an accepted update mark the last percentage **old** and
show `No new progress update for …`. Preparing may stay quiet for the PRNG
auto-bench (8×1.0s) plus the first pulse; the first-update grace is 20
seconds. After that grace with no number, progress is unavailable — not a
process failure. Stopping belongs to the cancellation owner, and Finalizing
means process exit was observed and terminal processing/cleanup is pending.
Those known phases, cancellation, and a confirmed process exit are never
shown as stale telemetry. Quiet progress never cancels, kills, or restarts
the erase. The sliding bar animates only during Preparing before the first
number; stale or unavailable progress is static.

## Estimated time remaining

The estimate is omitted unless all of these hold:

- At least six advancing samples span at least twenty seconds, with each
  interval between one and ten seconds. The bounded history holds up to 61
  samples so normal two-second updates can accumulate a sufficient window. Buffered lines count as one observation, not
  invented historical timing samples.
- Every increase is at least one engine-reported percentage quantum, and the
  window spans at least ten quantization units. Floating-point comparison
  tolerance is one millionth of a quantum; it adds no displayed precision.
- The fastest interval rate is no more than 1.5 times the slowest, and the
  measured job-wide projection agrees with the engine ETA within a factor of
  1.5. The larger of those two estimates is displayed.
- This is the final round/pass and final operation: verification for the
  methods that request it, or writing for Quick zero. Earlier writing rates
  cannot predict the unmeasured read-back rate.

Phase/counter/precision changes, regressions, missing data, timestamp discontinuities,
clock changes and gaps clear history. Local wall/monotonic disagreement over
100 milliseconds clears history; engine log timestamps have whole-second
resolution and use a two-second comparison tolerance. Duplicated percentages
cannot renew rate freshness. A regression must catch up to the prior high-water mark before a new
window can form. Unstable or inadequate rates suppress the estimate. There is
no estimate at 100%, during stopping/finalizing, after a result, or after
recovery. The interface never decrements an old ETA between engine samples.

The exact label is Estimated time remaining. Values use less than one minute,
rounded-up minutes, five-minute buckets, or whole hours, never seconds. This is
an estimate of remaining engine work; final cleanup or report-saving time is
unknown. Fast operations and slow quantized streams may never show an estimate.

## Working-screen glance (#132)

Every interface draws the Working screen from the same `ProgressView` glance:
a large percentage, one time line, and the current step. Nothing here changes
parsing, estimate gates or completion checks.

- The percentage is clamped to 99% on this screen even after the runner
  publishes a validated 100; completion is the result screen's job. Before
  the first number the large line is *Starting…* (*Stopping…* or
  *Finishing…* in those phases).
- The time line is *About … left* only when the estimate above exists, using
  the same upward rounding (`progress.time_left`). Otherwise it is *Running for
  …* (elapsed). During earlier steps a note says time left appears during the
  last step; the other estimate-gate reasons stay in the full status text
  used by tests and the preview payload, not on the glance.
- The step line is *Step k of n:* plus *Overwriting*, *Overwriting (pass i of
  n)* or *Checking (verification)*. Unknown steps are hidden; a disagreement
  with the plan shows the mismatch warning. Quick zero plans one step.
- Stale telemetry marks the percentage old and adds the stale explainer as a
  separate warning band. Phase notes and, with an estimate, the elapsed time
  follow as small notes.

`ProgressAnnouncer` paces spoken output: the GTK summary label and progress
bar, and plain console lines, change at once for a new step, progress going
quiet or resuming, or stopping/finishing (at least 5 seconds apart), and
otherwise at most once every 60 seconds. Tk and curses redraw live; they are
not spoken. Whether Orca speaks each change is not yet verified on the image.

## Method-screen time guide

Before anything starts, each method shows a rough range for the selected disk,
for example "Rough guide for this 1 TB hard disk (not promised): 2–10 hours."
It is a planning hint, not a measurement: it never gates, starts or describes
an erase, is not written to evidence or reports, and does not feed the live
estimate above. When the disk size is unknown no range is given and every
method says "Time depends on the disk." instead (#159).

Work is the disk size times the method's full-disk passes from `methods.py`
(every overwrite plus every verification read: Everyday 2, Three overwrites 4,
Quick zero 1), divided by conservative sustained rates:

| Disk kind (from lsblk) | Slow bound | Fast bound |
| --- | --- | --- |
| Hard disk (rotational) | 60 MB/s | 200 MB/s |
| SATA SSD | 100 MB/s | 500 MB/s |
| NVMe | 150 MB/s | 1500 MB/s |
| Rotation unknown | 60 MB/s | 500 MB/s |

A USB transport halves the slow bound only. The fast end rounds down and the
slow end rounds up, each in minutes under 1.5 hours (5-minute steps from 10
minutes), hours under 48 hours, otherwise days. A slow end over 10 hours adds
"Plan to leave it running overnight or longer." Tk cards, the GTK radio names
read by Orca, both console views and the web preview use the same text
(`copy.method_time_line`, which wraps `copy.method_time_guide`; tests in
`tests/test_method_time_guide.py` and `tests/test_method_cards_159.py`).

## Shared presentation and evidence

Every interface uses the same progress view. Displayed integer percentages
update at most once per five seconds; phase changes and terminal results are
immediate. Existing percentage clamping is preserved: 100% is unavailable until
the existing completion check succeeds. Elapsed text changes at minute
boundaries. GTK does not emit redundant text changes, and plain console output
does not repeat unchanged status or device identity on every poll.

Elapsed time uses monotonic time from successful runner startup to the observed
terminal result, including preparation and stopping. The frozen endpoint also
feeds the evidence duration, so slow evidence writes and bounded save retries
cannot lengthen the operation. Wall-clock adjustments invalidate ETA history
but do not change elapsed time. An invalid/backward monotonic clock makes
elapsed unavailable and prevents a valid terminal timing record from being
claimed. Recovery displays only the saved duration, never resumes a timer or
restores an ETA. Live samples and estimates are not written to reports and
cannot become completion proof. Existing volatile evidence and privacy rules
remain unchanged: shutdown or power loss loses evidence unless exported.

Deterministic tests use controllable clocks and fake output for incomplete,
foreign, irregular, duplicated, regressing, multi-phase, fast, slow, stalled,
long-duration and clock-change streams. Rendered Tk/GTK tests cover readable
long-duration text, stable controls and duplicate accessibility events.
