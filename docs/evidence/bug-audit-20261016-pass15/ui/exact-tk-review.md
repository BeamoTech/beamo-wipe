# Pass15 exact Tk repair review

Date/author:2026-10-16 / delegated Codex pass15_ui_boot.
Source-only review requested by primary; no runtime started or product/test edit.

## Exact identity

- Starting `tk_wizard.py` SHA256:
  `9abb3cf1800a04d8f094c030b2b7a2052d8da3b608389dc95bbfb07b0454a8ea`.
- Reviewed current `src/beamo_wipe/ui/tk_wizard.py` SHA256:
  `06cfd5488624c78c98d2b2cabf33256ae81403587065d8a72814ef77f8eb13bd`.
- Frozen regression `tests/test_empty_inventory_wheel_pass15.py` SHA256:
  `9e1dd204f39e96c7a6943783687481056caff0dffff3b0b520d206666c069138`.
- Compared current full Tk file directly against exact member
  `src/beamo_wipe/ui/tk_wizard.py` of
  `/tmp/pass15-primary/starting-source.tar.gz`.

## Disposition: APPROVE exact current source delta

The complete delta is six inserted lines in `_empty()`'s recursive
`bind_wheel` only. It returns before rebinding Text/Listbox/Treeview/native
scrollbars, the project's `_Scrollbar`, or an independent nested scrolling
Canvas. The outer empty-screen canvas is explicitly exempted from that nested
Canvas check, so its ordinary prose still receives the original handler.
Decorative `_Box`/Canvas objects with no scroll region remain part of prose
scrolling. Stopping recursion at an independent scroll surface preserves its
own class/widget bindings and embedded descendants' ownership.

The picker helper is byte-for-byte unchanged from the starting snapshot;
the initially misplaced guard is absent. General body focus/wheel handling,
keypress guards, consent, discovery/eligibility, countdown, tokens, methods,
erase/argv, teardown, claims and every other Tk byte remain unchanged.

Contracts match the independently measured issue: reader and its custom
scrollbar must scroll the information-only two-line reader while the outer
empty canvas remains still. Empty prose continues scrolling outer content.
Current64-case frozen regression module checks those outcomes directly with
native Button4/5 and synthetic MouseWheel, visible hit tests, three layout/type
profiles and rebuilt controls. It retains read-only text, focus, wizard state,
authorization and request invariants; callback exceptions fail; no native
application effect is allowed. The regression file hash is unchanged.

Primary reports original-source replay32intendedFAIL/32controls,0errors/skips.
The earlier first patch's32empty-UI failures showed the guard was placed in
the wrong helper; the corrected exact delta now targets the proven function.
Primary's corrected574-case rerun was active during this review. This source
approval does not claim its outcome, final full gate or native qualification.
No unresolved source objection found for these exact bytes.
