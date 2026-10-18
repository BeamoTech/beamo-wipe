# Final 0.2.13 hosted UI failure repair

2026-10-18 / Codex. BeamoTech/beamo-wipe, fix/safety-audit-20261015.
Parent commit 4f7ee8d434497f52b58966792ed6cc28b587635e. This is local candidate evidence;
new-commit PR qualification, protected main CI and publication remain pending.
The earlier [Tk pool record](../release-tk-pool-review-20261017/README.md)
retains the original P1 proof and its separately qualified d8f527 snapshot.
This record supersedes its overall candidate qualification after later edits.

The [original PR run](https://github.com/BeamoTech/beamo-wipe/actions/runs/39079362211)
failed ten source tests: nine Tk callback lifetime failures and one fresh GTK
Return after closing sound controls. Its PR head was4f7ee8d; its actual tested
synthetic merge source was a77fbd94a7ce4d9079f7da0125a428ea4c94e30d.
Raw JUnit, five gate receipts and logs remain in failed-hosted/. The deliberate
negative mutant failure is an expected safety check, not an extra gate failure.
The run did not qualify ISO/QEMU; its15 skips are recorded separately from the
14 local artifact skips (the additional hosted skip is the absent legacy SDK).

An unprivileged local container used the exact CI Debian digest and matching
Python3.11.2, Tk8.6.13-2, Tcl8.6.13+dfsg-2, GTK3.24.38-2~deb12u3 and GI3.42.2.
The original three-module replay reproduced all9 Tk failures with47 controls.
Source was read-only; only owned output and public CA mounts were provided,
with no physical devices, Docker socket, privileged flags or host networking.
The positively identified container was stopped/removed after every test exec
finished. Its setup-only sleep exited137 during intentional Docker cleanup;
no test process was terminated. Mount/ID and cleanup receipts remain.

Owned roots now cancel their Tcl timers without deleting Tcl procedures.
Bookworm also queues a C-level theme notification absent from `after info`.
[Upstream Tk8.6.13](https://github.com/tcltk/tk/blob/core-8-6-13/generic/ttk/ttkTheme.c#L510)
confirms the native idle callback evaluates the Tcl notification procedure.
The retirement helper retains the original ThemeChanged body and adds a
root-existence guard, so obsolete notifications return before touching dead
widgets. Live notifications, failed-destroy retry behavior, ordinary Tcl errors
and other interpreters' queued work remain. All owned-root construction failure,
wizard teardown and startup close paths use the helper. No bgerror handler is
suppressed and no native destructor is replaced by the product.

The GTK native fixture requested zero-delay XTest presses. A real256-event
trace proves215 fresh synthetic presses reused the prior release timestamp
with heldFalse and were correctly rejected by the product's repeat guard.
The fixture now requests1ms server delay for fresh presses. A new256-event
regression requires every fresh press to have a distinct timestamp and remain
unblocked. Production GTK input code is byte-identical, all16 original assertion
predicates across14 parameterized cases remain, the exact same-time repeat
tests remain, and the original2s input bound is unchanged. The old single CI
failure had no recorded event timestamps: its exact retrospective attribution
is an inference. The verified fixture defect and new strict controls are the
concrete correction, rather than a claim about unrecorded old events.

| Verification | Observed result |
| --- | --- |
| Initial explicit native-timer regression | 4 failures before product edit |
| Timer-only attempt on Bookworm | 13 failures/33 controls; untracked native notification still failed |
| Corrected matching Debian UI modules | 62 passed, including all original failed cases |
| Matching Debian native lifetimes | 77 passed,65 native children zero exit/empty stderr |
| Ubuntu focused UI | 20 passed |
| Final fresh full local gate | All9 phases passed; 10146 combined Python/Orca passes, no warnings |
| Artifact-dependent local skips | 14 exact existing IDs; retained as skips |
| Audit regressions | 61 modules/3943 cases passed |
| Full native readback | 65 clean children;37 direct source hashes |

Evidence-helper history remains explicit: the first request for40 identical
pytest node IDs ran only1 case because of de-duplication; a parameterized80-case
diagnostic then passed. A new Tcl control initially compared a Tcl string with
an integer; its failing fixture/log are preserved and conversion was corrected.
The earlier P1 native-output classifier correction is retained in its own record.
None of these helper outcomes replaces an applicable product check.

Frozen877-input map: 6582e76ea795a1e7f4f322c5f7844f82870fd3446e1bb1915e7377119ec5d93b.
Runtime SHA-256: 9e2d6373ea8e6d1e8a41d0ecf59b99f0f007681b3278ccecb483234d2f23532b.
Tk source SHA-256: 028e13c7d64c230aaaabfbd806ae900c41c64acd8e07334d3d38abd8af6c901f.
All source inputs remain unchanged through the complete local gate. Windows
crossbuild bytes are indexed to their identical earlier archive; a new compile
ran, but this is not native Windows acceptance. Hosted ISO/QEMU and native
Windows still must qualify the exact new commit. Physical/firmware acceptance
and historical incident attribution remain unproved. No physical media was
written and no production release is established by this local record.
