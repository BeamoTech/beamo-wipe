# PASS11 boot, launcher and build review

Baseline b46e5642d4c849d503b41d8bf562cfb1f9fad68b; 2026-10-21 America/Chicago.
Source ownership released. Only desktop/io.go and one new Go regression module
were changed. All existing Python/developer/Go test files remain byte-identical.

Two root causes were proved before their repairs. First, boundedOutput could
wait beyond context cancellation or direct-child exit while a descendant held
stdout or stderr. The root independently reproduced all three pipe variants.
Cmd.WaitDelay now bounds drain to at most100ms and preserves stricter positive
caller limits; incomplete capture remains an error. Second, embedded bytes.Buffer
promoted io.ReaderFrom, so exec/io.Copy could bypass the limitedBuffer.Write
byte budget entirely. Root independently reproduced zero/one-byte/1KiB budgets, including64KiB output.
The buffer is now a named field, ensuring writes pass through the existing cap.

Exact final baseline module:17 failing leaves/30 passing controls,52 named
outcomes,zero races. After both repairs all52 named outcomes pass (47leaves,
5parent/helper tests). Cases exercise stdout/stderr/both, cancellation/parent
exit, default/stricter drain limits, descendant EOF-release controls, direct
cancel/pre-cancel, launch failure, failed exit, stderr discard, exact limits,
and budgets0/1/1024/1MiB with one-shot or37byte chunked cap+1 overages.
All processes are this Go test executable and finite owned helpers. Completion
receipts are awaited before cleanup. Child GORACE removes only its1s exit pause,
leaving instrumentation/race detection active. No native utility/engine ran.

The exact final test hash is bound to baseline-io.go in expanded-before-inputs;
the Go baseline overlay replaces only io.go. Final green hashes are in
final-owned-source-sha256.json. Root original probes also pass independently
on the repaired source; see original-root-probes-after log/status. Fresh final
Go full race/vet/fuzz/cross-builds are root's central gate, not duplicate results.

Fresh independent plan/readiness model:162 valid authority states,162 partition-
order invariance controls,162 unrelated-entry controls,161 changed-fingerprint
observations,1620 refusal transitions and1620 clean restored controls. It uses
real plan/readiness code with fake EFI data; source hashes are bound in metrics.
It has zero mismatches/native callbacks and is supporting evidence, not extra
canonical tests. Root can replay plan_freshness_matrix_test.go by changing only
its metrics output path and using the provided Go overlay pattern.

Focused boot/build/developer Python:464 unique passes,one existing unavailable
legacy gcloud skip,zero failures/errors,32modules/465outcomes. The exact path
set and JUnit are retained. Existing fake compiler fixtures are used; actual
launcher builds, Docker and hosted CI were not launched by this reviewer.

Candidate histories are explicitly excluded from final coverage. The earliest
external cancellation probe failed one leaf/two controls. An initial new-module
format command used a wrong relative path; its unformatted baseline run and
receipt remain history. The next boundary candidate revealed byte-cap bypass;
its WaitDelay-only repair retained exactly that one failure. Small-budget and
initial model reports are history; final expanded baseline/green and final
plan model are the current records. No old test assertion was changed.

Native Windows/real inventory, ISO/KVM, firmware, physical USB and reconnect
acceptance remain unverified. Drain limits do not establish process-tree
termination. No real disk, mount, engine, firmware, power, VM, network policy,
remote write, release or hosted CI action occurred.
