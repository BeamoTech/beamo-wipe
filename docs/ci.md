# Continuous integration gates

**Blacksmith through GitHub Actions is the current CI platform.** This follows
the operator's 2026-09-26 correction and supersedes the Google Cloud guidance.
The workflow is `.github/workflows/ci.yml`; the stable check name is `CI gate`.
See [the migration audit](evidence/ci-audit-20260926/README.md) for measured
rollout status. A configured workflow is not proof of a successful hosted run.

## Execution

PRs targeting `main`, pushes to `main`, and verification branches matching
`codex/ci-*` run every gate. Manual dispatch is verification only:

```bash
python3 -m pytest
./scripts/test-all.sh
# After the workflow has been installed on GitHub:
gh workflow run ci.yml --repo BeamoTech/beamo-wipe --ref main
gh run list --repo BeamoTech/beamo-wipe --workflow ci.yml
```

The Linux image runner is `blacksmith-8vcpu-ubuntu-2404`. Native Windows
launcher tests run independently on `blacksmith-2vcpu-windows-2025`; both jobs
must succeed for the aggregate `CI gate` check to pass. Each source gate runs in its own
container using the content-addressed Debian bookworm image already pinned
by the ISO builder. The shared checkout has the same absolute path inside
and outside Docker so sibling ISO bind mounts resolve correctly. No developer
credentials, signing keys, environment secrets, or GitHub token are passed to
these containers. Checkout does not retain Git credentials.

| Phase | Validation |
| --- | --- |
| Workflow | actionlint 1.7.7, including shell validation |
| lint | Python compile, blocking Ruff including security rules, existing developer-tool formatting gate, ShellCheck and blocking mypy |
| tests | Full fake-device pytest at Xvfb 72 DPI; Orca in a separate clean D-Bus/X session; both JUnit reports counted in the receipt; Node, Playwright/Chromium, QR decoder and pinned Go installed so their tests execute |
| preview | Web, console, helper and embedded JavaScript syntax |
| desktop-launchers | Pinned Go 1.26.8, Linux race/vet/fuzz, Windows compilation, tested launcher bundle |
| Windows | Native Go tests/vet including Win32 and PowerShell fixtures, on pinned Go 1.26.8 |
| negative | Private safety mutation must produce the expected failing fake-device test, followed by a passing unmodified-source test |
| iso | Tested launchers, pinned nwipe v0.42, build provenance, ISO size/PVD/checksums |
| qemu | ISO and USB image inspection, installed-package inventory, fixed-vulnerability scan, isolated shipped-nwipe tests, BIOS/UEFI/Secure Boot checks, manifest finalization |

The five source phases run concurrently; every process is waited for and any
failure stops image building. ISO waits for all source gates. QEMU follows ISO
on the same disposable worker. There are no ISO/QEMU skip inputs in the
workflow. PRs receive full QEMU coverage, including image vulnerability checks.
KVM is required; Mac emulation cannot substitute for this gate. QEMU receives
only newly created regular-file images. No host `/dev` tree is bound into a
container, and the QEMU script rejects `/dev/` guest-drive arguments.

The image build uses privileged Docker as before. The QEMU container needs
privileges for private file-backed loop mounts; its loop identity checks must
remain intact. Run this only on isolated disposable workers.

## Caches, concurrency and evidence

Only pip download caches are persisted; the key binds the Debian architecture,
CI dependency-install script, and project manifest. Only a successful push to
`main` saves a cache. PRs may restore it but cannot update the trusted key.
Compiled launchers, manifests, test results and images are never cached.

New PR runs cancel older runs for that PR. Main runs are not cancelled by
concurrency policy. Linux image work is bounded at 120 minutes, Windows at 20, and aggregation at five. Action references use
immutable commit hashes. No path filters can leave an unchanged required
check missing. `pull_request_target` is not used.

Build IDs are UUIDv5 values derived from repository/run ID/attempt. All phases
share that ID and source commit; receipts also record `runner=blacksmith`,
GitHub run ID, attempt and repository. Artifact names contain source SHA, run
ID and attempt. Logs, receipts, JUnit and checksum/manifest sidecars are kept
for seven days even on failure. The private QEMU temporary-path receipt is
excluded. ISO/USB binaries are not uploaded by this verification workflow.
Gate receipts report execution duration; GitHub step timings additionally
include dependency/bootstrap time. Never compare those two timings as if they
were the same measurement.

