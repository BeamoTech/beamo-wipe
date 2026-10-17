# Pass17 independent review of the final change set

Follow-up status: the primary subsequently proved the adjacent inherited-ID
projection defect described in `bridge-proposal.md`. It authorized the exact
targeted-refusal patch after authenticating both corrected probes. The final
discovery approval and current hashes are in the addendum to
`final-source-review.md`; those supersede the discover.py row below. This
child's source review approves that correction for the primary's fresh gates.
The approval below otherwise covers its earlier exact reviewed bytes; any
subsequent primary-owned runner/fixture changes need their separate review.

2026-10-17, Codex `/root/pass17_discovery`; shared worktree
`/root/dev/Beamo Wipe`, branch `fix/safety-audit-20261015`, HEAD
`35107a8d1a701093eac876a58ab4efd50e291673`. Source-only cross-review: this
child ran no runtime tests, engine, device inventory, network, loop or guest
operation. The primary owns runtime attribution, source freezing and acceptance.

I compared runner, Tk and plain-console changes directly with the primary's
`starting-inputs.tar.gz`, and reviewed the exact final discovery implementation,
all four new regression modules, their fixtures, nearby result/authorization
callsites and primary test-launch protections. The UI peer's final hash receipt
matches these readback hashes. The primary reported 826 fixed-three cases and
then 861 final focused cases passing; those are primary-owned runtime results,
not a separate child execution.

## Source findings

**Approved at the exact hashes below; no additional defect or safety weakening
found in the reviewed change set.**

The runner's timestamp/severity discriminator prevents an unprefixed model
continuation from proving that no erase occurred once the log contains native
record context. It applies to busy/open/geometry records, where the stronger
unchanged-disk claim matters. It does not grant positive completion or suppress
actual erase-activity contradictions. Canonical timestamped failure records
remain attributable; wholly bare legacy parser inputs retain their explicit
contract. Short optional prefixes cannot authenticate a continuation. Whole-log
projection retains the first native record at its original position, counts it
toward the existing evidence-byte cap, and rejects overflow. It does not append
synthetic trust context or reorder earlier terminal/progress records. Poll,
cancellation and saved-evidence callers continue using the common method-bound
completion evaluator. Review covers large-file identity and line-bound checks
around the added retention, not only the small-string parser.

Tk startup tracks only its initial idle focus job and current polling job.
The polling callback clears its already-dispatched ID before doing work and
stores a replacement only when one is actually scheduled. Finally retires the
two owned IDs before its last destroy attempt, including paths where close or
an external destroy already removed the widgets. Cancellation does not rely on
enumerating a destroyed widget's command registry. Already-fired IDs and an
already-destroyed window are tolerated through TclError. It does not pump the
event loop, run stale scripts, cancel peer-interpreter timers, or alter
StartupRun's wizard/failed/abandoned result contract. Start/mainloop exceptions
still propagate after cleanup.

Plain console retires queued input immediately after the full visible review
countdown and immediately before accepting the enabled erase prompt. It requires
a real TTY, a valid nonboolean descriptor, ICANON and a successful TCIFLUSH.
Neither terminal mode nor the host terminal is modified. Canonical terminal
reads return one completed line; the dedicated real-PTY METHOD/ERASE control
checks that the prior method read does not leave ERASE hidden in Python's
buffer while kernel retirement runs. Partial prefixes are also discarded, so
an early `ER` followed by later `ASE` cannot assemble an authorization.
NonTTY streams are allowed only for the existing fake preview/dry-run path;
the real path raises EOFError. Terminal-control errors do the same. Existing
outer EOF settlement handles interface loss and existing liveness/shutdown
guards remain in force. The eventual shared `confirm_erase` claim still checks
owner, exact token, current discovery/context and countdown. The helper does
not itself launch, authorize, change a gate or auto-accept buffered input.

The inherited-ID fix uses the same resolver for selectable/display and
safety-only physical observations. It validates every inherited candidate,
rejects conflicting meaningful IDs, compares equivalent WWNs canonically,
allows a meaningful parent to remain authoritative, and preserves raw padding
when no stronger ID exists. An unrelated clean target is retained when only
an unmounted malformed candidate is skipped; uncertainty about the boot or a
mounted physical source still refuses targets.

## Regression and fixture review

