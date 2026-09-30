# Development and CI guidance correction — #120

2026-09-29, Codex. Local preparation only: no push, PR creation, hosted
dispatch/rerun, tagging, publication, image build, firmware change or real
disk operation was performed for this task.

## Source and authoritative workflow

Base: `7e8603d588502fedce9206a735f924398d59b260`, `origin/main` when this
branch was created. Working branch: `codex/dev-ci-guidance-120`. The final
commit containing this receipt identifies the reviewed change; use
`git log -1 --format=%H -- docs/evidence/development-ci-120/README.md`.
The primary checkout's pre-existing changes and the separate #119 branch
were preserved.

Authority is [AGENTS.md](../../../AGENTS.md),
[contribution policy](../../../CONTRIBUTING.md),
[current CI](../../ci.md), and the actual
[CI workflow](../../../.github/workflows/ci.yml),
[release workflow](../../../.github/workflows/release.yml) and
[release readiness check](../../../scripts/check-release-ready.sh).
Configuration, rather than old provider prose, establishes:

- PRs to main and main pushes execute Linux source/ISO/KVM and native
  Windows gates on Blacksmith. `CI gate` depends on both. PR runs use the
  merge revision; release readiness requires a successful `ci.yml` push
  run for the exact tagged main SHA.
- Linux uses `blacksmith-4vcpu-ubuntu-2404`; Windows uses
  `blacksmith-2vcpu-windows-2025`. Ordinary qualification retains evidence
  for seven days, without customer ISO/USB binaries or production credentials.
- Separately authorized manual `release.yml` rebuilds and qualifies bytes,
  transfers measured inputs for one day, then uses the protected production
  publisher with GitHub OIDC and the existing GCP signing/storage identity.
  Those GCP dependencies are active, not obsolete developer prerequisites.