## Required checks and rollout

Require `CI gate` on `main`, with up-to-date branches, pull-request review,
no force pushes and no deletion. Enable the requirement only after the new
check has actually run successfully, to avoid a permanently pending check.
Use the GitHub Actions app identity observed on that run when binding the
required check. Verify enforcement through the API afterward.

At audit start, GitHub reported no classic protection or ruleset on `main`,
and no custom Actions workflow. Blacksmith is installed in the organization
with selected repository access; repository enrollment still needs actual
execution proof. Current canonical repository is `BeamoTech/beamo-wipe`;
`BeamoINT/beamo-wipe` redirects there. Current rollout evidence belongs in the
linked dated audit, not in claims inferred from this configuration.

## Publication, provenance and rollback

CI never publishes. There is no signing secret, production environment,
write permission, release trigger or cloud identity in this workflow.
A green check does not authorize a release. Publication requires separate
explicit operator authorization and a reviewed production destination/signing
procedure. Do not automatically promote unsigned CI artifacts.

The retained `cloudbuild.yaml`, `ci-cloud.sh`, trigger installer and GCS
publisher document the previous production system. They are legacy tooling,
not the current CI route. Do not invoke Google Cloud for current CI. Migration
of release credentials or publication to a new provider is a separate operator
action; no release path has been activated by adding this workflow.

Existing publisher checks remain required for any authorized publication:
clean/tagged source, all passing gates, exact artifact hashes and package
inventory, detached Ed25519 signature, no-overwrite upload, remote byte
verification, and completion marker last. Build inputs are pinned where the
project currently pins them, but Debian package repositories remain mutable;
this does **not** establish bit-for-bit reproducible ISO bytes. Record installed
package versions and hashes for each build.

Rollback remains `beamo-wipe-0.2.9-amd64.iso`, SHA-256
`4042f85e0e7c155dd2340dc93a6b879c35ebe2f13da9c81c1ba6269524a6b169`.
See [release verification](release-verification.md) and [runbook](runbook.md).
Do not relabel a fresh build as the old verified artifact.

## Failure triage

- Queued Blacksmith job: verify App enrollment for this repository; do not
  silently fall back to Google Cloud or an untrusted self-hosted machine.
- Missing KVM: fix the Blacksmith x86_64 worker capability; do not weaken the
  gate or wait on local Mac TCG.
- Tk clipping: use Xvfb 72 DPI, never VNC at 96 DPI.
- Missing live-build generated config: source checks still run; image tests
  requiring actual build outputs run against the image in the hosted phase.
- Failed tests, security scan or negative test: fix the cause; do not mask the
  exit code or weaken coverage to obtain a green check.
- Stale receipt/output: rerun on a fresh worker; never overwrite provenance to
  disguise a partial run.

## Desktop and regular-file packaging checks

Use the repository-pinned Go 1.26.8 for shipped builds. From `desktop/`,
`go test -race ./...` and `go vet ./...` run the local launcher gate.
`GOOS=windows GOARCH=amd64 go test -c -o /tmp/beamo-desktop-windows.test.exe`
compiles the Windows suite. The Blacksmith Windows job runs the actual Win32
and Windows PowerShell tests natively; cross-compilation alone does not prove
those runtime paths. The Windows fixtures include Unicode identities and
512-byte/4096-byte sector layouts.

The Linux utility integration test enumerates disks only when
`BEAMO_DESKTOP_NATIVE_INVENTORY_TEST=1`; `scripts/ci-desktop.sh` opts in on its
isolated hosted runner. Leave it unset on developer machines. All other local
launcher tests use fixture data and fake firmware. No test requests a host
restart.

The hosted Python phase installs `dosfstools` and `mtools`. With those tools on PATH, `tests/test_usb_image_readback.py` builds
64 MiB regular-file FAT32 fixtures, embeds them at the image's 1 MiB partition
offset, and checks manifest/launcher readback and failure cases. No mount,
loop device, or physical device is used. This does not replace ISO provenance,
Syslinux/GRUB boot, or the full 2 GiB image gate. The image builder assembles
and reads back a private staged image on the output filesystem, then publishes
the image and its checksum and ISO-binding sidecars with no-overwrite links.
A failed assembly or readback leaves no final image or sidecars, so a corrected
build can be retried without deleting an unverified artifact by hand.
