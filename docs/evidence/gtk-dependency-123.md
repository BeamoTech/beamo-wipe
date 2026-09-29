# GTK dependency boundary — #123

2026-09-29, Codex. Local test/configuration correction; no application,
disk-discovery, erase, signing or release behavior changed. No hosted workflow
was triggered and no remote source or setting was changed.

## Source and reproduced failure

Base: `607655b1322edeb4af50074dc886fd9823c15b47` (the preserved local #122
commit, itself based on main `7e8603d588502fedce9206a735f924398d59b260`).
Branch: `codex/gtk-dependency-123`. The commit containing this receipt records
the exact correction (`git log -1 --format=%H -- docs/evidence/gtk-dependency-123.md`).
Other task branches and the primary checkout's unrelated edits remain intact.

Observed platform: macOS 26.6.2 arm64, Python 3.10.0, no `gi`, no DISPLAY.
Before editing, collection of the two modules **succeeded: 25 collected**.
The task's suspected collection error was actually a runtime import failure
in two test functions, before their later import of `test_accessible_runtime`
could apply its dependency handling:

```text
tests/test_compat_story.py:310
    import gi
ModuleNotFoundError: No module named 'gi'

tests/test_separate_footer_actions.py:98
    from gi.repository import Atk
ModuleNotFoundError: No module named 'gi'

2 failed in 0.22s
```

Exact tests:

- `test_compat_story.py::test_what_screen_keeps_title_and_shows_this_usb_line`
- `test_separate_footer_actions.py::test_assist_nav_names_do_not_rewrite_result_heading`

## Existing policy and correction

`tests/test_accessible_runtime.py` already uses `pytest.importorskip("gi")`
before importing the GTK implementation. Mixed-module examples include
`test_compare_disks.py`, `test_operation_identity.py` and
`test_accessible_boot_option.py`; the last supplies the reused reason:
`GTK bindings are validated on the hosted Linux image`.

Both affected functions now apply that pattern **inside the test**, before
any GTK import. They first inspect `find_spec("gi")`, so an installed binding
is imported normally: native dependency/ABI errors and syntax errors cannot
be hidden by `importorskip`'s broader ImportError handling. No module-wide
skip, environment policy or new skip helper was introduced. Existing non-GTK
tests remain collectable and executable. The footer test also explicitly
requires GTK 3.0 and ATK 1.0 before namespace import, removing reliance on
another test having selected their versions first. Initialization and test
assertions remain outside any skip/error-catching boundary.

`scripts/ci-hosted.sh` already declares `python3-gi` and `gir1.2-gtk-3.0`
(which brings ATK) and runs the full fake-device suite under Xvfb at 72 DPI,
with Orca isolated on another D-Bus/X session. It now preflights both namespace
versions and runs `scripts/check-gtk-test-results.py` on the suite's actual
JUnit report after waiting for both child processes. Each of the two tests
must occur once and pass; skipped, failed, errored, missing or duplicate cases
fail the gate. Absent/malformed reports also fail by exception. Existing child
failures remain failures; the guard does not overwrite their exit status.

Static workflow tracing: `ci.yml` (PR/main/manual) and `release.yml` both call
`ci-blacksmith.sh sources`, whose `tests` phase invokes this shared hosted
gate. No check context, runner, package pin, job dependency or bypass changed.
[Current CI policy](../ci.md#execution) now documents local optional bindings
versus mandatory qualification. This trace is configuration evidence, not a
claim that Linux executed the changed source.

## Verification

All test devices were fakes; no `nwipe` or image build was invoked.

```sh
BEAMO_WIPE_DRY_RUN=1 python3 -m pytest -p no:cacheprovider -o addopts='' \
  --collect-only -q tests/test_compat_story.py tests/test_separate_footer_actions.py

BEAMO_WIPE_DRY_RUN=1 python3 -m pytest -p no:cacheprovider -o addopts='' -q -rs \
  tests/test_gtk_dependency_handling.py tests/test_compat_story.py \
  tests/test_separate_footer_actions.py tests/test_ci_hosted.py \
  tests/test_blacksmith_release.py tests/test_blacksmith_ci.py

BEAMO_WIPE_DRY_RUN=1 PYTEST_ADDOPTS='-p no:cacheprovider' \
  ./scripts/test-all.sh -o addopts='' --junitxml=/private/tmp/beamo-wipe-123-full-final.xml
```

- Post-change collection: **25 collected**, no errors, same inventory as before.
- Two affected tests plus one non-GTK control: **1 passed, 2 skipped, 0.18 s**.
  Exactly those two report the expected GTK reason. Feeding this real report
  to the hosted guard exits 1 with `Mandatory GTK test must execute and pass
  exactly once`; local skips cannot pass hosted qualification.
  The exact hosted namespace preflight also exits nonzero on this Mac with
  `ModuleNotFoundError: No module named 'gi'`, before starting pytest.
- Final expanded focused run: **92 passed, 6 skipped, 29.33 s**. Two GTK skips and
  four existing Tk geometry skips (`no DISPLAY on macOS — Tk would abort`).
- Fifteen new regression cases cover missing bindings in both test orders,
  missing native subdependency, import/ABI error, syntax error, wrong namespace
  version, initialization failure, deliberate bad-UI assertion failures,
  six hosted-result outcomes, and static CI/release wiring. Each isolated
  dependency simulation executes a non-GTK control successfully. Subprocesses
  have a 30-second timeout and do not mutate the parent import state.
- Replaying the original functions from the base commit in memory under the
  same controlled missing-dependency setup produces **2 failed, 1 passed**.
  No tracked source was temporarily replaced to obtain that negative result.
- The first full run caught four hosted-runner simulation failures:
  **4,641 passed, 703 skipped, 4 failed, 411.17 s**. The fixture invoked the
  actual shell function but supplied neither GTK nor named JUnit cases. It
  now supplies isolated fake bindings and the required result records, keeping
  all existing overlap, private-session, wait/cleanup and child-failure
  assertions. Two additional cases prove that skipped/missing GTK results
  fail the actual shell gate even when both simulated processes exit zero.
  All six scenarios pass in the final focused run. These are fixture tests,
  not Linux/GTK execution evidence.
- Final full repository suite: **4,647 passed, 703 skipped, zero failures or
  errors, 389.80 s**. Both affected cases report the intended GTK dependency
  reason. The two additional GTK skips account for the change from the
  preceding task's 701 skips; no unrelated test was newly skipped.
- Prescribed compileall, Ruff (including security selections), developer-tool
  formatting, mypy (50 source files), ShellCheck and actionlint passed.
  Updated CI guidance rendered locally with markdown-it. Final diff checked.

Detailed logs/JUnit are disposable files under `/private/tmp/beamo-wipe-123-*`;
the adjacent [result receipt](gtk-dependency-123-results.json) retains hashes,
counts and exact skip reasons.

## Coverage limits and next step

Real Linux GTK/ATK and rendered accessibility execution: **NOT TESTED** for
this source. This Mac has no GTK runtime; controlled Python substitutes prove
dependency/error routing, not real rendering or assistive-technology behavior.
The actual existing GTK assertions and cleanup still execute normally when
the bindings are installed. The deliberate-assertion simulations execute those
assertions with incorrect substitutes and correctly fail.

Review the local commit and run authorized exact-source Blacksmith Linux
qualification before considering the Linux acceptance criteria verified.
No push, PR, hosted run, merge or release was performed as part of this task.
