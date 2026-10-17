# Finite product-owned Tk field inventory

2026-10-17 / pass20_tk_lifetime. Source-only extraction and manual review of
`src/beamo_wipe/ui/tk_wizard.py`, SHA256
`23d280b0451d3e25d64387de62d4912a8867ffbdec934244efe6a7f7a7ee0615`.
No product imports, Tk, tests, collectors, threads, or child processes executed.
The accompanying JSON records every assignment location and every other self
assignment, including nested callback assignments and all container item writes.

The complete app-owned native/widget field list has **48 fields**:

| Group | Exact fields | Disposal value |
| --- | --- | --- |
| 17 fonts | `font_hero`, `font_h`, `font_lead`, `font_b`, `font_bold`, `font_size_big`, `font_s`, `font_s_bold`, `font_tiny`, `font_meta`, `font_btn`, `font_mono`, `font_mono_bold`, `font_mono_sm`, `font_entry`, `font_stat`, `font_brand` | `None`, after pinning |
| 3 images | `_logo_header`, `_logo_splash`, `_support_qr` | `None`, after pinning |
| 3 persistent variables | `_confirm_var`, `_typing_var`, `_owner_var` | `None`, after pinning and retiring exact owned traces |
| 21 widgets | `_body`, `_footer`, `_header`, `_strip`, `_hint`, `_primary`, `_countdown_ring`, `_countdown_num`, `_countdown_label`, `_progress_label`, `_progress_pct`, `_progress_bar`, `_match_label`, `_match_icon`, `_match_pill`, `_pick_canvas`, `_body_inner`, `_body_canvas`, `_support_lead`, `_more_button`, `_power_label` | `None`, after ordinary destruction |
| 3 widget containers | `_pick_cards`, `_keyboard_layout_cards`, `_keyboard_language_cards` | empty dictionaries |
| 1 root | `root` | `None`, after local pin and ordinary destruction |

The initial constructor does not initialize `_more_button`, `_power_label`,
`_keyboard_layout_cards`, or `_keyboard_language_cards`. Partial-construction
retirement must tolerate their absence. Setting a known missing field to its
disposal value is safe; invoking methods on a missing/None field is not.

`_draw` resets several current-screen fields but omits `_more_button` and both
keyboard-card dictionaries. The keyboard dictionaries can retain destroyed
cards after navigating away; do not rely only on the current root child tree.
The complete finite list above covers these stale app-owned references.

Two additional containers are not themselves Tk resources:
`_refresh_results` and `_refresh_threads`. They can retain exceptions, workers,
and `self`. Clearing them under the existing `_refresh_lock` after marking the
UI dead removes unnecessary retention. A late worker checks `_ui_dead` and must
still discard its outcome. Do not block indefinitely joining a discovery worker.
Keeping these containers also remains safe only if their retained UI is fully
detached from the 48 native/widget fields.

The remaining 38 assigned self fields contain Wizard state, layout primitives,
flags, numeric geometry, token strings/lists, or the refresh lock. They are all
listed in JSON for review. Do not blanket-clear them. Exact after/trace tokens
still require their existing cancellation/removal before resource detachment.
The only dynamic `setattr(self, ...)` calls update those known trace and timer
token names; there is no unclassified dynamically named native/widget field.

## Native wrappers held by rows and callbacks

The current tree can contain three kinds of local BooleanVars: comparison-open,
report-wanted, and report-share. They are reached through `_CheckRow._variable`
and command closures, not a separate app field. Pin these variables before final
tree destruction. `_CheckRow` destroys must retire the row's own trace and clear
the exact `_variable`, `_font`, `_command`, `_label`, and `_icon` references;
perform this for redraw destruction as well as final close. This releases old
screen variables before a later worker can collect dead row/label graphs.

`_Button._command` can close over the UI; clear it at its own destruction.
`_Scrollbar._command` can retain a peer widget; it is not a direct font or
variable owner, but owner-thread collection must settle its dead widget graph.
`_Box.inner`/child `.master` graphs also require collection after app detachment.

The finite pin sequence is part of correctness: take strong local root and
native-wrapper pins first; retire callbacks and destroy normally; detach the
48 fields and exact root backlink; collect dead Python widget graphs while pins
remain strong; release pins naturally on the creating UI thread. Root and asset
pins must remain live across the collection even if no longer app-owned.

Externally retained variables keep their `_tk`, `_root`, value, and peer observer
token. Only the app/row reference and its own token are retired. A peer variable
can intentionally keep its root interpreter alive; no test should mistake that
external ownership for a product resource leak. Arbitrary native objects held
directly by unmodified Tkinter traceback locals also remain outside the claimed
reclamation boundary.

## Fixture-owned mainloop wrapper cycle

Both the retained pass19 proof and the first prepared pass20 extension install
an instance `root.mainloop` wrapper that captures the bound original mainloop.
That creates `root -> wrapper function -> bound original -> root`, independently
of the product. Preserve the old diagnostics unchanged. A new product test
should induce an exception through a class-level wrapper/observer that does not
install a self-retaining instance attribute, or retain and retire the fixture's
exact override after boundary observations. Product code should not clear
arbitrary monkeypatched instance attributes merely to satisfy that fixture.

This inventory is a design/review artifact. No product change or acceptance
result is implied. Root owns the private candidate, original failure proof,
fixed proof, source readback, regression integration, and all runtime gates.
