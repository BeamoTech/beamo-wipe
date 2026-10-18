# Comprehensive audit, pass 6 — 2026-10-16

Baseline: `6bf8c54ce6b25dd21f8be730f705a54c2c8c3ff8`.
Branch: `fix/safety-audit-20261015`.
Implementation: `ac6ed67c496090c26a9520d0244100ca371ce192`, committed and pushed after all applicable
local gates passed. Source remains unmerged and unreleased.

Fresh bounded reviews rotated discovery/safety, recovery/report/privacy, and
wizard/UI/boot/build ownership. The primary reviewed runner/progress/evidence
integration and independently verified original failures and final diffs.
Only fake targets, fake process boundaries, regular temporary files and
isolated 72-DPI UI sessions were used. No real nwipe, disk operation, VM,
hosted CI, native inventory, PR or release was invoked.

## Reproduced fixes

- Require a full timestamped engine record before arming SIGUSR1 telemetry.
  A model with an embedded LF could forge any of four readiness phrases and
  make the runner signal too early. Eight <=40-byte model cases fail on the
  original source; four genuine records remain supported. Five existing test
  modules now use genuine positive prefixes while preserving their checks.
  [Original proof](readiness-before.txt), [independent review](readiness-independent.txt).
  Pinned [nwipe startup order](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/nwipe.c#L507)
  places device enumeration before the signal mask/handler; its
  [logger prefixes engine records](https://github.com/martijnvanbrummelen/nwipe/blob/6082bde060091e66365d852a1877f2ee80c67105/src/logging.c#L97).
- Preserve validated sharing-copy controls and canonical result prose when an
  identifier collides with words such as `sharing`, `verified`, `a`, method IDs
  or verification flags. Continue scrubbing freeform identifiers, preserve the
  original evidence, and regenerate fixed policy/presentation from the strict
  original result. Known structural text is not a disk identifier. Unsupported
  or contradictory core values never gain a successful verdict.
- Preserve valid sharing results after an English/French/German UI restart.
  Redacted method prose stays tied to its source locale; canonical result prose
  is rendered in the current report language. No outcome parser was loosened.
- Reject malformed nested containers at sharing scalar leaves; warnings retain
  strings only. Otherwise a private identifier used as a dictionary key could
  bypass value-only scrubbing and leak into SHARE.json.
  [Four original shape failures](sharing-key-before.txt).
- Redact all original identifier occurrences in one escaped-regex pass. A later
  identifier could otherwise re-redact an inserted `withheld` placeholder,
  corrupt method prose and make a valid copy indeterminate. Replacement text
  is never rescanned. [24 original failures /12 controls](sharing-placeholder-before.txt).

The 180 new cases produce **120 intended failures / 60 passing controls** on an
exact isolated baseline source tree, and **180 passes** on the fixed source.
[Original reproduction](original-reproduction.txt), [fixed cases](fixed-regressions.txt).
No checkout revert or test guard weakening was used. The privacy module's 168
cases cover all eleven canonical outcomes plus Three overwrites, nine identifier
collisions, all nine locale transitions, owner-original byte preservation,
exported summaries, unknown controls, validated build/clock metadata and malformed
container keys. The original policy ID/version, method flags and erase outcomes
are preserved.

## Fresh independent coverage

Counts overlap the final suite; do not add them as unique passing tests.

- Rotated discovery/boot/classification/authorization/argv/permissions/concurrent
  admission/retry: 415 tests, plus a [364-case controlled matrix](selection-matrix.txt)
  and [script](selection-matrix.py). [Reviewer summary](selection-review-summary.txt)
  labels reported results rather than fabricating raw transcripts.
- Runner/readiness: [189 primary tests](readiness-focused.txt),
  [213 independent readiness/cancel/retry/FD tests](readiness-independent.txt),
  [1,176 completion cases](completion-matrix.txt) using the
  [retained harness](../bug-audit-20261015-continuous/completion-matrix.py).
- Privacy/report/recovery: [482 adjacent tests](sharing-targeted.txt),
  [305 independent tests](sharing-independent.txt),
  [1,408 malformed-core mutations](sharing-core-matrix.txt) with
  [script](sharing-core-matrix.py), and
  [118 nonempty nested-container checks](sharing-container-matrix.txt) with
  [script](sharing-container-matrix.py). Original verdicts and bytes stayed
  unchanged; no planted private marker leaked. A further
  [330 multiple-identifier cases](sharing-multiple-matrix.txt) and
  [harness](sharing-multiple-matrix.py) cover placeholders, overlapping prefixes,
  case variants, all eleven outcomes and English/French/German.
- UI/app/Tk/GTK/console/preview/kiosk/compatibility:
  [955 tests](ui-tests.txt), [358 adjacent async/stop/recovery/power tests](ui-adjacent.txt),
  [20,000 seeded navigation events](navigation-matrix.txt) and
  [harness](navigation-matrix.py). Actual `./preview` was launched at 72 DPI;
  the primary inspected its [fake-preview screenshot](preview.png). Owned
  preview processes were retired.
- Build/asset/manifest fixtures: [242 passed](build-tests.txt), with
  [two explicitly skipped generated lb-config checks](build-skips.txt).
  These are not image or hardware acceptance.

## Final local verification

The first full integration run [failed one unchanged method-redaction test](failed-method-redaction-gate.txt)
(6,089 passed /14 expected image skips). The draft restored too much method
prose. The corrected source keeps both method and verification-scope prose
redacted, restoring machine controls only; the existing test remains unchanged.
The new collision assertions validate machine flags and permitted redacted
prose instead of requiring whole-method equality. A separate
[scope regression](sharing-scope-before.txt) failed on the draft before its
unnecessary restoration was removed. Cross-review then found the distinct
pre-existing multi-identifier placeholder defect above. An early replacement
full gate was deliberately interrupted on exact owned pytest PID269626 for
that fix; its missing-JUnit failure is not a pass. Only the final replacement
frozen-source gate below is the passing result.

Final replacement gate passed:

- [Main pytest](final-tests.txt): **6,127 passed /14 expected image-only skips**,
  no failures/errors, in 484.56s; mandatory GTK result guard passed.
- Private Orca: **1 passed**, giving **6,128 unique passing cases**. The
  [JUnit-derived summary](final-summary.json) confirms no duplicate case IDs
  and lists every skipped check: two generated lb-config and twelve manufacturing-ISO cases.
- [Lint/types/security/shell/developer formatting](lint.txt),
  [preview web/console/helper/JS](preview.txt) and
  [private safety mutation](negative.txt) passed.
- Pinned [Go 1.26.8](go-version.txt) [uncached race](go-race.txt),
  [vet](go-vet.txt) and [350,000 parser fuzz executions](go-fuzz.txt) passed.
  Native inventory opt-in stayed unset.
- All [nine frozen source/test hashes](source-sha256.txt) match final working
  and committed bytes. Runtime digest:
  `f07a27aae8022eed109d8431dcf4227bca2724a6dcc8582e26104d4589c2c1d2`.

The unchanged TODO-regex warning in `release_manifest.py:40` and mypy untyped-
body notes are informational. No unresolved material lint/type warning remains.
Five existing readiness-fixture assertion ASTs match baseline after normalizing
only their genuine positive record prefixes; [all checks are retained](assertion-preservation.txt).

The source gate runs locally with `BEAMO_GATE_CHILD=1`, pinned Go and the
no-space Python-venv alias on PATH, `GOTOOLCHAIN=local`, and explicit scratch
JUnit paths. Suite and Orca use private XDG/D-Bus/Xvfb sessions at 72 DPI.
Pytest 9.0.3 and required GTK/Orca/Playwright 1.63.0/decoder dependencies are
present. No hosted run, dependency upgrade or test guard change is involved.

ISO/QEMU, native Windows and physical firmware/media/reconnect acceptance
remain unrun for this source and require separate public-candidate qualification.
No pinned version, method mapping, authorization gate, claims, nwipe argv,
boot/build/publication control or shipped surface boundary was relaxed.
The canonical [unfinished-work record](../../../.ai/memory/unfinished-work.md)
tracks current state and separate qualification. This audit is not proof of
absolute absence of bugs.

Final frozen-source review, independent matrices and the replacement complete
local gate found no further reproducible actionable defect in the reviewed
local scope. Source/test bytes match the implementation commit. Only evidence
and handoff documentation changed afterward. Workflow inspection and read-only
GitHub checks found no branch PR or hosted run; pushing this existing branch
without a PR did not trigger PR/main qualification. No merge or release occurred.
