# Pass 16 incident review: three native loop probes crossed the test boundary

- Written 2026-11-15 (started 17:10:53Z, file written 17:13Z) by Claude (Opus 5.5) from
  the evidence retained in this directory and the source on main `93a7c9e9`.
  Nothing was re-run. No loop device, losetup, WSL, host or hosted CI command
  was used for this review.
- Scope: the three `test_loop_pool_prepares_concurrent_nodes_and_cleans_only_owned_files`
  cases in the failed "space-interpreter" full run of 2026-10-17. Its pytest
  phase ran 03:00:28-03:12:46Z and ended `23 failed, 7942 passed, 14 skipped`.
  The other fallbacks in that run (public metadata downloads, system xorriso on
  an ordinary temporary file) share the root cause and are only noted here.
- This file is an addendum. It is not part of the original sealed artifact set,
  so it is not listed in `artifacts-sha256.txt`. The original files are
  unchanged.

## Evidence used

Each file's sha256 was re-checked against `artifacts-sha256.txt` on 2026-11-15,
and all match.

| File | Recorded sha256 |
| --- | --- |
| `primary/failed-environment-boundary-audit.json` | `64cea6fe5d942a191db9a479c16bfd4007b26a86e07b53992d1ac53a50de94af` |
| `primary/initial-misread-boundary-audit.json` | `312d55834b265c8329a8271c865f9f7c1908efe7a76098f4b85b08f20d7e3b57` |
| `primary/system-tool-resolution.json` | `a1c38a57c3c6c3238079c00716d74434f84030affa3a57c9bfc2f6f2795e18fa` |
| `primary/interpreter-path-probe.json` | `2ddde37f7fcc09a5358bf661040fed96ed7e3a302d33a449fd756d9820bc1c12` |
| `primary/space-interpreter-final.txt` | `db7380c3bee53242b572c12c445e5c669de834c3373b923b21769e1615dea274` |
| `primary/space-interpreter-local-gate-status.json` | `abbe69bdfb1d4cddb2cb78ab96c9dd4b84dbb0c3b78834b2c36eab291da70945` |
| `primary/fallback-guard-manifest.json` | `7624a328e5f506e6ed8cc788056d2caf20018e1ba1d9180ac5f3a32469cfa048` |
| `primary/fallback-guard-source.sh` | `8f0cee76eb36b50ed623d59610eeda9b3091a2eb6a241cee84fbefec4bb6d40a` |
| `primary/fallback-guard-probe.json` | `43c7eb2d8b42c74423d286706c3d2576622bf534ad08d78924040b6d73eef7a7` |
| `primary/final-summary.json` | `346a2149d009f030508e3391a250503800f1634d5942820d3926debb7fe46aaa` |
| `primary/checkpoint-history.md` | `a7d92339c971741097599184dc498c0ed6ea9181c52765d9c87a0cff03f876de` |
| `README.md` | `43333f298d06f852ca091c522a3a07429fdbd5d558741b1d4a2fb989dd505e61` |

Source: `tests/test_blacksmith_ci.py` (lines 103-149 on `93a7c9e9`) and the
second `sudo python3 - <<'PY'` block of `scripts/check-ci-kvm.sh`. That block
is byte-identical at the pass's HEAD `35107a8d` and on main `93a7c9e9`.

## What happened

1. **The fake could not run.** The test writes a fake `losetup` into a private
   `bin/` directory with the shebang `#!{sys.executable}`. The audit's
   interpreter was `/root/dev/Beamo Wipe/.venv-linux/bin/python3`
   (`interpreter-path-probe.json`, case `space`). Linux splits a shebang at the
   first space, so the kernel looked for an interpreter named `/root/dev/Beamo`.
   That does not exist, so the exec failed with `ENOENT`. The same interpreter
   through a no-space alias ran a probe script correctly (case `plain`,
   `PASS16_SHEBANG_OK`).
