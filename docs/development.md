# Developing Beamo Wipe

Use a normal development computer and fake devices. The same source checkout
supports development from Windows, macOS and Linux; the Linux live USB remains
the only supported erasure runtime. Doctor, preview and local test commands use
fake devices and do not erase disks, change firmware or restart the computer.
OS dependency installation may require administrator access. Hosted verification,
VM work and release publication have separate boundaries below.

## Choose your environment

| Host | Python wizard and full checkout tests | Desktop launcher | ISO and complete acceptance |
| --- | --- | --- | --- |
| Linux x86_64 | Native; Tk or browser preview; Xvfb for headless tests | Native tests; Windows/Linux cross-builds | Blacksmith through GitHub Actions; optional interactive QEMU on an authorized disposable x86_64 KVM worker |
| Linux ARM64 | Native Python development; platform-dependent tests may skip | Native Go tests; Windows/Linux amd64 cross-builds | Remote x86_64 Linux; local ARM emulation is not acceptance |
| macOS Intel or Apple Silicon | Native Python; modern Tk or browser preview | Native Go logic/UI tests; Windows/Linux cross-builds | Remote x86_64 Linux |
| Windows | WSL2 Ubuntu for the Python wizard and full suite; browser preview works without WSLg | Native Go tests and builds; native Python developer-tool tests | Remote x86_64 Linux |
| Other machines | Use a remote Linux development host over SSH | Unqualified locally | Remote x86_64 Linux |

The matrix describes intended development workflows, not certification of every
OS version or CPU. See the [initial workflow verification](evidence/development-ci-120/README.md)
and [Windows follow-up](evidence/development-ci-120/windows-20261001.md) for environments
actually tested. Native Windows Python cannot run the POSIX wizard: file locking, secure
file descriptors, terminal input and Linux device paths are intentional runtime
requirements. `dev.py` routes Python commands through WSL2 rather than weakening
those controls. Native Windows `test --native` tests developer tools only.
GTK/Orca accessibility, Linux mounts, process handling, live boot and firmware
behavior require Linux acceptance. Go tests on macOS do not exercise Windows
firmware APIs. Cross-compilation alone does not prove runtime behavior.

## First setup

Install Git and Python 3.10 or newer with venv/pip support. Use a current Python
with maintained security updates. Windows users can use `py -3` wherever these
examples say `python3`. Go **1.26.8** is needed only for desktop work; build
commands reject a different version and do not download a replacement silently.

Clone the canonical repository into a development directory:

```text
git clone https://github.com/BeamoTech/beamo-wipe.git
cd beamo-wipe
```

The old `BeamoINT/beamo-wipe` GitHub URL redirects here. Other remotes are not
qualification evidence: verify the same source revision before comparing
results on different machines; record `git rev-parse HEAD`.
Do not copy virtual environments or executable caches between operating systems.

On Debian/Ubuntu, install Python and optional graphical test dependencies:

```bash
sudo apt-get update
sudo apt-get install python3 python3-venv python3-tk git xvfb x11-utils xauth dbus-x11
python3 dev.py setup
python3 dev.py doctor
```

On macOS, install Python with a working Tk. The canonical preview selects a
Tk version at least 8.6.13; older Aqua Tk bundles can crash when closing a
window. If none is available, it falls back to the console. Web mode does not
probe or need Tk. Install a modern Python/Tk before using the graphical tests.

```bash
python3 dev.py setup
python3 dev.py doctor
```

`setup` installs project development dependencies and the CI Ruff/mypy versions
inside `.venv-linux` or `.venv-darwin`. It never installs packages into system
Python. It is safe to rerun after a failed download. Activation is unnecessary:
`dev.py test` selects the host's environment automatically. On macOS the Tk
preview retains the existing modern-Tk interpreter selection.

