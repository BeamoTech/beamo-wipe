# TkWizard trace cleanup implementation checkpoint

2026-10-17, Codex child `/root/pass19_ui_boot`. Root independently ran and
reviewed the prepared full-constructor proof on unchanged source: eight cases
gave six intended AssertionError failures and two live-input controls. Its raw
evidence is `/tmp/pass19-primary/fixture-original.*`. Root approved this minimal
fix after that proof. The earlier `source-audit.md` and receipt retain the
pre-proof candidate state rather than silently replacing that history.

`src/beamo_wipe/ui/tk_wizard.py` now saves the exact confirmation and keyboard
typing trace tokens as `Optional[str]`. At teardown it clears each owned token
first, then removes that exact callback before destroying the root. Repeated
teardown and lightweight controllers missing these attributes are harmless;
only `tk.TclError` from already-removed trace/interpreter state is caught.
Independent observers and callback bodies are unchanged. There is no global
trace sweep and no disabled callback pretending that cleanup happened.

The root-approved eight-case proof was copied byte for byte to
`tests/test_tk_owner_trace_lifetime_pass19.py` (SHA256
`dfa703b52c8f404771131afdd5a80235670bba31f87b747a7b6a414401d20d98`).
The exact incremental patch and before/after hashes are recorded in
`tk-owner-trace.patch` and `tk-owner-fix-receipt.json`.

No runtime was executed by this child. Fixed, adjacent and complete applicable
verification remains root-owned and pending at this checkpoint. The shared
accessible-runtime and pass18 checkbox fixture corrections belong to root and
were not edited here. No other runtime, method, authorization, command, claim,
pin or automation bytes changed in this child action.
