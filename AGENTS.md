# Beamo Wipe — AI agent guide

`AGENTS.md` is the sole guide for all agents.

Prior context: `.ai/memory/MEMORY.md`; read only relevant notes.

## CI, cost and documentation

Read `~/dev/AGENTS.md` for shared checkout, cost, documentation and storage rules.

- Iterate locally; run the applicable full local gate before release. Hosted
  CI is only for necessary final public/customer production verification,
  never routine work, draft PRs, previews or unshipped instruction/doc maintenance. Local
  scripts named `ci` remain local; do not push merely to trigger CI.
- Run the fewest required hosted jobs. Reuse only evidence for the exact final
  SHA, artifacts and config; revalidate after changes. Fix every candidate/gate
  failure and material warning, then rerun until all applicable checks pass.
  Pending, canceled, blocked, timed out and unexpected skips are not passes;
  path skips require workflow evidence. Never weaken tests/coverage or retry blindly.
- Check automatic triggers and gate publication on successful verification.
  Preserve required statuses, branch protection, scheduled security/ops checks,
  native acceptance and approvals; record proof and verify after deployment.
  No hosted CI means retain local/manual gates. Changes to automation or
  publication need task authority. Avoid duplicate providers/runs.

**Project gate:** This older checkout retains its own Cloud Build gate. Use local pytest and
preview during development; reserve its ISO/native/QEMU qualification for a
final public release candidate. Inspect this checkout's triggers and receipts
rather than assuming parity with Beamo Wipe. A local Mac pass or a Cloud build
without the required QEMU evidence cannot qualify a public ISO.

## Project

Guided **nwipe** front-end plus a Debian live ISO. Beamo Wipe does not implement a wipe engine. It discovers disks, refuses to target the boot USB, walks a non-technical owner through confirms, then execs pinned **nwipe v0.42**.

Repo: `https://github.com/BeamoINT/beamo-wipe` (slug `beamo-wipe`). Branding may say Beamo Wipe; do not rename nwipe.

## Shared-checkout discipline

Other agents may be working here. Stage explicit paths only. Never `git add -A`. Never commit `*.iso`, USB images, or secrets.

## Canonical commands

```bash
python3 -m pytest
./scripts/test-all.sh
./scripts/ci-cloud.sh    # Google Cloud Build: pytest + amd64 ISO (project beamo-wipe)
./preview                # Tk window, fake disks, nothing erased
./preview --web          # browser click-through
./scripts/build-iso.sh   # amd64 live image (prefer Cloud Build, not this Mac)
```

Local pytest is the fast gate. This checkout has Cloud Build in `beamo-wipe`, no Actions. `cloudbuild.yaml` → `scripts/ci-hosted.sh` runs `lint`/`tests`/`preview`/`negative`/`iso`/`qemu`, secret-free (`docs/ci.md`). Intended PR trigger `beamo-wipe-pr-gate` skips QEMU; `main` trigger `beamo-wipe-main-gate` runs all phases. Until migration is verified, necessary final ISO/x86 qualification uses `./scripts/ci-cloud.sh` or `gcloud builds submit --project=beamo-wipe`. Preserve native/ISO/QEMU coverage; Hostinger and this Mac are not the ISO gate.

Cloud Build produces amd64 ISOs. On Apple silicon, Docker `linux/amd64`/`qemu-system-x86_64` use TCG; avoid waiting on emulation. Interactive `docs/vm-test.md` QEMU needs a disposable x86_64/KVM VM via `gcloud`/`aws`; tear it down. See `.ai/memory/iso-builds-on-cloud.md`.

## Cloud agent environment

Cloud VMs: x86_64 Ubuntu. `.cursor/environment.json` runs `.cursor/install.sh`, then `.cursor/start.sh` (dockerd, Xvfb `:99`, 72 DPI). Fast smoke: `.cursor/check.sh`.

Tk layout checks need 72 DPI. VNC `DISPLAY=:1` is 96 DPI and clips; keep that computer-use display unchanged. Run:

```bash
dbus-run-session -- xvfb-run -a -s "-screen 0 1600x1000x24 -dpi 72" python3 -m pytest
```

`.cursor/start.sh` launches Xvfb on `:99` at 72 DPI, so `DISPLAY=:99 dbus-run-session -- python3 -m pytest` works. Do not replace `:1` (computer-use / VNC).

`packaging/live/config/{bootstrap,binary}` are gitignored live-build outputs. Two tests in `tests/test_live_image.py` fail until `lb config` has been run inside `./scripts/build-iso.sh`. That is expected on a fresh checkout.

Nested Docker requires `fuse-overlayfs` in `/etc/docker/daemon.json`; `/dev/kvm` is present. `./scripts/build-iso.sh` and QEMU run natively. Use `sudo docker` unless already in the `docker` group. `gcloud`/`aws` are installed but need existing secrets for login; tear down disposable VMs.

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