All four new modules exercise observable behavior, with original assertions
retained. The console fixture's corrected method setup explicitly returns to
CONFIRM and re-enters the token after a method change revoked authorization;
it does not bypass that state transition. Added helper cases retain the real
PTY early/middle/late proof and add partial input, buffered prior-line, fake vs
real nonTTY and unusable control cases. Startup observes actual Tcl bgerrors
after destruction and bounds only its own worker/PTY/interpreter cleanup.
Runner large-log cases use ordinary files and an exited fake process; discovery
uses copied injected inventories. Native application/process/discovery/power
effects are denied in the fixtures. No regression assertion was replaced with
an expected exception or broadened success condition to make the fix pass.

## Test-launch protections and incident limits

The primary uses the same installed interpreter through a no-space symlink;
its retained probe demonstrates why the old spaced shebang failed and why the
alias executes the fake stub. The alias is ahead of PATH fallback wrappers.
The wrappers reject known unmocked curl/sudo/losetup/docker/QEMU/gh/aws calls;
the gcloud wrapper allows only the exact offline file-list fixture, in a
canonical private owned pytest upload directory with a fresh owned config
location. It strips credential overrides and disables credentials, prompts,
updates and telemetry before that local SDK operation. Its actual command is
not hosted CI, authentication or publication. The 12-case intercepted authority
probe records no actual CLI executions. The existing loop fixture invokes
`losetup` by PATH, so the rejecting wrapper covers the prior shebang-fallback
mechanism. GOTOOLCHAIN=local avoids automatic Go toolchain acquisition.

These PATH wrappers are targeted fallback protection, **not a universal process
sandbox against arbitrary absolute-path invocations**. No such bypass was
found in the reviewed affected fixtures or primary gate orchestration. No
claim that a zero fallback log alone proves isolation is made here.

The gate driver serializes its nine phases, removes only its owned old main
and Orca JUnit files before the test phase, and records each exit and UTC start/
end. The canonical main/Orca pair uses separate private displays at 72 DPI and
separate private runtime directories. Cross-build environment is scoped to
that phase and does not establish native Windows acceptance. The primary must
still authenticate fresh reports, source/config identity and actual artifacts.

The pass16 incident correction is supported by its retained trace: fake loop
bookkeeping stayed empty while actual subprocess output reported native
regular-file loop attachments and ownership-checked cleanup. Empty fake state
does not prove no attachment. The source/read-only follow-up cannot reconstruct
the original loop IDs or lift the isolated-worker requirement. Neither this
review nor a new passing test attributes pass8's historical SIGTERM or recovers
pass9's unavailable original timing trace. Those remain separate acceptance
limitations; physical/firmware/native final-public qualification remains unrun.

## Exact reviewed bytes

| File | SHA256 |
| --- | --- |
| src/beamo_wipe/discover.py | 0203da10e2efde1db560d5eecc853dc503aac3e3c906ca053b74fcfd0a5bfddf |
| src/beamo_wipe/nwipe_runner.py | ddfc855a50cb06816f1f094caefef53acdec562039e9171b163273d396d13441 |
| src/beamo_wipe/ui/tk_wizard.py | bb64632df587965f41afc70efe2201d3b776579038d680c3a2405319764f170d |
| src/beamo_wipe/ui/console_wizard.py | 1c3dc2f6839b7a4b1c7d43225b2175b7bc8b5f5d2b5af63aa17725c417c5ded5 |
| tests/test_descendant_hardware_ambiguity_pass17.py | 55c79450a3dd7676876ae5896569653d5bb913f962e92cc3e0fd17ddfc25900f |
| tests/test_runner_model_lf_noerase_pass17.py | 076ddb3f20082deb045c747e28853c828ca15a42091211e833e4d71701d959cf |
| tests/test_startup_callback_retirement_pass17.py | b008493fee9540ca0f659a54aaca491b4197f93566e5a4fff29d03d6369bc65c |
| tests/test_plain_erase_typeahead_pass17.py | 671fe42ce50ee56fa1be19331aa989c2191709d761afb857e5054ccffb77d012 |
| /tmp/pass17-primary/run-gates.py | 56a4508e0adafb16786f4c6afcb6e344f94e5f926e1271e804353a417232a076 |
| /tmp/pass17-primary/run-regressions.py | 2078bc9e715e24f9da3a5d111d4c37c341a3be4d43a4fca892ce9899fa102967 |
| /tmp/beamo-pass17-fallback-guard/gcloud | a91cacf1cb44f2d32e58062682b1c33ce58ff8d3e808dc1162ae0de06a1603ec |
| /tmp/beamo-pass17-fallback-guard/curl (generic wrapper) | cba41168ef00df7373f4415f3de107c7b0ab47927121235609e4e5749c97c051 |

Any change to these source/test bytes requires fresh review and affected
verification. This source approval does not approve a release, merge, physical
test, hosted job or unsupported acceptance substitution.