On Windows, install WSL2 and Ubuntu following Microsoft's WSL setup, then open
Ubuntu and run the Debian/Ubuntu setup above. Prefer cloning inside Ubuntu's
home directory for filesystem performance and normal POSIX permissions.
WSLg provides Tk windows when available. A headless WSL installation can use
`preview --web`, then open the generated HTML in Windows through Explorer's
Linux filesystem view. `BEAMO_WIPE_NO_OPEN=1` prints the path without attempting
to open a browser.

From a Windows checkout in PowerShell, the following delegate to the default
WSL distribution using `wslpath`; paths with spaces remain one argument:

```powershell
py -3 dev.py setup
py -3 dev.py preview --web
py -3 dev.py test
```

Install `python3` and `python3-venv` in that distribution first. Missing WSL,
an uninitialized distribution, or an unconvertible checkout path produces a
nonzero error with instructions. No Windows Python wizard fallback is implied.
For native Windows developer tools and Go work:

```powershell
py -3 dev.py setup --native
py -3 dev.py test --native
py -3 dev.py desktop-test
py -3 dev.py desktop-build
```

The native environment is `.venv-win32`; `setup --native` installs only the
portable tooling test dependency. It does not install the POSIX application.

## Everyday commands

```bash
python3 dev.py preview                 # fake Tk wizard (or console fallback)
python3 dev.py preview --web           # browser click-through, no wipe engine
python3 dev.py preview --console       # keyboard console on POSIX
python3 dev.py preview --scenario empty
python3 dev.py preview --scenario blocked
python3 dev.py preview --scenario fail
python3 dev.py test                    # full existing checkout suite
python3 dev.py test --native           # portable developer-tool tests only
python3 dev.py desktop-test            # native Go unit tests and vet
python3 dev.py desktop-build           # Windows/Linux amd64 executables
```

The supported `./preview`, `./scripts/test-all.sh`, and
`./scripts/build-desktop.sh` entry points remain available. The shell desktop build
and `dev.py` use the same Python implementation, Go pin, flags, executable names,
and manifest schema. `BEAMO_GO_BIN` may select an explicit Go executable.
The generated `dist/desktop/desktop-build.json` identifies source and hashes;
the executables retain the existing embedded dirty-source indicator. A failed
build must not be presented as a successful latest build. Concurrent builds to
the same output are refused. Normal errors and keyboard cancellation release
`dist/desktop/.build.lock`; a force-killed process can leave it behind. Confirm
that no build is still running before manually removing that stale lock and
retrying. Never remove the lock to bypass an active build.

`doctor` is a local, operation-specific preflight. It never authenticates,
installs tools, checks remote permissions, enumerates disks, builds images or
dispatches CI. Output is one JSON object with `operation`, `status`, `problems`,
and `notes`; exit 0 means the selected local prerequisites passed, and exit 2
means an actionable prerequisite is missing, failed, timed out or unverified.
It runs at most two local probes, each bounded to five seconds, and does not
print subprocess diagnostics or credentials.

| Command | Scope |
| --- | --- |
| `python3 dev.py doctor` | Git, selected Python >=3.10, venv/pip; no Go, Tk or cloud prerequisite |
| `python3 dev.py doctor --for test` | Git, selected Python and pytest; full Linux/display coverage still requires actual tests |
| `python3 dev.py doctor --for test-native` | Portable developer-tool test prerequisites, including on native Windows |
| `python3 dev.py doctor --for preview` | Python plus optional Tk module discovery; no window/display claim; console fallback remains available |
| `python3 dev.py doctor --for preview-web` | Python, without a Tk prerequisite |
| `python3 dev.py doctor --for desktop` | Git/Python and the exact Go pin from `desktop/go.mod`, with toolchain downloads disabled |
| `python3 dev.py doctor --for qualification` | Git and optional `gh` discovery plus the Blacksmith route; the selected Python environment and credentials are not probed |

