# Second fake-device bug audit — 2026-10-15

Baseline: `8a5dced72b044f22b8dee168f76a2ea882083124`.
Branch: `fix/safety-audit-20261015`.
Implementation: `57ead7e4304f7f373a0c862ff36335c949f4cf7a`, pushed to origin.
This record covers local source verification, not shipped-image qualification.

Three bounded reviewers revisited discovery/identity, engine/log/evidence,
and boot/recovery/reporting. The primary reviewed wizard transitions, repeated
launches, stop/retry/shutdown, language switching, packaging and build boundaries,
independently reproduced original failures in a private import tree, and reviewed
all resulting changes. Only fake disks, fake process boundaries and regular
files were exercised.

## Findings

- A recovery store retained an old directory descriptor after its public path
  was replaced. It could report quiescence while another owner held the new
  directory's wipe lock. Validate public directory identity at lock/read/write
  boundaries and refuse an obsolete store.
- A report preference read could return obsolete false intent after replacement,
  or a load/save could succeed in a retired directory. Validate the directory
  and the complete file snapshot before returning or accepting a write.
- Lock identity checked during acquisition could change during launch preparation.
  Recheck the named coordination lock immediately before process creation.
- A substituted engine log could provide unrelated completion or telemetry.
  Bind reads to the validated launch log and retain its open descriptor throughout
  process ownership. An intermediate device/inode-only implementation failed an
  independent unlink/recreate trace because inode reuse was immediate; that
  implementation was rejected. The descriptor prevents reuse during execution.
  Pinned nwipe's [logging implementation](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/logging.c#L324)
  appends to its log; it does not intentionally replace the inode.
- Concurrent start preflight could outlive another ambiguous spawn and reach a
  weaker second admission guard. Preserve retained ownership at both guards.
- Translated discovery uncertainty reasons were omitted from inventory warnings,
  including snapshots retained across language changes. Match all supported
  translations while preserving definite exclusions.
- Inventory available/unavailable counts remained English in French/German
  sessions. Use translated zero/singular/plural templates.

The descriptor transfer and cleanup paths also have regression coverage for
failed transfers, ambiguous process creation and confirmed cleanup. Existing
fixtures now use actual regular log files and retire their descriptors.

## Verification

The baseline-compatible regressions produce **44 intended failures / 19 passing
controls** against a private copy of the exact baseline source. No checkout
reversion was used. [Original reproduction](original-reproduction.txt).
The fixed source passes **71 new regression and lifecycle tests**, including
eight additional descriptor-lifetime/transfer cases using the new internal API.
[Fixed regressions](fixed-regressions.txt).

Independent review repeated the inode-reuse attack 1,000 times: the retained
launch inode could not be reused, replacement evidence was refused, and
cleanup closed the descriptor. [Original trace](inode-reuse-original.txt),
[fixed trace](inode-reuse-fixed.txt). A separate **76-test** in-process review
found **zero surviving temporary-file descriptors**; another 20 adjacent checks
passed. [Descriptor review](independent-descriptor-review.txt),
[adjacent checks](independent-descriptor-adjacent.txt).

All applicable local source gates passed. [Final summary](final-summary.txt):

- [Complete pytest](final-tests.txt): **5,787 passed / 14 image-dependent
  skipped**, no failures, in 519.90 seconds. Mandatory GTK result guard passed.
- Separate private-session Orca: **one passed**. Combined: **5,788 passed**.
- Remaining skips: two generated live-build-config cases and 12 manufacturing-ISO
  cases. No browser, GTK, QR-decoder or Go-renderer dependency skip remains.
- [Lint/types](lint.txt), [preview](preview.txt) and
  [safety mutation](negative.txt) phases passed through the existing local
  `scripts/ci-hosted.sh` child mode. The mutation intentionally fails in a
  private import tree, then the pristine source passes.
- Go 1.26.8 [race tests](go-test.txt), [vet](go-vet.txt) and
  [firmware-parser fuzz](go-fuzz.txt) passed, with **350,000 executions**.
  Native inventory override remained unset.
- Actual Tk `./preview` welcome screen inspected at 72 DPI: no clipping.
  [Screenshot](tk-preview.png). Web/console/helper generation and supported
  language JavaScript syntax checks passed separately.

The final full test command used the existing `.venv-linux` through the
no-space `/tmp/beamo-wipe-audit-python` alias, pinned Go on PATH,
`GOTOOLCHAIN=local`, `BEAMO_GATE_CHILD=1` and an explicit temporary JUnit path,
then ran `./scripts/ci-hosted.sh tests`. That script runs separate private
D-Bus/XDG/Xvfb sessions for speech and the main suite, at 1600×1000 and 72 DPI.
Pinned dependencies match the project gate (pytest 9.0.3, Playwright 1.63.0).
No dependency simulation tests or runtime guards were weakened.

[Source/test hashes](source-sha256.txt) cover all 19 changed implementation and
test files. They match the frozen test input and committed implementation.
No source or tests changed after the final gates. Transcript trailing whitespace
is normalized for Git. Lint's existing TODO warning matches the placeholder
regex in unchanged `release_manifest.py:40`; mypy untyped-body notes are
informational. No unresolved source lint/type error or material warning remains.

Other focused review evidence: 273 wizard confirmation/refresh/stop/retry/shutdown
cases, 108 inventory/language cases, 812 recovery/report/boot cases under private
72-DPI D-Bus/Xvfb, and 494 affected runner/evidence/cancel/retry/security cases
passed. These overlap the final suite and are not added to its total. An earlier
display-less recovery run failed GTK initialization; it is not counted as a pass.

## Limits

No physical disk was modified, no guest started, and no ISO built. ISO/QEMU,
native Windows and physical firmware/media/reconnect acceptance remain unrun
for this source. They belong to separately controlled public-candidate
qualification. The T3 browser opened the generated preview but its snapshot
client failed; no successful interactive inspection is claimed. Repository
browser regression tests are separate evidence.

Large-log crash recovery conservatively retains only authenticated suffix
evidence. A fake trace with a valid early completion record followed by more
than 1 MiB of controller padding produced an initial verified result, then
`indeterminate` on recovery when the completion record was outside that suffix.
This is a deliberate refusal without enough retained evidence, not a false
success. Expanding the recovery format was outside this minimal-fix pass.

Implementation was committed and pushed only after all applicable local gates
passed. A read-only GitHub check confirmed no open branch PR; workflow inspection
confirms PR/main triggers. No hosted CI, PR, deployment or release was performed. See the canonical
[unfinished-work record](../../../.ai/memory/unfinished-work.md).