2. **The real tool ran instead.** The test runs the probe with
   `PATH=<fake bin>:<inherited PATH>`. When one PATH entry fails, the
   subprocess exec keeps searching. It therefore ran the next `losetup` on
   PATH: the system binary `/usr/sbin/losetup`, sha256 `44ccbcc5…6f0f02`
   (`system-tool-resolution.json`). pytest ran as root (`/tmp/pytest-of-root/…`)
   on a host where `/dev/loop-control` and `/sys/block` existed
   (`loop_device_metadata`).
3. **The real probe ran three times.** The probe code is the shipped one, not a
   test double. Each run did the following:
   - Created a private `mkdtemp` directory under the test's `TMPDIR`.
   - Made eight 1 MiB sparse regular files there.
   - Attached each one read-only with `losetup --find --show --read-only <file>`.
   - Before detaching each loop, checked with
     `losetup --list … --output BACK-FILE` that it was still backed by that
     exact file.
   - Detached each loop, deleted the files and removed the directory.

   If any ownership check or detach failed, the code exits nonzero and keeps
   the backing files. All three cases returned 0
   (`actual_loop_probe_failure_messages`), so every check passed. Two cases'
   captured output still shows "Eight private regular-file loop attachments
   succeeded." and "Private loop probes detached and removed".
4. **The test's injected failures had no effect.** The `attach` and
   `ownership` parameters only work inside the fake, so the real tool behaved
   the same in all three cases. The test failures prove the fake was bypassed:
   `peak` stayed 0, and the `attach`/`ownership` cases returned 0 where a
   failure was expected.

## What was and was not affected

- **Attachments:** at most 24 loop attachments (3 runs × 8), every one
  read-only and backed only by a test-owned 1 MiB regular file in the test's
  private temporary directory. Return code 0 means all 24 passed the ownership
  check and were detached, and the backing files and directory were removed.
- **Devices:** no block device, physical disk or USB was a loop backing, a
  probe target or a wipe target. The wipe engine (nwipe) was not invoked
  (README and checkpoint 5).
- **Writes:** no data was written through any loop device; every attachment
  was `--read-only`.
- **Follow-up inventory:** a read-only follow-up at 2026-10-17T03:27:32.615704Z
  ran `/usr/sbin/losetup --list --noheadings --raw --output NAME,BACK-FILE`.
  It returned 0, found no matching fixture backings and no leftover
  probe-prefix directories, and did no writes or detaches
  (`readonly_followup`).
- **Not recoverable:** the loop device numbers used were not retained, so
  which `/dev/loopN` nodes were briefly attached is unknown. On kernels that
  allocate loop nodes lazily, the probe may have left extra empty nodes. They
  hold no attachment and are harmless.
- **The boundary was crossed.** Kernel loop devices on that host were outside
  the allowed test boundary. The run's results carry no "fake-only" claim.
  The audit already records this, including the correction of its first
  misreading in checkpoint 4 (`initial-misread-boundary-audit.json`).

## What the pass 16 correction fixed, and what it did not

- **Fixed for that audit:** the corrected runs used a no-space interpreter
  alias. They also put rejecting stubs first on the child PATH in
  `/tmp/beamo-pass16-fallback-guard/` (`fallback-guard-manifest.json`). The
  stubs covered `losetup`, `sudo`, `docker`, `qemu-system-x86_64`, `curl`,
  `gh`, `aws` and a reviewed `gcloud`. Each one logs the attempt and exits 97
  (`fallback-guard-source.sh`). The final gate recorded
  `forbidden_fallback_attempts: 0` (`final-summary.json`), and the 12-case
  guard probe recorded `actual_cli_execs: 0`.