Native Windows doctor cannot verify Linux dependencies for `test`, `preview`
or `preview-web`: run that operation inside the WSL2 Ubuntu checkout. It returns
2 with this instruction even if `wsl.exe` is installed. Use `test-native` for
portable Windows tooling. A missing selected Python or a live erasure environment
also returns 2. Tk module discovery is not proof of compatible Tk or a working
display; the preview launcher makes the actual interpreter/display choice.
Preview/test commands enforce fake mode and remove inherited
boot-device and native-inventory test overrides. They refuse a live system
instead of clearing its live identity.

Linux `test` uses a separate Xvfb display at 72 DPI when Xvfb and D-Bus are
installed. It does not replace an existing desktop. A local passing suite may
still contain explicit environment-dependent skips; inspect the summary. Full
GTK/speech and packaged-image checks require the dependencies in
`scripts/ci-hosted.sh` and the hosted gate. Do not enable native inventory tests
on a personal development computer. Use only controlled fixtures.

For launcher browser development, run `go run . --preview` inside `desktop/`.
That uses fake readiness and cannot reboot. Test UI behavior in the host browser;
Windows/Linux runtime and firmware tests remain separate. The offline helper is
`helper/index.html`; it provides boot guidance and never erases disks.

## Qualification, artifacts and release handoff

The approved pipeline is [Blacksmith through GitHub Actions](ci.md), configured
in [ci.yml](../.github/workflows/ci.yml). No Google Cloud CLI or cloud credentials
are needed for local development or ordinary qualification.

1. Make source changes on a local branch. Run `python3 dev.py test` (or
   `./scripts/test-all.sh`), review failures/skips and record the source SHA.
   Use fake previews for UI work. `test --native` is a smaller tooling suite.
2. When remote work is authorized, open a PR targeting `main`. Every PR update
   triggers the full Linux source/ISO/KVM gate and native Windows tests.
   Pushing a branch without a PR does not trigger `ci.yml`; opening/updating
   its PR does. A push to `main` runs the full gate again. Do not push or open
   a PR during a local-only task.
