# PASS12 boot / launcher / developer / build bounded review

Baseline `b462e62005a752b0e5f2a066bda19bd9c79bbd8b`, branch
`fix/safety-audit-20261019`, repo `/workspace/beamo-wipe`, 2026-10-21 UTC.
No repository file was edited by this reviewer. Source ownership is released;
root retains validation, repair assignment, integration and release ownership.

Read AGENTS.md, current development/CI guidance, unfinished work and PASS11 boot
and root reports. Blacksmith is current; no legacy GCP instruction was applied.
No dependency, policy, remote, Docker, actual build, native inventory, engine,
real device, mount, sysfs/firmware, host power or VM operation occurred.

## Proven baseline observations awaiting root validation

1. `linuxMedia` uses permissive `json.Unmarshal`. Contradictory duplicate
transport/path/root fields and case/escaped aliases overwrite earlier evidence;
null-last string fields retain earlier string values. Malformed UTF8 and lone
UTF16 surrogates are replaced rather than refused in serial identity.
`native_parse_probe_test.go` records 9 failing leaves and 4 passing controls
using the existing regular-string fixture only; uncached race run, exit 1.

`native_readiness_probe_test.go` separately composes actual linuxMedia,
makePlanForHost and explainReadiness with fake EFI option bytes. Duplicate
SATA-to-USB transport and contradictory source path both yield Direct=true,
USB check pass and route check pass. It has 2 failures / 2 positive/refusal
controls. No firmware interface is invoked. This establishes observable
acceptance of contradictory evidence, not reproduction from actual lsblk.
Invalid Unicode is a separately observed accepted/collapsed identity input;
no native utility producing such output has been demonstrated.

2. `dev.doctor` catches ValueError/TypeError around JSON decoding but not
RecursionError. Two bounded 20,000-level injected local-tool outputs raise
RecursionError with no JSON report. A valid probe and a wrong-type probe
produce the prescribed status 0/status 2 report controls. `doctor_probe.py`
and `doctor-probe.json` retain the exact replay and result, exit 1. An earlier
1,100-level exploratory input was cleanly refused; it was below this runtime's
JSON recursion threshold and is not claimed as a failure.

Root was sent all proof locations before any edit. No speculative fix or new
canonical test has been added. No further build-publication defect was proved;
the existing staging re-verification and source-input checks address the
reviewed sequential-copy concern.

## Fresh independent request epoch model

`request_epoch_model_test.go` exercises actual API handlers / inspectPlan with
fake delayed snapshots, separate from the prior plan-fingerprint models.
16 states cover canceled old workers with ready/refusal results; fresh
ready/refusal results; old-worker completion before or while the fresh handler
owns its busy epoch; and preview/ordinary fake callback contexts. The final
model waits for the actual busy latch before releasing the delayed worker.
All finite fake workers settle before the next scenario.

Final uncached race run passes 16 canceled publications, 16 fresh publications,
16 stale-revision restart refusals, 16 current-revision positive/refusal controls
and 64 closed-session refusals, zero native callbacks. Metrics and overlay are
retained. Source hash final model:
`6da393504529b038c735d19969c81d515f99747d6ebb5153c9f8da650de26bf1`.
This supporting model is not additional canonical test coverage.

## Focused checks

- Existing focused Go tests, `go test -race -count=1`: 108 named pass events,
  zero skips/failures/races; `go vet .` exit 0. Native inventory opt-in remains
  unset. This is a focused count including subtest events, not whole-package
  unique coverage.
- Existing Python developer tooling plus 14 adjacent desktop/build/launcher
  modules: `python3 -W error -m pytest ...`, 310 passed in 21.39s, zero
  skips/failures/errors/warnings. `focused-python.xml` is the JUnit result.
- Source inputs did not drift between the proofs and final reviewer checkpoint.
  `review-inputs.json` binds the original source and probe inputs; final evidence
  ledger binds the completed model (its earlier exploratory hash in the input
  snapshot is historical).

All checks used `/workspace/beamo-tools/activate.sh`, Go 1.26.8, child umask
022, owned regular temporary files and fake callbacks only. No GUI was needed.
No full test gate/fuzz/container/build was duplicated. Existing test assertions
remain byte-identical. Native Windows, ISO/QEMU, actual devices/firmware/media,
pinned-browser/network and physical reconnect qualification remain unverified.
Earlier operational-backlog export auto-review remains root-owned; no retry.
