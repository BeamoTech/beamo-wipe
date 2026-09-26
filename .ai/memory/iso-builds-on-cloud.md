# Heavy x86_64 image builds: Blacksmith

The operator explicitly corrected the CI platform on 2026-09-26: **use
Blacksmith, not Google Cloud**. This supersedes the older GCP instructions.

- Workflow: `.github/workflows/ci.yml`, stable check name `CI gate`.
- Runner: `blacksmith-8vcpu-ubuntu-2404`, disposable x86_64 Linux with KVM.
- Shared gate implementation: `scripts/ci-hosted.sh`; isolated Docker runner:
  `scripts/ci-blacksmith.sh`. All image/test userspace is pinned Debian bookworm.
- Run all gates on PRs/main, including QEMU and the image vulnerability check.
- Retain run URLs, receipts, hashes and timings; do not download duplicate ISOs
  onto this Mac. CI verification does not publish a production release.
- Google Cloud scripts/config are retained historical tooling. Do not use them
  or request gcloud authentication for the current CI task.
- Check `docs/ci.md` and dated audit evidence for rollout status. Configuration
  and an installed Blacksmith App alone do not prove successful execution.

Local pytest and previews stay on the Mac with fake disks. Docker amd64 and
QEMU x86_64 here are emulated and cannot replace the hosted image gate.
Never pass a host block device to a guest; QEMU uses disposable regular files.