3. Require the exact PR's `CI gate` and maintainer authorization before merging.
   A separate non-author approval is not required under the
   [sole-maintainer policy](ci.md#required-checks-and-rollout).
   PR CI checks GitHub's merge revision; record its base/head parents.
   Main qualification is the separate successful `push` run for the exact main
   commit, not a reused PR result. Manual dispatch is available for authorized
   verification branches; see [CI execution](ci.md#execution).
4. Retain the run URL, tested SHA, build ID, receipts and artifact digests.
   Ordinary CI retains evidence/sidecars for seven days, **not ISO/USB binaries**.
   Retaining binaries for another machine needs an authorized destination and
   measured hashes; local output is not a published release.
5. Separately authorized publication uses [release.yml](../.github/workflows/release.yml)
   on `main` with a version tag at that exact, successfully qualified main
   commit. It rebuilds and verifies the actual customer bytes on Blacksmith,
   transfers them for one day to the protected `production` publisher, checks
   all hashes, then obtains short-lived GitHub OIDC credentials for GCP signing
   and storage. GCP is still required for that publisher; it is not CI compute
   and does not require a maintainer's interactive cloud login. Follow
   [release verification](release-verification.md), including immutable uploads,
   signatures, completion marker and GitHub asset checks before public promotion.

A configured workflow or a passing doctor is not an executed qualification.
No local command substitutes for the full hosted gate. Do not run amd64
Docker/QEMU acceptance on Apple Silicon or attach host disks to test VMs.
Optional manual VM work belongs on an authorized disposable x86_64 worker;
see [VM notes](vm-test.md). It does not publish or replace the required gate.

### Retained legacy and shared tools

| Entry point | Current purpose and support boundary |
| --- | --- |
| `scripts/ci-cloud.sh`, `cloudbuild.yaml`, `make cloud-test` / `make legacy-cloud-test` | Retained Cloud Build compatibility path, covered by local fake-command tests. It can submit remote builds (and explicitly request publication); it is not the approved qualification/publication route. Use only for separately authorized legacy maintenance, never to satisfy `CI gate`. |
| `scripts/install-cloud-triggers.sh` | Retained legacy trigger reconciliation. It changes remote settings; do not run for normal onboarding or to recreate superseded triggers. `--help` is local only. |
| `scripts/ci-hosted.sh`, `scripts/build-iso.sh`, `scripts/qemu-verify.sh` | Shared, actively required implementation used by Blacksmith; these are not obsolete. Privileged image/QEMU work requires isolated disposable Linux workers. |
| `scripts/publish_release_gcs.py`, `scripts/publish-release-blacksmith.sh` | Active signed-release publisher and its Blacksmith entry point. Existing GCP signing/storage remains required only inside the separately authorized protected publisher. |
| `./preview`, `scripts/test-all.sh`, `scripts/build-desktop.sh` | Supported local entry points; keep their existing compatibility behavior. |

Historical release notes and dated evidence retain their original provider
names and commands. They describe those runs, not today's onboarding route.

## Troubleshooting and recovery

- Missing Python/venv/pip: install the OS prerequisite, rerun `setup`; do not use
  system-wide pip or copy another host's environment.
- Missing display/Tk: use `preview --web` or `--console`; install Tk/WSLg for GUI
  work. Use isolated Xvfb at 72 DPI for Linux layout tests.
- Test failure: keep the output and exact SHA; reproduce the failing case before
  editing. A skip is not a pass. Native tooling tests are not the full suite.
- Wrong Go version: install the pinned version or point `BEAMO_GO_BIN` at it.
  Do not change the project's Go pin merely to match your machine.
- Local prerequisite failure: select the relevant doctor operation and repair
  that tool. Do not install/authenticate a cloud CLI for local tests or previews.
- GitHub access or queued Blacksmith job: check repository/App access using the
  approved account and [CI triage](ci.md#failure-triage). Doctor does not test
  that access. Do not silently switch providers or broaden cloud IAM.
- Protected release authentication failure: preserve verification evidence and
  investigate its dedicated OIDC publisher binding under separate release
  authorization; an interactive developer cloud login is not a substitute.
- Interrupted preview/test/build: inspect the process and result before retrying.
  No preview state is evidence of erasure. Preserve unrelated working-tree edits.

## Desktop readiness checks

The desktop launcher reports three separate checks: original USB detection,
startup-settings readability, and a supported restart route. Partial results
retain successful evidence; checks that were not reached remain unverified.
A read failure may mean permission is needed, but does not prove that permission
was denied. The technical disclosure includes the available USB identity,
partition identities, Secure Boot read result and matched startup entry.
These checks never select a disk to erase or guarantee a successful boot.

The existing `ready`, `title`, `detail`, `preview` and `version` JSON fields are
preserved. `checks` and `technical` add explanations to `/api/check`, completed
`/api/state` results and `--check-json`. Restart authorization still uses the
original plan, explicit confirmation and a fresh elevated probe. A browser
retry or failed request clears stale displayed evidence and confirmation.

The offline helper describes these checks but cannot perform them. Build staging
copies `helper/index.html` into START-HERE.html; Go embeds `desktop/web/*` into
both launchers. Tk, console fallback and `./preview --web` run the wipe wizard
after USB startup (or simulate that wizard), so they do not show pre-restart
firmware checks. Their disk exclusion and erase confirmations are unchanged.
The desktop `--preview` uses simulated checks without reading devices.

For browser regressions, install Python `playwright` alongside the development
dependencies and install Chrome or Chromium. Run
`python3 -m pytest tests/test_launcher_readiness.py`; it renders shipped assets
against fake Go snapshots and intercepts all launcher requests. Missing browser
tooling is an explicit skip, not rendered acceptance. The tests inspect the
accessibility tree and keyboard behavior; actual screen-reader speech,
physical Windows manual boot, and Linux guided restart acceptance remain
separate environment checks.
