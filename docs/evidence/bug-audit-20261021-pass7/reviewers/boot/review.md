# PASS7 boot/build review

Baseline938fe60347c78f2a745d5d5b04e30dfa013da809, branchfix/safety-audit-20261019.
Source hashes in original-source-sha256.json. No repository/index/remote changes.

One new bounded low-severity preflight finding, awaiting root independent replay:
dev.py live_environment catches OSError but an undecodable ordinary fake Linux
cmdline raises UnicodeDecodeError. It crashes development preflight rather than
returning unknown/live=True and the documented conservative refusal. This does
not establish an unsafe erase or allow a preview onto an actual live system.
Actual byte-decoding proof (not a fabricated exception) uses a regular temp
marker b'boot=live label=\xff', with every native marker/mount callback guarded.
Red4-case proof:1FAIL3controls (normal false/live true/denied true). Source probe
and raw XML/text are test_dev_cmdline_decode_probe.py and dev-cmdline-original.*.
Root decides whether to include this narrow availability repair; no edit granted.

Reviewed desktop main.go HTTP host/origin/token/body/duplicate/revision gates,
single-use restart state, blocked probe/idle ownership and browser poll/state
validation; identity null/type/completeness/status; media marker/case/link checks,
regular-descriptor digests, framing and per-file limits; EFI path/header/node/
geometry parsing and exact-route fingerprint; Linux partition parent/global-ID/
geometry/probe/live-state checks; Windows fake inventory script/native/manual
refusal; restart transaction exclusive-create and value rollback refusal.

Reviewed live kiosk finite retries/fallback/EOF/speech/Stop-before-power gate,
service tmpfs/no-network settings and shell wrapper isolation; build_desktop
source snapshot/digest/build env/output-lock/prior receipt retirement/publication
readback/cleanup; wrapper staging tracked regular inputs, approved hooks/include
sets, directory pinning, live asset checks; ISO copy input binding and prior
bundle verification/finalization; development fake environment and doctor probes.
No additional newly proved root cause in these reviewed boundaries.

Uncached Linux Go race:338named pass events,2explicit native skips; no fail.
Go vet0. Native inventory opt-in was deliberately absent. Neither native lsblk
nor Windows PowerShell/runtime executed. Bounded boot/developer16-module
Python baseline:285PASS/0SKIP/0failure/error under-Werror, privateXvfb87272DPI.
Its existing Linux probe fixture executes15fake scenarios; it is not native
platform qualification. These supporting results overlap root's final suite,
not additional canonical unique passes. Selection/command/XML/raw logs retained.

No Docker/network/auth/policy/hostedCI/release/actual device/mount/power/firmware/
USB/guest or real engine action. Root owns final source freeze/gates/retention/
canonical backlog/local commit and publication decision. Native Windows/macOS,
ISO/KVM, firmware and physical media/reconnect remain unverified.