Read-only inspection confirmed the base main
[run 36519281288](https://github.com/BeamoTech/beamo-wipe/actions/runs/36519281288)
completed successfully, event `push`, source exactly the base SHA above.
[Saved metadata](baseline-main-ci.json) describes that existing run; it
does **not** qualify this new branch. The dated
[2026-09-26 CI audit](../ci-audit-20260926/README.md) supplies the earlier
migration evidence and explicitly supersedes gcloud authentication guidance.

## Inventory and changes

[Reference inventory](reference-inventory.tsv) records matching line numbers
and SHA-256 for 263 text files: 23 current guidance/scoped validation notes,
40 implementation/configuration files, four retained legacy files, 35 test
files, 159 historical/release records and two optional lab files. Search
covered tracked text, including hidden configuration, JSON evidence, help
generators and tests, plus the new doctor tests. Broad publication matches
include intentionally unrelated runtime references; these were left alone.
Search terms included `gcloud`, Google Cloud/Cloud Build, `cloudbuild`,
`ci-cloud`, `cloud-test`, trigger installation, Blacksmith, hosted gate/
qualification, `release.yml` and publication/publisher variants.

- Replaced obsolete development onboarding/authentication guidance and
  documented the local → PR → main → artifacts → authorized release path.
  Supported preview/test/desktop scripts are no longer called legacy.
- Doctor now selects local, test, test-native, preview, preview-web,
  desktop or qualification prerequisites. It emits one JSON object and
  actionable exit 2 failures. Cloud tools/credentials are not probed.
  Optional Tk/console fallback and optional GitHub CLI are explicit.
  Native Windows cannot silently claim WSL prerequisites were checked.
- Python/module and Go version probes have five-second timeouts, at most
  two probes. Go disables automatic toolchain downloads and checks the
  current repository pin. Probe diagnostics are not echoed. Python uses
  the development command's module lookup, including user site packages;
  an initial isolated-mode false negative was caught by real command
  verification and corrected before handoff.
- Corrected CI execution guidance, runbook 1.12 and compatibility matrix
  1.14, VM notes, accessibility evidence scope, evidence-tier references,
  storage source attribution, key-custody prose and the signing module's
  docstring. No signing implementation or disk-safety behavior changed.
- Corrected the durable runner-size note and missing-KVM guidance.
  Removed the obsolete always-applied `.cursor/rules/iso-builds-on-cloud.mdc`
  duplicate: repository instructions already designate `AGENTS.md` as the
  sole guide. No replacement mirror was created.
- Kept `ci-cloud.sh`, `cloudbuild.yaml`, `.gcloudignore`, the cloud trigger
  installer and `make cloud-test` compatibility behavior. Added explicit
  legacy help and a `legacy-cloud-test` alias. Both shell help paths exit
  before any cloud command, even with an empty PATH. Existing fake-cloud
  regression suites still exercise the compatibility path.
- Kept actively shared `ci-hosted.sh`, image/QEMU scripts, protected GCP
  publisher and optional authorized `tools/usb_lab` workflows. Historical
  records and public release assets were not rewritten. Old matrix audit
  commands are explicitly scoped as historical, including superseded
  non-blocking lint and Cloud Build instructions.

Generated text was checked via CLI help, actual doctor JSON and fake web/
console previews. `stage_live_assets.py` stages NOTICE/LICENSE/THIRD_PARTY/
SOURCE documents, not a generated development-guide copy; wrapper staging
copies tracked source. No ISO or generated live-build tree was created.

## Local verification

Host: macOS arm64, Python 3.10. All pytest commands use fake-device fixtures;
the legacy suites substitute cloud commands. No setup/dependency installation
or cloud authentication was performed.

| Check | Result |
| --- | --- |
| Initial complete `./scripts/test-all.sh -o addopts=''` | 4,650 passed, 701 skipped, 3 failed in 305.80 s. Two require missing `gi`/ATK; one used the previously loaded runbook 1.11 assertion while the document was being updated. |
| Developer, runbook, matrix and retained cloud regression suites | 116 passed in 8.27 s. The updated runbook assertion passes. |
| Final doctor, Blacksmith CI/release, signing and runbook focused tests | 98 passed in 16.14 s. |
| Runbook-prescribed storage/copy/UI/runbook tests | 64 passed in 1.95 s. |
| Final complete local suite | **4,651 passed, 701 skipped, two failed in 330.99 s**. Both failures require absent `gi`/ATK (`test_compat_story::test_what_screen_keeps_title_and_shows_this_usb_line` and `test_separate_footer_actions::test_assist_nav_names_do_not_rewrite_result_heading`). Runbook and all 32 doctor cases pass. [Machine-readable summary and log hashes](test-results.json). |
| Ruff tooling lint/format, full source/tests lint and prescribed security selections | Pass. |
| mypy `--ignore-missing-imports src/beamo_wipe` | Pass, 50 source files. |
| compileall, ShellCheck, shell syntax, actionlint, `git diff --check` | Pass. |
| YAML/JSON configuration parsing | All three Actions workflows, retained Cloud Build configuration and Cursor environment parse. CI/release events match the documented route. |
| Relative Markdown files/anchors in changed guidance and this receipt | 60 checked, no broken targets. All 263 inventory hashes verified against the final files. External link availability was not exhaustively network-checked. |
| Help and `make -n cloud-test legacy-cloud-test` | Pass; only printed help/plans, no submission. |
| `BEAMO_WIPE_NO_OPEN=1 python3 dev.py preview --web`; console preview with EOF | Exit 0, fake devices; web output generated and console returns on EOF. |

[Actual doctor results](doctor-results.json) show all non-desktop profiles
pass on this Mac in 0.041–0.129 s. Desktop correctly exits 2 because the
installed Go does not match the pinned 1.26.8; no replacement was downloaded.
Deterministic tests cover present/missing/legacy-only tools, Python failure,
timeout, malformed output, version mismatch, live-system refusal, Windows
boundaries and optional dependencies without relying on host installation.

Command families actually executed: `python3 -m pytest`,
`./scripts/test-all.sh`, `python3 -m ruff check`, `ruff format --check`,
`python3 -m mypy`, `python3 -m compileall`, `shellcheck`, `bash -n`,
`actionlint`, local YAML/JSON/link parsers, `dev.py --help`, operation-specific
doctor/help, fake previews, shell legacy `--help`, and `make -n`.
Raw local run logs/JUnit are disposable under `/private/tmp/beamo-wipe-120`;
this receipt and the saved metadata retain the meaningful results.

## Limits and next action

No claim of hosted qualification for these edits. Native Linux GTK/Orca,
native Windows/WSL, ISO/KVM, physical hardware, release signing/storage and
external permission checks were not executed here. Desktop builds were not
run with the wrong local Go version. VM examples were syntax/review checked,
not executed; image build scripts were inspected, never invoked as `--help`.
No operational workflow contradiction remains in the corrected onboarding
path; dated historical receipts intentionally retain their original provider.
The separate #119 Secure Boot correction remains separate work.

Review this local commit, then obtain explicit permission before any push,
PR creation/update or hosted qualification. Such a run must test this source;
the successful baseline run cannot be reused. Publication requires its own
authorization and unchanged release safeguards.
