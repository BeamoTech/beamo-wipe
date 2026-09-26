# Beamo Wipe — AI agent guide

> This file is mirrored to `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `GROK.md`, and `.github/copilot-instructions.md`. Edit one copy, then run `~/dev/sync-ai-memory.sh --repo .` to re-sync the rest.

Durable notes live in `.ai/memory/` — start at `.ai/memory/MEMORY.md`.

## CI, cost and documentation

- Use **Blacksmith** runners for supported GitHub Actions CI. Check the current
  [runner documentation](https://docs.blacksmith.sh/blacksmith-runners/overview)
  and repository access before selecting labels. Preserve required checks and
  native platform coverage; retain an existing gate until its replacement proves
  equivalent coverage for the same source. Record any provider exception.
- Minimize total cost across CI, hosting, storage, network, APIs, AI and tooling.
  Choose the least costly option that meets the task's quality, security,
  reliability and performance requirements. Preserve mandated models and gates;
  never trade away correctness, coverage, accessibility or data safety for price.
- Measure usage, reuse valid caches, bound retries/concurrency, cancel superseded
  verification runs and expire disposable artifacts. Never cancel a release or
  data migration blindly. Use local fixtures for iteration, run required gates
  before delivery, and retire only verified idle resources within task authority.
- Keep Markdown focused: one canonical home per topic, short sections and useful
  links. Keep commands and safeguards near their use; move detailed history to
  dated evidence. Update stale guidance against code, preserve release records,
  and avoid duplicating this policy in every document.

## Project

Guided **nwipe** front-end plus a Debian live ISO. Beamo Wipe does not implement a wipe engine. It discovers disks, refuses to target the boot USB, walks a non-technical owner through confirms, then execs pinned **nwipe v0.42**.

Repo: `https://github.com/BeamoTech/beamo-wipe` (old BeamoINT URL redirects) (slug `beamo-wipe`). Branding may say Beamo Wipe; do not rename nwipe.

## Shared-checkout discipline

Other agents may be working here. Stage explicit paths only. Never `git add -A`. Never commit `*.iso`, USB images, or secrets.

## Canonical commands

```bash
python3 -m pytest
./scripts/test-all.sh
gh workflow run ci.yml --repo BeamoTech/beamo-wipe  # Blacksmith hosted gate
./preview                # Tk window, fake disks, nothing erased
./preview --web          # browser click-through
./scripts/build-iso.sh   # amd64 live image (Blacksmith, not this Mac)
```

Local pytest is the fast checkout gate. **CI runs on Blacksmith through GitHub Actions**, per the operator's 2026-09-26 correction. `.github/workflows/ci.yml` runs the secret-free `CI gate` on `blacksmith-8vcpu-ubuntu-2404`: parallel lint/types, Python tests, preview, desktop launchers, and negative checks; then the amd64 ISO and full QEMU validation, plus independent native Windows launcher tests. PRs to `main` and pushes to `main` run every phase. `codex/ci-*` pushes are verification branches. See `docs/ci.md` for bootstrap status and evidence. Never claim a configured workflow has passed before observing its hosted run.

**ISO build and QEMU wipe tests:** use Blacksmith's disposable x86_64 workers with KVM. Do not wait on this Apple silicon Mac's amd64 Docker/QEMU emulation. Never pass host disks to QEMU. `cloudbuild.yaml`, `ci-cloud.sh`, and the Cloud trigger installer are legacy tooling, not the current CI route. Do not invoke Google Cloud or request gcloud authentication for current CI. Publication requires separate explicit operator authorization; the Blacksmith workflow has no production credentials or publishing step. See `.ai/memory/iso-builds-on-cloud.md`.

## Cursor Cloud specific instructions

Cursor Cloud Agent VMs for this repo are **x86_64 Ubuntu**, not the Apple silicon Mac. Committed boot is `.cursor/environment.json` → `.cursor/install.sh` then `.cursor/start.sh` (dockerd + Xvfb `:99` at 72 DPI). `.cursor/check.sh` is the fast smoke.

Python gate on Cloud Agents: Tk layout tests scale with X DPI. The VNC desktop is `DISPLAY=:1` at 96 DPI and fails clipping tests. Use 72 DPI:

```bash
dbus-run-session -- xvfb-run -a -s "-screen 0 1600x1000x24 -dpi 72" python3 -m pytest
```

`.cursor/start.sh` launches Xvfb on `:99` at 72 DPI, so `DISPLAY=:99 dbus-run-session -- python3 -m pytest` works. Do not replace `:1` (computer-use / VNC).

`packaging/live/config/{bootstrap,binary}` are gitignored live-build outputs. Two tests in `tests/test_live_image.py` fail until `lb config` has been run inside `./scripts/build-iso.sh`. That is expected on a fresh checkout.

ISO on Cloud Agents: Docker Engine is nested, so `/etc/docker/daemon.json` must use `fuse-overlayfs` (plain overlay fails). `/dev/kvm` is present. `./scripts/build-iso.sh` and KVM QEMU are native here. Prefer `sudo docker` unless this user is already in the `docker` group. `gcloud` and `aws` are installed for throwaway VMs you will tear down; they are not logged in unless secrets exist.

## Safety boundaries

- Erasure = the `nwipe` binary only. No ATA/NVMe sanitize engine, no custom overwrite loop.
- No password reset, SAM edits, BitLocker extraction, Secure Boot circumvention, or in-OS wipe of the running Windows disk.
- Boot USB must never be selectable. If it cannot be identified, list no disks.
- Confirm token + 5s delay + owner checkbox. No auto-start wipe on boot.
- Logs under `/tmp/beamo-wipe/`, never the target disk.
- `--autonuke` is allowed only with exactly one positional `/dev/…` target and `--exclude=` the boot device. Never `--force`.
- No Apple Silicon / Chromebook / “certified DoD” / “plug and play” claims. See `docs/claims.md`.

Any change to disk selection or nwipe flags is a `safety:` commit and needs a test.

## Layout

- `src/beamo_wipe/` — wizard, discover, safety, nwipe_runner
- `./preview` — local Tk / `--web` gallery (not shipped as a wipe tool)
- `helper/index.html` — boot-menu helper (does not wipe)
- `packaging/live/` — live-build config, Dockerized by `scripts/build-iso.sh`
- `docs/claims.md` — Amazon copy
- `docs/ADVANCED.md` — pinned nwipe flags
