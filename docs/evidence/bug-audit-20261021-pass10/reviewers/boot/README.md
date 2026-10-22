# PASS10 boot/build review

2026-10-21 America/Chicago / Codex reviewer boot_pass10. Baseline
7047dfb8c22d0b17faad2d5de1ec470b2debfaac, /workspace/beamo-wipe,
branch fix/safety-audit-20261019. Source ownership released to root.

One new root cause was independently confirmed by root: the launcher did not
atomically retire action authority when its session ended. A successful close
only notified the event loop after unlocking and writing/flushing the response.
Previously decoded or concurrent handlers could still publish readiness or
invoke the fake restart provider. The idle ticker similarly cached idle=true
after unlocking, leaving a window for a new action before server exit.

Only desktop/main.go and the new desktop/close_admission_pass10_20261021_test.go
were edited, following root's explicit bounded assignment. No old test changed.
retireLocked consumes the restart plan, publishes a later non-ready revision and
marks the session terminal under the existing mutex. Valid API actions check
that terminal state before reading state or admitting work. Close retires before
unlock/response. retireIfIdle checks age and busy ownership and retires in one
critical section; the ticker uses that atomic decision. A busy action remains
owned, and preview/manual Windows policy remains unchanged.

## Before and after evidence

- Original external httptest proof: three failures and three normal controls.
  Post-close restart/check/state remained admitted/published; normal restart,
  check and busy-close behavior passed. Original source is close_admission_probe_test.go.
- Deterministic delayed-body proof: one in-flight restart failure and one normal
  in-flight control. No socket, process, firmware or real restart was involved.
- Idle historical trace: exact baseline ticker lock/age/busy/unlock statements
  are bound by idle-baseline-trace-input.json. A handler scheduled between that
  unlock and the cached idle exit invokes the fake restart provider: one failure,
  one busy-action control. This is a historical scheduling trace, not a model
  to run against repaired source. The final model calls the real idle helper.
- Exact final new regression module: 24 leaf cases in four parents. Archived
  baseline desktop source executes 18 failing leaves and six positive controls
  under Go race; zero race reports. expanded-before-receipt.json binds baseline
  main SHA and exact final new-test SHA. baseline/desktop retains all 57 inputs.
- Final full Go race: 366 named pass events (338 old plus 28 new parent/leaf
  events); the same two explicit native inventory/platform skips. Go vet passes.
- Fresh strict Python boot/build/developer subset: 25 modules, 255 unique passes,
  zero failures, errors or skips, warnings treated as errors.

The new cases cover close before subsequent valid API actions, already decoding
bodies, a blocked close response flush, revoked plan/readiness/revision, and
normal/busy/unauthorized/malformed/manual/preview controls. The normal-check
positive control retains Windows' existing manual-only policy while requiring
the actual ready fake route on Linux. No native Windows execution is claimed.

## Independent root replay model

retirement_idle_matrix_test.go and retirement-model-overlay.json run a pure fake
216-state model. It covers a future clock, exact five-minute boundary, one
nanosecond past that boundary, old idle state, busy ownership, already closed
sessions, repeated retirement and subsequent state/check/restart/close actions.

Actual metrics in retirement-idle-matrix.json: 24 new idle retirements,
72 busy-action preservations, 72 already-closed idempotence checks, 96 repeated
retirements and 96 post-retirement API refusals. Positive controls include 12
normal fake checks, 12 normal closes, four explicit fake restarts, four preview
restart controls and four manual-policy refusals. Zero mismatches/native callbacks.
These supporting counts are not added to canonical Python or Go totals.

Root replay can copy the model and change only its metrics output destination:

    source /workspace/beamo-tools/activate.sh
    cd /workspace/beamo-wipe/desktop
    go test -count=1 -race -overlay <overlay.json> -run '^TestPass10RetirementIdleMatrix$' -json .

The final new regression pattern is:

    ^(TestCloseRetiresEveryAPIActionPass10|TestCloseRejectsAlreadyDecodingActionsPass10|TestCloseRetiresBeforeResponseFlushPass10|TestClosePreservesOpenAndBusyControlsPass10)$

## Scope and retained history

Static review also covered EFI parsing and firmware rollback ownership,
readiness and revision binding, Linux/Windows platform gates, bounded file reads,
source snapshot/digest and bundle publication/retirement, kiosk fallback and
portable developer preflight. No second independent defect was promoted.

Historical files preserve the initial formatted-test setup, the first
17-failure/seven-control candidate before the stronger direct retirement
assertion, and the Windows positive-control fixture correction. No old assertion
was weakened. The first gofmt command used an incorrect relative path; it did not
edit source and was corrected with an absolute path before final formatting and
exact-source replay. All final source/status/hash records identify the final
module, not those earlier snapshots.

No Docker, hosted CI, remote write, native device/inventory, actual firmware,
restart/power, guest or physical media action occurred. Native Windows, isolated
ISO/KVM, physical hardware and reconnect qualification remain unverified. Parent
owns final comprehensive gates, staging, commit, backlog and publication status.