- **Not fixed in the repository:** those guards lived only in the audit's
  temporary run setup. On main `93a7c9e9` (checked 2026-11-15), the test still
  writes its fake with a `#!{sys.executable}` shebang and still appends the
  inherited PATH. It also still runs the real probe source.

  The same fallback therefore happens again whenever both of these hold:
  - the interpreter path cannot be a shebang target (for example, it
    contains a space);
  - pytest runs as root on a machine with usable loop devices.

  Correction (2026-11-15 17:18Z, see the follow-up section below): an
  earlier version of this review said that
  `tests/test_qemu_bus_journeys_20261028.py` and `tests/test_runbook.py` use
  the same pattern. They do not. The first runs `#!/usr/bin/env bash` scripts
  explicitly with `bash` and asserts that `losetup` is absent. The second
  only reads `docs/runbook.md`. The files that did use `#!{sys.executable}`
  fakes on main were:
  - `tests/test_blacksmith_ci.py`: `docker`, `sudo`, `losetup` and
    `dbus-run-session`;
  - `tests/test_qemu_iso_inspection.py`: `xorriso`;
  - `tests/test_usb_download_verification.py`: `curl`.

  The `xorriso` and `curl` fakes are the other two tools that fell back
  during pass 16.
- **Hosted CI exposure is low but unverified.** The main pytest gate runs as
  root inside a Docker container. That container gets `--privileged` only for
  the qemu gate (`scripts/ci-blacksmith.sh`) and uses `/usr/bin/python3`, so
  its shebangs are valid and the fallback should not trigger there. That loop
  attachment would also fail inside the unprivileged container is expected but
  was not tested here.

## Disposition

- **Root cause:** attributed. The space-bearing interpreter made the fake's
  shebang invalid, and the PATH fallback then reached the real `losetup`, run
  as root.
- **Impact:** bounded by the probe's own design (read-only attachments of
  private regular files, each ownership-checked and detached) and by the
  read-only follow-up inventory. Nothing indicates harm to any device or data.
  The loop numbers cannot be recovered and stay unknown.
- **Effect on PASS16:** this closes the "review the incident" part of PASS16's
  remaining acceptance. It does not close the other open parts, which stay as
  recorded:
  - the attributable platform evidence for pass 8's 06:29 UTC SIGTERM/exit 143;
  - the missing pass 9 timing trace;
  - the platform and physical qualification.
- **Recommended follow-up (needs its own reviewed change and Jack's approval
  to push):** make fake-tool tests fail closed. Some options:
  - give the subprocess a PATH that contains only the fake `bin/` directory
    plus absolute paths for real tools it truly needs;
  - put rejecting stubs for `losetup`, `sudo`, `docker`, `qemu*`, `curl` and
    `gh` ahead of the inherited PATH, as pass 16's guard did;
  - skip the test with a clear message when `sys.executable` is not a valid
    shebang target.

  Until then, do not run the suite as root on a machine with loop devices
  unless it is a disposable isolated worker.

## Follow-up applied (2026-11-15 17:18Z, local commit, not pushed)

- New `tests/fake_tool_shebang.py` provides `python_shebang()`. It returns
  `#!<python>\n` only when Linux can start that interpreter: an absolute
  path with no blank, at most 127 bytes including `#!`. Otherwise it fails the
  test (`pytest.fail`, never a skip), so a fake that could not start is never
  written.
- All six `#!{sys.executable}` fakes listed above now use it.
- `test_loop_pool_prepares_concurrent_nodes_and_cleans_only_owned_files` now
  runs the real probe source with `PATH` set to the fake's directory only. If
  the fake cannot start, `losetup` is not found and the probe fails. The PATH
  search can no longer reach `/usr/sbin/losetup`.
- New `tests/test_fake_tool_shebang.py` covers the helper with nine cases
  (three accepted, six refused). The refused cases include the pass 16
  interpreter path.
- Limits:
  - The other fakes still append the inherited PATH, because the scripts
    they drive need real `bash` and core utilities. For those fakes the
    shebang check is the protection.
  - The changed Linux tests were not run here (no WSL/Linux in this pass).
    Only lint and the portable helper test ran.
