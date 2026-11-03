# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK accessibility view. All authorization and operations belong to Wizard."""

from __future__ import annotations

from typing import Callable
import os
import subprocess
import sys
import threading
import time
from xml.sax.saxutils import escape as _markup_escape

import gi

os.environ["GTK_MODULES"] = "gail:atk-bridge"
os.environ["NO_AT_BRIDGE"] = "0"
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("Atk", "1.0")
from gi.repository import Atk, Gdk, GLib, Gtk, Pango  # noqa: E402

from beamo_wipe import copy as C  # noqa: E402
from beamo_wipe import diagnostic_report as D, inventory, storage_limits  # noqa: E402
from beamo_wipe.outcomes import may_have_erased  # noqa: E402
from beamo_wipe.recovery import (  # noqa: E402
    recovery_for_blocked,
    recovery_for_diagnostic,
    recovery_for_empty,
    recovery_for_view,
    recovery_for_wizard_error,
)
from beamo_wipe import keyboard as _keyboard  # noqa: E402
from beamo_wipe.keyboard import LAYOUT_ORDER  # noqa: E402
from beamo_wipe.lang import LANGUAGE_NAMES, LANGUAGE_ORDER, LANGUAGE_PICKER_LABEL  # noqa: E402
from beamo_wipe.methods import METHODS  # noqa: E402
from beamo_wipe.models import Screen  # noqa: E402
from beamo_wipe.progress import ProgressAnnouncer  # noqa: E402
from beamo_wipe.diagnostics import emit_serial_marker  # noqa: E402
from beamo_wipe.safety import same_size_conflict  # noqa: E402
from beamo_wipe.ui import StartupDisplayUnavailable  # noqa: E402
from beamo_wipe.wizard import PREPARATION_PATH, Wizard, error_needs_support  # noqa: E402


def _record_image(text: str, scale: int = 4):
    """Gtk.Image of the record code, or None when it cannot be drawn."""
    try:
        gi.require_version("GdkPixbuf", "2.0")
        from gi.repository import GdkPixbuf

        from beamo_wipe.erase_record import qr_matrix

        matrix = qr_matrix(text)
        size = len(matrix) * scale
        rows = []
        for modules in matrix:
            row_bytes = bytearray()
            for dark in modules:
                row_bytes.extend((b"\x00\x00\x00" if dark else b"\xff\xff\xff") * scale)
            rows.append(bytes(row_bytes) * scale)
        data = GLib.Bytes.new(b"".join(rows))
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(
            data, GdkPixbuf.Colorspace.RGB, False, 8, size, size, size * 3
        )
        return Gtk.Image.new_from_pixbuf(pixbuf)
    except Exception:
        return None


def _error_text(wizard: Wizard) -> str:
    """Error severity in words. Shared by render and tick updates so the
    live refresh never drops the label."""
    if not wizard.error:
        return ""
    text = f"{C.SEVERITY_ERROR}: {wizard.error}"
    if error_needs_support(wizard.error):
        text += " " + C.support_text()
    return text


def _widget_text(widget) -> str:
    """The words a focused label or button shows, else ""."""
    if widget is None:
        return ""
    try:
        if isinstance(widget, Gtk.Button):
            return widget.get_label() or ""
        if isinstance(widget, Gtk.Label):
            return widget.get_text() or ""
    except Exception:  # noqa: BLE001 - destroyed or foreign widget
        return ""
    return ""


def _find_by_text(root, text: str):
    """First focusable, sensitive label or button showing exactly ``text``."""
    stack = [root]
    while stack:
        widget = stack.pop(0)
        if (
            widget.get_can_focus()
            and widget.get_sensitive()
            and _widget_text(widget) == text
        ):
            return widget
        if isinstance(widget, Gtk.Container):
            stack.extend(widget.get_children())
    return None


class AccessibleWizard:
    def __init__(self, wizard: Wizard, fullscreen: bool = False):
        self.w = wizard
        self.failed = False
        self.closed = False
        # Retirement must be usable even if the first GTK setup call fails.
        self.window = None
        self.timer = 0
        self._sound_dialog = None
        self.generation = 0
        self._main_loop_level: int | None = None
        try:
            self.window = Gtk.Window(title=C.ACCESSIBLE_TITLE)
            # GtkLabel needs selectable text to accept keyboard focus, but its
            # default select-all-on-focus emits text-selection-changed first.
            # Orca can consume that event and suppress the real focus announcement.
            # Keep manual selection available without selecting text on arrival.
            self.window.get_settings().set_property("gtk-label-select-on-focus", False)
            self.window.set_name("beamo-accessible")
            self._style = Gtk.CssProvider()
            self._apply_type_css()
            # Size before the first show: a low-resolution live session may have
            # no window manager to constrain an oversized default for us.
            width, height = 900, 700
            display = self.window.get_display()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            if monitor is not None:
                workarea = monitor.get_workarea()
                width = min(width, workarea.width)
                height = min(height, workarea.height)
            self.window.set_default_size(width, height)
            if fullscreen:
                # Bare X11 marks fullscreen without a window manager to resize it.
                if monitor is not None:
                    geometry = monitor.get_geometry()
                    self.window.set_default_size(geometry.width, geometry.height)
                    self.window.move(geometry.x, geometry.y)
                self.window.fullscreen()
            self.window.connect("delete-event", self._close)
            self.window.connect("key-press-event", self._key_press)
            self.window.connect("key-release-event", self._key_release)
            self.held: set[int] = set()
            self._release_times: dict[int, int] = {}
            self.primary = None
            self.progress_label = None
            self.progress_bar = None
            self.progress_announcer = ProgressAnnouncer()
            self.walk_away_label = None
            self.finish_reason_label = None
            self.finish_toggle = None
            self._rendered_sound_message = ""
            self.countdown_label = None
            self.error_label = None
            self.shown = None
            self.report_revision = -1
            self.sound_revision = -1
            self.actions: dict[str, Gtk.Button] = {}
            self._refresh_lock = threading.Lock()
            self._refresh_result: tuple[int, object] | None = None
            self.render()
            self.timer = GLib.timeout_add(100, self.tick)
        except BaseException as error:
            self._close_preserving_error(error)
            raise

    def _apply_type_css(self) -> None:
        scale = getattr(self.w, "text_scale", 1.0)
        body = max(12, int(round(16 * scale)))
        heading = max(18, int(round(26 * scale)))
        css = f"""
            #beamo-accessible {{ background: #FFFFFF; color: #12202E; }}
            #beamo-accessible label {{ font-size: {body}px; }}
            #beamo-accessible .screen-heading {{ font-size: {heading}px; font-weight: bold; color: #12202E; }}
            #beamo-accessible .preview-notice {{ background: #E6A817; color: #0A1B34; padding: 8px; }}
            #beamo-accessible .disk-identity {{ background: #F0F5FA; color: #12202E; padding: 16px 20px; border: 1px solid #1C4A73; border-radius: 12px; }}
            #beamo-accessible button {{ padding: 10px 20px; border-radius: 999px; }}
            #beamo-accessible button.primary-action {{ background-image: none; background-color: #1C4A73; color: #FFFFFF; }}
            #beamo-accessible button.primary-action:hover {{ background-color: #163A5C; }}
            #beamo-accessible button.primary-action:active {{ background-color: #102A44; }}
            #beamo-accessible button.destructive-action {{ background-image: none; background-color: #B3261E; color: #FFFFFF; }}
            #beamo-accessible button.destructive-action:hover {{ background-color: #8E1D16; }}
            #beamo-accessible button.destructive-action:active {{ background-color: #6E1510; }}
            #beamo-accessible button:disabled {{ background-image: none; background-color: #E8ECF1; color: #6E7989; }}
            #beamo-accessible button:focus {{ outline: 3px solid #2563EB; outline-offset: 2px; }}
            #beamo-accessible checkbutton {{ padding: 8px 10px; border-radius: 12px; }}
            #beamo-accessible checkbutton:hover {{ background-color: #F4F6F8; }}
            #beamo-accessible checkbutton:checked {{ background-color: #F0F5FA; }}
            #beamo-accessible checkbutton:focus {{ outline: 3px solid #2563EB; outline-offset: 2px; }}
            #beamo-accessible entry {{ padding: 8px 12px; border-radius: 12px; }}
            #beamo-accessible button.utility-action {{ background-image: none; background-color: #FFFFFF; color: #1C4A73; box-shadow: none; }}
            #beamo-accessible button.utility-action:hover {{ background-color: #F0F5FA; }}
            #beamo-accessible button.utility-action:active {{ background-color: #D7E4F2; }}
            #beamo-accessible .erase-warning {{ background: #FBF1D5; color: #7A5200; padding: 12px 16px; border-radius: 12px; }}
            #beamo-accessible .screen-actions {{ border-top: 1px solid #E3E8EE; padding-top: 12px; }}
            #beamo-accessible .report-warning {{ background: #FBF1D5; color: #7A5200; padding: 10px 14px; border-radius: 12px; }}
            #beamo-accessible .report-saved {{ background: #E7F2EB; color: #17703F; padding: 10px 14px; border-radius: 12px; }}
            #beamo-accessible .error-message {{ color: #B3261E; font-weight: bold; }}
        """
        self._style.load_from_data(css.encode())

    def label(self, text: str, *, focusable: bool = False):
        widget = Gtk.Label(label=text)
        widget.set_line_wrap(True)
        widget.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        widget.set_xalign(0)
        widget.set_max_width_chars(70)
        widget.set_can_focus(focusable)
        widget.set_selectable(focusable)
        self.body.pack_start(widget, False, False, 4)
        return widget

    def erase_record(self) -> None:
        """Erase record (#127): heading, code, then the same summary as text.

        The code image is not focusable; its accessible name says the text
        follows. Orca reads the focusable summary label line by line.
        """
        record = self.w.erase_record
        if record is None:
            return
        heading = self.label(C.RECORD_TITLE, focusable=True)
        heading.get_accessible().set_role(Atk.Role.HEADING)
        self.label(C.RECORD_PREVIEW_NOTE if record.preview else C.RECORD_LEAD, focusable=True)
        image = _record_image(record.text)
        if image is None:
            self.label(C.RECORD_NO_CODE)
        else:
            image.set_halign(Gtk.Align.START)
            image.get_accessible().set_name(C.RECORD_CODE_NAME)
            self.body.pack_start(image, False, False, 8)
        self.label(C.RECORD_TEXT_LABEL)
        summary = self.label("\n".join(record.lines), focusable=True)
        summary.get_accessible().set_name(record.text)
        if not record.preview:
            self.label(C.RECORD_NOTE)

    def support_identity_labels(self) -> None:
        ident = self.w.support_identity
        if ident is None:
            return
        self.label(C.support_identity_text(ident), focusable=True)

    def recovery(self, sections) -> None:
        """Screen-reader order: happened, meaning, next, then technical."""
        for label, body in sections.labeled_pairs():
            heading = self.label(label, focusable=True)
            heading.get_accessible().set_role(Atk.Role.HEADING)
            heading.get_style_context().add_class("recovery-heading")
            self.label(body, focusable=True)
        if sections.technical:
            self.technical(sections.technical)

    def technical(self, text: str) -> None:
        """Technical details stay behind an expander, read on demand."""
        from beamo_wipe import recovery as Rec

        expander = Gtk.Expander.new(Rec.RECOVERY_TECHNICAL)
        reader = Gtk.Label(label=text)
        reader.set_line_wrap(True)
        reader.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        reader.set_max_width_chars(65)
        reader.set_selectable(True)
        reader.set_can_focus(True)
        expander.add(reader)
        self.body.pack_start(expander, False, False, 4)

    def button(self, text: str, action: Callable, *, enabled: bool = True,
               utility: bool = False, in_body: bool = False):
        widget = Gtk.Button.new_with_label(text)
        widget.set_sensitive(enabled)
        widget.set_can_default(False)
        widget.set_receives_default(False)
        widget.get_child().set_line_wrap(True)
        # Footer actions contain short words. Character wrapping would reduce
        # their minimum width to one glyph and inflate GTK's height request.
        widget.get_child().set_line_wrap_mode(
            Pango.WrapMode.WORD_CHAR if in_body else Pango.WrapMode.WORD
        )
        widget.get_child().set_max_width_chars(65 if in_body else 24)
        context = widget.get_style_context()
        if text in {C.BTN_ERASE, C.SHUTDOWN_DISCARD}:
            context.add_class("destructive-action")
        elif text in C.PRIMARY_ACTION_LABELS or text in {C.SHUTDOWN_KEEP, C.BTN_SAVE_REPORT}:
            context.add_class("primary-action")
        elif utility:
            context.add_class("utility-action")
        generation = self.generation

        def clicked(_button):
            # A queued AT-SPI or key action from a replaced screen is stale.
            if self.closed or generation != self.generation or not widget.get_sensitive():
                return
            getattr(self.w, "acknowledge_finish_sound", lambda: None)()  # someone is back (#133)
            action()
            if self.w.wants_shutdown or self.w.wants_new_session:
                self.close()
            else:
                self.render()

        widget.connect("clicked", clicked)
        if in_body:
            self.body.pack_start(widget, False, False, 3)
        elif utility:
            self.utilities.attach(widget, self._utility_count % 3, self._utility_count // 3, 1, 1)
            self._utility_count += 1
        elif text == C.BTN_BACK:
            self.navigation.pack_start(widget, False, False, 0)
            self.navigation.reorder_child(widget, 0)
        else:
            self.navigation.pack_end(widget, False, False, 0)
        self.actions[text] = widget
        return widget

    def _style_tree(self, widget):
        # Widget-scoped providers cannot recolor other apps or later windows.
        widget.get_style_context().add_provider(self._style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        if isinstance(widget, Gtk.Container):
            for child in widget.get_children():
                self._style_tree(child)

    def identity(self, *, token: bool = False):
        disk = self.w.operation_disk
        if disk is not None:
            view = self.w.disk_view(disk)
            marked = token and view.token_end > view.token_start
            # On Confirm the identity is focusable and selectable, so Orca can
            # read the serial or hardware ID character by character (#129).
            widget = self.label(view.announcement, focusable=marked)
            widget.get_style_context().add_class("disk-identity")
            if marked:
                self._mark_token(widget, view)
        elif self.w.operation_identity_text:
            self.label(self.w.operation_identity_text).get_style_context().add_class(
                "disk-identity"
            )

    def _mark_token(self, widget, view) -> None:
        """Underline the confirmation characters inside the identity text.

        The label's text (what AT-SPI and Orca read) is unchanged; Pango
        markup underlines, bolds and tints the ending of the identifier, so
        the mark is not colour alone.
        """
        text = view.announcement
        field = f"{view.id_label}: {view.id_value}"
        at = text.find(field)
        if at < 0:
            return
        start = at + len(view.id_label) + 2 + view.token_start
        end = at + len(view.id_label) + 2 + view.token_end
        esc = GLib.markup_escape_text
        widget.set_markup(
            esc(text[:start])
            + '<span underline="double" weight="bold" background="#FFF3C4">'
            + esc(text[start:end])
            + "</span>"
            + esc(text[end:])
        )

    def reader(self, text: str):
        view = Gtk.TextView()
        view.set_editable(False)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        view.get_buffer().set_text(text)
        view.get_accessible().set_name(text)
        view.set_can_focus(True)
        scroll = Gtk.ScrolledWindow()
        # A TextView can initially request the width of its longest paragraph
        # even with wrapping enabled. NEVER propagates that request through
        # the outer viewport and widens the window (Advanced exceeded 800px).
        # AUTOMATIC constrains the reader; normal text still wraps in place.
        scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroll.set_min_content_height(180)
        scroll.add(view)
        self.body.pack_start(scroll, False, False, 4)
        return view

    def render(self):
        if getattr(self, "closed", False):
            return
        self._live_sound_dialog()
        first_review_frame = (
            self.w.screen == Screen.LAST_CHANCE and self.shown != Screen.LAST_CHANCE
        )
        self.generation += 1
        # Orca reads the window title; follow a language change.
        if self.window.get_title() != C.ACCESSIBLE_TITLE:
            self.window.set_title(C.ACCESSIBLE_TITLE)
        self._apply_type_css()
        self.actions = {}
        self.primary = self.progress_label = self.countdown_label = None
        self.progress_bar = None
        self.progress_announcer = ProgressAnnouncer()
        self.walk_away_label = None
        self.finish_reason_label = None
        self.finish_toggle = None
        self._rendered_sound_message = self.w.sound_message
        self.power_label = None
        # A Done re-render (live report-USB status, #135) keeps Orca where
        # it was; from inside the report panel it moves to the new status.
        refocus_text, refocus_panel = "", False
        if getattr(self, "shown", None) == Screen.DONE == self.w.screen:
            focused = self.window.get_focus()
            refocus_text = _widget_text(focused)
            refocus_panel = focused is not None and focused in getattr(self, "_panel_widgets", ())
        self._panel_widgets: list = []
        self._panel_status = None
        self.shown = self.w.screen
        self.report_revision = self.w.report_view.revision
        self.sound_revision = getattr(self.w, "sound_revision", 0)
        old = self.window.get_child()
        if old:
            self.window.remove(old)
            old.destroy()
        shell = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        shell.set_border_width(16)
        self.window.add(shell)
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        shell.pack_start(scroll, True, True, 0)
        self.body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scroll.add(self.body)
        self.footer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.footer.get_style_context().add_class("screen-actions")
        shell.pack_start(self.footer, False, False, 0)
        # Utilities wrap independently of navigation. Keep the action footer
        # outside the scrolling body without six full-width button rows at
        # 800x600. No fixed content height or minimum window size is imposed.
        self.utilities = Gtk.Grid()
        self.utilities.set_column_homogeneous(True)
        self.utilities.set_column_spacing(6)
        self.utilities.set_row_spacing(4)
        # Grouping names must not rewrite action or result heading ATK names.
        self.utilities.get_accessible().set_role(Atk.Role.PANEL)
        self.utilities.get_accessible().set_name(C.ASSIST_LABEL)
        self._utility_count = 0
        self.footer.pack_start(self.utilities, False, False, 0)
        self.navigation = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.navigation.get_accessible().set_role(Atk.Role.PANEL)
        self.navigation.get_accessible().set_name(C.NAV_LABEL)
        self.footer.pack_start(self.navigation, False, False, 4)
        if self.w.preview:
            self.label(C.PREVIEW_BANNER).get_style_context().add_class("preview-notice")
        screen = self.w.screen
        generation = self.generation
        heading = self.label("Beamo Wipe", focusable=True)
        heading.get_style_context().add_class("screen-heading")
        arrival = heading
        if screen == Screen.SPLASH:
            heading.set_text(C.SPLASH_TAGLINE)
            # The header's stages, from the same source (#138).
            self.label(C.splash_roadmap(PREPARATION_PATH), focusable=True)
            self.button(C.primary_action(Screen.SPLASH), self.w.skip_splash)
        elif screen == Screen.KEYBOARD:
            heading.set_text(C.TITLE_KEYBOARD)
            # #131: language is the first control, each in its own name, so
            # Orca users reach it before the rest of the instructions.
            self.label(LANGUAGE_PICKER_LABEL)
            chosen_language = None
            for code in LANGUAGE_ORDER:
                state = C.ACCESSIBLE_SELECTED if self.w.language == code else C.ACCESSIBLE_NOT_SELECTED
                language_button = self.button(
                    f"{LANGUAGE_NAMES[code]} ({state})",
                    lambda lang_code=code: self.w.choose_language(lang_code),
                    in_body=True,
                )
                if self.w.language == code:
                    chosen_language = language_button
            self.label(C.LANGUAGE_LEAD)
            # #139: language, then text size, then the keyboard; each part
            # starts with a heading Orca can jump to.
            size_heading = self.label(C.TEXT_SIZE_UTILITY, focusable=True)
            size_heading.get_accessible().set_role(Atk.Role.HEADING)
            self.label(C.TEXT_SIZE_LEAD)
            for size_id, label in C.TEXT_SIZE_LABELS.items():
                state = C.ACCESSIBLE_SELECTED if self.w.text_size == size_id else C.ACCESSIBLE_NOT_SELECTED
                self.button(
                    f"{label} ({state})",
                    lambda sid=size_id: self.w.set_text_size(sid),
                    in_body=True,
                )
            keyboard_heading = self.label(C.KEYBOARD_LEAD, focusable=True)
            keyboard_heading.get_accessible().set_role(Atk.Role.HEADING)
            notice = C.keyboard_layout_notice(self.w)
            if notice:
                self.label(notice)
            for index, layout_id in enumerate(LAYOUT_ORDER, 1):
                spec = _keyboard.LAYOUTS[layout_id]
                state = C.ACCESSIBLE_SELECTED if self.w.keyboard_layout == layout_id else C.ACCESSIBLE_NOT_SELECTED
                self.button(
                    f"{index} {spec.title} ({state})",
                    lambda lid=layout_id: self.w.set_keyboard_layout(lid),
                    in_body=True,
                )
                self.label(spec.note)
            # #141: layout fine print behind Show more (an expander).
            limits = Gtk.Expander.new(C.BTN_MORE)
            limits.set_expanded(False)
            limits_text = Gtk.Label(label=C.KEYBOARD_LIMITS)
            limits_text.set_line_wrap(True)
            limits_text.set_xalign(0)
            limits_text.set_max_width_chars(70)
            limits_text.set_can_focus(True)
            limits_text.set_selectable(True)
            limits.add(limits_text)
            self.body.pack_start(limits, False, False, 4)
            if self.w.error:
                sections = recovery_for_wizard_error(self.w.error)
                if sections:
                    self.recovery(sections)
                else:
                    self.label(f"{C.SEVERITY_ERROR}: {self.w.error}")
            elif self.w.keyboard_message:
                self.label(f"{C.SEVERITY_WARNING}: {self.w.keyboard_message}")
            self.label(C.KEYBOARD_CHECK_LABEL)
            entry = Gtk.Entry()
            entry.set_visibility(True)
            purpose = getattr(Gtk, "InputPurpose", None)
            if purpose is not None:
                entry.set_input_purpose(purpose.FREE_FORM)
            entry.set_text(self.w.typing_check)
            entry.set_placeholder_text(C.KEYBOARD_CHECK_HINT)
            generation = self.generation
            entry.connect(
                "changed",
                lambda widget: self._typing(widget.get_text(), generation),
            )
            self.body.pack_start(entry, False, False, 4)
            # Guided check (#140): Orca reads the prompt as the box's name;
            # a result is an alert label that takes focus so it is spoken.
            entry.get_accessible().set_name(C.KEYBOARD_CHECK_LABEL)
            entry.connect(
                "key-press-event",
                lambda _widget, event: self._keyboard_check_key(event, generation),
            )
            arrival = chosen_language or entry
            result = self.w.keyboard_check_text
            if result:
                result_label = self.label(result, focusable=True)
                result_label.get_accessible().set_role(Atk.Role.ALERT)
                if getattr(self, "_check_fresh", False):
                    arrival = result_label
                switch = self.w.keyboard_check_switch
                if switch:
                    self.button(switch, self.w.accept_keyboard_suggestion, in_body=True)
            self._check_fresh = False
            self.button(C.primary_action(Screen.KEYBOARD), self.w.accept_keyboard)
        elif screen in (Screen.WHAT, Screen.OWNER):
            heading.set_text(C.TITLE_OWNER)
            self.label(C.WHAT_LEAD)
            self.label(C.TITLE_WHAT)
            self.label("\n".join(C.WHAT_BULLETS))
            self.label(C.this_usb_line())
            self.label(C.REPORT_MEDIA_WHAT, focusable=True)
            self.label(C.POWER_REMINDER)
            self.label(C.POWER_BLANKING)
            self.label(C.POWER_EVENTS, focusable=True)
            self.support_identity_labels()
            self.label(C.OWNER_LEAD)
            check = Gtk.CheckButton.new_with_label(C.OWNER_CHECKBOX)
            check.get_child().set_line_wrap(True)
            check.get_child().set_max_width_chars(65)
            check.set_active(self.w.owner_ok)
            self.body.pack_start(check, False, False, 4)
            self.primary = self.button(
                C.primary_action(Screen.OWNER), self.w.continue_owner, enabled=self.w.owner_ok
            )
            check.connect(
                "toggled", lambda widget: self._owner(widget.get_active(), generation)
            )
        elif screen == Screen.PICK:
            heading.set_text(C.TITLE_PICK)
            self.label(C.pick_subtitle())
            self.button(C.DISK_HELP_BUTTON, self.w.open_disk_help, in_body=True)
            if same_size_conflict(self.w.listed_disks):
                self.label(f"{C.SEVERITY_WARNING}: {C.SAME_SIZE_HINT}")
            if self.w.error:
                sections = recovery_for_wizard_error(self.w.error)
                if sections:
                    self.recovery(sections)
                else:
                    self.label(f"{C.SEVERITY_ERROR}: {self.w.error}")
            if self.w.report_wanted:
                self.label(C.REPORT_MEDIA_WANTED, focusable=True)
            self._inventory_count()
            self._protected_boot()
            for disk in sorted(self.w.selectable, key=lambda d: d.path):
                text = C.ACCESSIBLE_SELECT_DISK.format(disk=self.w.disk_view(disk).announcement)
                select = self.button(text, lambda path=disk.path: self._select(path), in_body=True)
                hint = C.contents_hint(disk)
                if hint:
                    # Factual contents line: shown under the row and spoken
                    # with it, so Orca users hear what sighted owners see.
                    select.get_accessible().set_name(f"{text}. {hint}")
                    self.label(hint)
                nested = inventory.card_nesting_text(self.w.nested_components(disk))
                if nested:
                    self.label(nested, focusable=True)
            if len(self.w.selectable) > 1:
                expander = Gtk.Expander.new(inventory.COMPARE_TITLE)
                reader = Gtk.Label(label=inventory.comparison_text(self.w.selectable, peers=self.w.listed_disks))
                reader.set_line_wrap(True)
                reader.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
                reader.set_max_width_chars(65)
                reader.set_selectable(True)
                reader.set_can_focus(True)
                expander.add(reader)
                self.body.pack_start(expander, False, False, 4)
            self._inventory()
        elif screen in (Screen.PICK_EMPTY, Screen.PICK_BLOCKED):
            heading.set_text(
                C.TITLE_EMPTY if screen == Screen.PICK_EMPTY else C.blocked_title(self.w.error, recovered=self.w._recovered)
            )
            self._inventory_count()
            if screen == Screen.PICK_EMPTY:
                self.recovery(recovery_for_empty())
                self.label(C.support_text(), focusable=True)
                self._protected_boot()
            else:
                self.recovery(
                    recovery_for_blocked(self.w.error, recovered=self.w._recovered)
                )
            self.support_identity_labels()
            self._inventory()
            self.button(C.BTN_SHUTDOWN, self.w.shutdown)
        elif screen == Screen.CONFIRM:
            heading.set_text(C.TITLE_CONFIRM)
            self.identity(token=True)
            arrival = self.label(f"{C.SEVERITY_WARNING}: {self.w.warning_text()}", focusable=True)
            arrival.get_style_context().add_class("erase-warning")
            arrival.get_accessible().set_role(Atk.Role.ALERT)
            self.label(C.CONFIRM_KEYBOARD_LINE.format(
                layout=_keyboard.LAYOUTS[self.w.keyboard_layout].title,
                language=LANGUAGE_NAMES[self.w.language],
            ))
            prompt = C.confirm_prompt(self.w.confirm) if self.w.confirm else C.ACCESSIBLE_NO_TARGET
            self.label(prompt)
            entry = Gtk.Entry()
            entry.get_accessible().set_name(prompt)
            entry.set_text(self.w.confirm_input)
            self.body.pack_start(entry, False, False, 4)
            self.primary = self.button(
                C.primary_action(Screen.CONFIRM), self.w.continue_confirm, enabled=self.w.token_ok
            )
            entry.connect(
                "changed", lambda widget: self._token(widget.get_text(), generation)
            )
        elif screen == Screen.METHOD:
            heading.set_text(C.TITLE_METHOD)
            self.identity()
            group = None
            guides = []
            for method, spec in METHODS.items():
                card = C.METHOD_CARDS[method]
                # Keep the radio ATK name as the method summary. Plain lead
                # and everyday limits stay off the radio so 800x600 choices
                # remain above the footer (same pattern as #51 headings).
                label = spec.summary
                if card["mark"]:
                    label = f"{label} [{card['mark']}]"
                if card["extra"]:
                    label = f"{label} {card['extra']}"
                choice = Gtk.RadioButton.new_with_label_from_widget(group, label)
                choice.get_child().set_line_wrap(True)
                choice.get_child().set_max_width_chars(65)
                group = choice
                choice.set_active(self.w.method == method)
                # Orca reads the rough duration with its choice. The visible
                # copy follows the choices so 800x600 keeps all three above
                # the footer; the name still starts with the visible label.
                guide = C.method_time_guide(method, self.w.selected)
                if guide:
                    choice.get_accessible().set_name(f"{label} {guide}")
                    guides.append(f"{spec.title}: {guide}")
                if spec.plain_lead:
                    choice.get_accessible().set_description(spec.plain_lead)
                self.body.pack_start(choice, False, False, 3)
                choice.connect(
                    "toggled",
                    lambda widget, mid=method: self.w.set_method(mid)
                    if widget.get_active() and generation == self.generation
                    else None,
                )
            # The general storage limits follow the choices (the next Tab
            # stop after them): above the radios this notice pushed the third
            # choice under the footer at 800x600 for hard disks and German.
            self.label(f"{C.SEVERITY_LIMITS}: {self.w.storage_notice}", focusable=True)
            for text in guides:
                self.label(text)
            for spec in METHODS.values():
                self.label(spec.plain_lead)
            for spec_method in METHODS:
                note = str(C.METHOD_CARDS[spec_method]["limits"] or "")
                if note:
                    self.label(note, focusable=True)
            self.button(storage_limits.BUTTON, self.w.open_limits, utility=True)
            self.button(C.BTN_ADVANCED, self.w.open_advanced, utility=True)
            self.button(C.primary_action(Screen.METHOD), self.w.continue_method)
        elif screen == Screen.DISK_HELP:
            heading.set_text(C.DISK_HELP_TITLE)
            self.reader(C.DISK_HELP_TEXT)
            self.button(C.DISK_HELP_STOP, self.w.shutdown)
        elif screen == Screen.REPORT_HELP:
            heading.set_text(C.REPORT_HELP_TITLE)
            reader = self.reader(
                C.REPORT_HELP_TEXT
                + (
                    "\n\n" + self.w.report_recovery_warning
                    if self.w.report_recovery_warning
                    else ""
                )
            )

            def set_preference(widget):
                if generation != self.generation:
                    return
                self.w.set_report_wanted(widget.get_active())
                content = C.REPORT_HELP_TEXT + (
                    "\n\n" + self.w.report_recovery_warning
                    if self.w.report_recovery_warning
                    else ""
                )
                reader.get_buffer().set_text(content)
                reader.get_accessible().set_name(content)

            choice = Gtk.CheckButton.new_with_label(C.REPORT_WANTED)
            choice.get_child().set_line_wrap(True)
            choice.get_child().set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            choice.get_child().set_max_width_chars(65)
            choice.set_active(self.w.report_wanted)
            choice.connect(
                "toggled",
                set_preference,
            )
            self.body.pack_start(choice, False, False, 4)
            share = Gtk.CheckButton.new_with_label(C.REPORT_SHARE_REDACTED)
            share.get_child().set_line_wrap(True)
            share.get_child().set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            share.get_child().set_max_width_chars(65)
            share.set_active(self.w.report_share_redacted)
            share.connect(
                "toggled",
                lambda widget: self.w.set_report_share_redacted(widget.get_active())
                if generation == self.generation
                else None,
            )
            self.body.pack_start(share, False, False, 4)
        elif screen == Screen.LIMITS:
            heading.set_text(storage_limits.TITLE)
            self.reader(storage_limits.full_text())
        elif screen == Screen.ADVANCED:
            heading.set_text(C.TITLE_ADVANCED)
            self.reader(C.ADVANCED_LEAD + "\n" + C.ADVANCED_LOG_NOTE)
        elif screen == Screen.LAST_CHANCE:
            heading.set_text(C.TITLE_LAST)
            self.label(C.LAST_LEAD)
            self.identity()
            self.label(self.w.operation_summary)
            # Orca reads a label's actual text, even when its accessible name
            # differs. Focus the full warning notice so arrival still speaks
            # the destructive consequence, without an oversized heading.
            arrival = self.label(f"{C.SEVERITY_WARNING}: {self.w.erase_label()}", focusable=True)
            arrival.get_style_context().add_class("erase-warning")
            arrival.get_accessible().set_role(Atk.Role.ALERT)
            self.label(self.w.method_summary)
            if self.w.error:
                sections = recovery_for_wizard_error(self.w.error)
                if sections:
                    self.recovery(sections)
                else:
                    self.label(f"{C.SEVERITY_ERROR}: {self.w.error}", focusable=True)
            self.support_identity_labels()
            self.countdown_label = self.label("")
            self.primary = self.button(
                C.BTN_ERASE, self.w.begin_erase, enabled=self.w.erase_enabled
            )
        elif screen == Screen.CHECKING:
            heading.set_text(C.BUSY_CHECKING_TITLE)
            self.identity()
            self.label(C.BUSY_CHECKING_MESSAGE)
        elif screen == Screen.STOPPING:
            heading.set_text(C.BUSY_STOPPING_TITLE)
            self.identity()
            self.label(self.w.operation_method_text)
            self.label(C.STOPPING_TEXT)
            self.progress_label = self.label("")
        elif screen == Screen.WORKING:
            heading.set_text(C.VIEWS["stop_unconfirmed"].message
                             if self.w.error == C.VIEWS["stop_unconfirmed"].announcement
                             else C.WORKING_PULSE)
            self.identity()
            self.label(self.w.method_summary)
            # Glance (#132): percentage, time line, current step. Focusable
            # so Tab reads it; its text changes at the announcer's pace, not
            # on every poll. The bar's value moves at the same pace, so
            # Orca's own progress-bar speech cannot run every tick either.
            self.progress_label = self.label("", focusable=True)
            self.progress_bar = Gtk.ProgressBar()
            self.progress_bar.get_accessible().set_name(C.ERASE_PROGRESS_LABEL)
            self.body.pack_start(self.progress_bar, False, False, 4)
            # Walk away (#133): the beep is promised only when it can play.
            # The laptop power/lid advice follows at the end of this screen.
            self.walk_away_label = self.label(self.w.walk_away_text, focusable=True)
            self.finish_reason_label = self.label(self.w.finish_sound_reason)
            self.finish_reason_label.set_no_show_all(True)
            finish = Gtk.CheckButton.new_with_label(C.FINISH_SOUND_TOGGLE)
            finish.get_child().set_line_wrap(True)
            finish.get_child().set_max_width_chars(65)
            self.body.pack_start(finish, False, False, 4)
            self.finish_toggle = finish
            self._sync_finish_sound()
            finish.connect(
                "toggled",
                lambda widget: self._finish_toggled(widget, generation),
            )
            if self.w.error:
                sections = recovery_for_wizard_error(self.w.error)
                if sections:
                    self.recovery(sections)
            if self.w.evidence_warning:
                self.label(f"{C.SEVERITY_WARNING}: {self.w.evidence_warning}")
            if self.w.stop_confirmation is not None:
                confirmation = self.w.stop_confirmation
                heading.set_text(C.STOP_TITLE)
                arrival = self.label(f"{C.SEVERITY_WARNING}: {C.STOP_LEAD}", focusable=True)
                arrival.get_style_context().add_class("erase-warning")
                arrival.get_accessible().set_role(Atk.Role.ALERT)
                self.button(C.STOP_KEEP, self.w.keep_erasing)
                self.button(C.STOP_CONFIRM, lambda: self.w.confirm_stop(confirmation))
            else:
                self.button(C.STOP_ASK, self.w.request_stop)
        elif screen == Screen.DONE:
            self.w.request_auto_outcome_sound()
            result = self.w.result_view
            plain = self.w.result_plain
            sections = recovery_for_view(result)
            # The plain headline is the heading (#134). A preview keeps its
            # one-sentence announcement; finished outcomes read their note
            # and What next list as the labels that follow.
            heading.set_text(
                plain.headline if sections or plain.checklist else result.announcement
            )
            heading.get_accessible().set_role(Atk.Role.HEADING)
            icon = Gtk.Image.new_from_icon_name(
                {
                    "check": "emblem-ok-symbolic",
                    "warn": "dialog-warning-symbolic",
                    "danger": "dialog-error-symbolic",
                    "info": "dialog-information-symbolic",
                }[result.icon],
                Gtk.IconSize.DIALOG,
            )
            icon.get_accessible().set_name(plain.headline)
            css = Gtk.CssProvider()
            color = {
                "ok": "#17703F",
                "warn": "#7A5200",
                "danger": "#B3261E",
                "info": "#1C4A73",
            }[result.tone]
            css.load_from_data(f"image {{ color: {color}; }}".encode())
            icon.get_style_context().add_provider(
                css, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self.body.pack_start(icon, False, False, 0)
            heading.get_accessible().set_description(
                f"Result: {result.code}. Status: {result.tone}."
            )
            self.identity()
            self.label(self.w.method_summary)
            self.label(self.w.elapsed_text)
            panel = self.w.report_panel
            if panel.kind == "evidence":
                # Ref #153: the evidence failure and Retry come first.
                self.report_panel(panel)
            if sections:
                self.recovery(sections)
            elif plain.checklist:
                from beamo_wipe import outcomes as O

                self.label(plain.note, focusable=True)
                next_heading = self.label(O.WHAT_NEXT, focusable=True)
                next_heading.get_accessible().set_role(Atk.Role.HEADING)
                for item in plain.numbered:
                    self.label(item, focusable=True)
            else:
                self.label(self.w.result_view.next_step)
            if self.w.done_support_needed:
                self.label(C.support_text(), focusable=True)
            self.support_identity_labels()
            if plain.checklist:
                # Support wording: the exact status message and result code.
                self.technical(self.w.result_technical)
            elif may_have_erased(result.code):
                self.label(C.POST_ERASE_BOOT)
            for alert in self.w.check_alerts:
                self.label(f"{C.SEVERITY_WARNING}: {alert}")
            report = self.w.report_view
            if panel.kind != "evidence":
                self.report_panel(panel)
            self.erase_record()
            # Two final actions (#135). Report controls are in the panel;
            # the Sound check utility below holds the sound settings.
            if self.w.preview:
                self.button(C.BTN_RUN_AGAIN, self.w.reset_for_preview)
            else:
                reason = self.w.done_actions_reason
                self.label(reason or C.ANOTHER_HINT, focusable=bool(reason))
                self.button(C.BTN_ERASE_ANOTHER, self.w.erase_another_disk,
                            enabled=self.w.can_erase_another)
            self.button(
                C.BTN_CLOSE_PREVIEW if self.w.preview else C.BTN_SHUTDOWN, self.w.shutdown,
                enabled=not report.exporting and not report.saving_evidence,
            )
        elif screen == Screen.REFRESH_CONFIRM:
            heading.set_text(C.TITLE_REFRESH)
            if self.w.refresh_guarded:
                # #136: Cancel comes first and is the safe choice; Enter on
                # the arrival heading does nothing, F5 cannot accept.
                self.label(C.REFRESH_GUARD_LEAD, focusable=True)
                self.label(C.HINT_REFRESH_GUARD, focusable=True)
                self.button(C.BTN_REFRESH_CANCEL, self.w.back)
                self.button(C.BTN_REFRESH, self._begin_refresh_scan)
            else:
                self.label(C.REFRESH_LEAD, focusable=True)
                self.button(C.BTN_REFRESH, self._begin_refresh_scan)
                self.button(C.BTN_BACK, self.w.back)
        elif screen == Screen.SHUTDOWN_CONFIRM:
            heading.set_text(self.w.exit_confirmation_title)
            self.label(self.w.exit_confirmation_loss)
            self.label(C.SHUTDOWN_HINT)
            if self.w.report_recovery_warning:
                self.label(self.w.report_recovery_warning)
            self.label(C.MEDIA_STEPS_TITLE, focusable=True)
            self.label(self.w.exit_media_steps, focusable=True)
            self.button(C.SHUTDOWN_KEEP, self.w.keep_report_session)
            generation = self.w.shutdown_generation
            self.button(
                self.w.exit_confirmation_discard,
                lambda: self.w.confirm_shutdown_without_saving(generation),
            )
        elif screen == Screen.DIAGNOSTIC:
            view = self.w.diagnostic_view
            heading.set_text(D.report_title(self.w.startup_error_code))
            self.recovery(
                recovery_for_diagnostic(
                    self.w.startup_error_code,
                    view.message,
                    self.w.diagnostic_step,
                )
            )
            self.support_identity_labels()
            self.button(
                C.SAVE_DIAGNOSTIC_REPORT if view.ready else C.BTN_PREPARE,
                lambda: self.w.diagnostic_action(background=True),
                enabled=not view.busy,
            )
            self.button(C.BTN_BACK, self.w.close_diagnostic, enabled=not view.busy)
            self.button(C.BTN_SHUTDOWN, self.w.shutdown, enabled=not view.busy)
        elif screen == Screen.REFRESHING:
            heading.set_text(
                C.ACCESSIBLE_REFRESHED
            )
        else:
            heading.set_text(
                C.ACCESSIBLE_UNCONFIRMED
            )
            self.label(C.support_text(), focusable=True)
        self.error_label = self.label(_error_text(self.w), focusable=True)
        self.error_label.get_style_context().add_class("error-message")
        if self.w.error:
            self.error_label.get_accessible().set_role(Atk.Role.ALERT)
        if screen not in {
            Screen.CHECKING,
            Screen.STOPPING,
            Screen.REFRESHING,
            Screen.SHUTDOWN_CONFIRM,
        }:
            self.button(C.SOUND_CHECK_BUTTON, self.open_sound_check, utility=True)
        if self.w.can_open_diagnostic:
            self.button(C.DIAGNOSTIC_TITLE, self.w.open_diagnostic, utility=True)
        if self.w.can_open_report_help:
            self.button(C.REPORT_HELP_TITLE, self.w.open_report_help, utility=True)
        if self.w.refresh_offered:
            # #136: not on What/Owner; guarded from Confirm, Method, Review.
            self.button(C.BTN_REFRESH_UTILITY, self.w.open_refresh_confirm, utility=True)
        if self.w.can_open_keyboard and screen != Screen.KEYBOARD:
            self.button(C.KEYBOARD_UTILITY, self.w.open_keyboard, utility=True)
        if screen not in {
            Screen.SPLASH, Screen.KEYBOARD, Screen.WORKING, Screen.STOPPING,
            Screen.CHECKING, Screen.REFRESHING, Screen.DONE, Screen.SHUTDOWN_CONFIRM,
            Screen.METHOD, Screen.LAST_CHANCE, Screen.ADVANCED, Screen.LIMITS,
            Screen.DISK_HELP, Screen.REPORT_HELP,
        }:
            self.button(
                f"{C.TEXT_SIZE_UTILITY}: {C.TEXT_SIZE_LABELS.get(self.w.text_size, C.TEXT_SIZE_STANDARD)}",
                self.w.cycle_text_size,
                utility=True,
            )
        if screen in {
            Screen.WHAT,
            Screen.OWNER,
            Screen.PICK,
            Screen.PICK_EMPTY,
            Screen.PICK_BLOCKED,
            Screen.CONFIRM,
            Screen.METHOD,
            Screen.LAST_CHANCE,
            Screen.LIMITS,
            Screen.REPORT_HELP,
            Screen.DISK_HELP,
            Screen.ADVANCED,
        } or (screen == Screen.KEYBOARD and self.w._keyboard_from):
            self.button(C.BTN_BACK, self.w.back)
        if screen in {Screen.WHAT, Screen.OWNER, Screen.LAST_CHANCE, Screen.CHECKING, Screen.WORKING, Screen.STOPPING}:
            if screen not in {Screen.WHAT, Screen.OWNER}:
                self.label(C.POWER_KEEP)
            self.power_label = self.label(self.w.power_text, focusable=True)
        self._style_tree(self.window)
        self.window.show_all()
        if not self.utilities.get_children():
            self.footer.remove(self.utilities)
            self.utilities.destroy()
        self.arrival = arrival
        if self._focus_active_window() is self.window:
            target = _find_by_text(self.window, refocus_text) if refocus_text else None
            if target is None and refocus_panel:
                target = self._panel_status
            (target or arrival).grab_focus()
        if first_review_frame:
            # Building and showing the first review may consume its original
            # timer. Give Orca users the full five seconds after arrival.
            self.w.restart_review_countdown()
        self.update_status()
        # Stage and step are the ATK description, not a prefix on the heading
        # name: "Preparation, step 3 of 6: Choose a disk." (#130). Result and
        # busy screens keep the canonical stage announcement exactly;
        # "Result. Erase completed…" hid that title from heading names.
        spoken_stage = C.journey_step_announcement(self.w)
        if spoken_stage:
            heading.get_accessible().set_description(spoken_stage)
        emit_serial_marker(f"BEAMO_WIPE_ACCESSIBLE_SCREEN_{screen.name}")

    def _protected_boot(self):
        if self.w.protected_boot_text:
            self.reader(self.w.protected_boot_text)

    def _inventory_count(self):
        text = self.w.inventory_count_announcement
        widget = self.label(text, focusable=True)
        widget.get_accessible().set_name(text)
        return widget

    def _inventory(self):
        if self.w.other_devices:
            self.label(inventory.TITLE)
            self.reader(inventory.full_text(self.w.other_devices))

    def report_panel(self, panel) -> None:
        """Save a report (#135): heading, state, numbered steps, controls.

        Steps are focusable so Orca reads them in order; a greyed control is
        followed by its reason.
        """
        widgets = self._panel_widgets
        heading = self.label(C.REPORT_STATUS_TITLE, focusable=True)
        heading.get_accessible().set_role(Atk.Role.HEADING)
        heading.get_style_context().add_class("screen-heading")
        widgets.append(heading)
        if panel.kind == "preview":
            widgets.append(self.label(panel.headline, focusable=True))
            return
        if panel.tone == "ok":
            summary = self.label(f"{C.SEVERITY_SAVED}: {panel.headline}", focusable=True)
            summary.get_style_context().add_class("report-saved")
        elif panel.tone == "warn":
            summary = self.label(f"{C.SEVERITY_WARNING}: {panel.headline}", focusable=True)
            summary.get_style_context().add_class("report-warning")
            summary.get_accessible().set_role(Atk.Role.ALERT)
        else:
            summary = self.label(panel.headline, focusable=True)
        widgets.append(summary)
        self._panel_status = summary
        if panel.detail:
            prefix = f"{C.SEVERITY_WARNING}: " if panel.kind == "evidence" else ""
            widgets.append(self.label(prefix + panel.detail, focusable=True))
        for index, line in enumerate(panel.step_lines):
            step = self.label(line, focusable=True)
            widgets.append(step)
            if index == 1 and panel.kind in ("ready", "failed"):
                # The live USB line: where Orca lands when it changes.
                self._panel_status = step
        if panel.show_retry:
            widgets.append(self.button(C.RETRY_SAVE, self.w.begin_evidence_retry,
                                       enabled=panel.retry_enabled, in_body=True))
            if not panel.retry_enabled:
                widgets.append(self.label(panel.retry_reason, focusable=True))
        if panel.show_save:
            widgets.append(self.button(C.BTN_SAVE_REPORT, self.w.begin_report_export,
                                       enabled=panel.save_enabled, in_body=True))
            if not panel.save_enabled:
                widgets.append(self.label(panel.save_reason, focusable=True))
        if panel.notice:
            self.label(panel.notice)

    def open_sound_check(self):
        from beamo_wipe.ui.sound_dialog import SoundDialog

        if self._live_sound_dialog() is not None:
            self._focus_active_window()
            return
        self._sound_dialog = SoundDialog(Gtk, self.window, self.w, on_stop=self.render)
        self._sound_dialog.dialog.connect("destroy", self._sound_closed)
        self._sound_dialog.dialog.connect("key-press-event", self._modal_key_press)
        self._sound_dialog.dialog.connect("key-release-event", self._key_release)
        self._focus_active_window()

    def _live_sound_dialog(self):
        controller = getattr(self, "_sound_dialog", None)
        if controller is None or controller.dialog is None:
            return None
        if controller.screen != self.w.screen or controller.screen_epoch != self.w._screen_epoch:
            controller.close()
            return None
        return controller.dialog

    def _focus_active_window(self):
        # Bare X11 has no window manager to keep the modal above its parent.
        if getattr(self, "closed", False):
            return None
        window = self._live_sound_dialog() or self.window
        window.present()
        if window.get_window():
            window.get_window().focus(Gdk.CURRENT_TIME)
        return window

    def _sound_closed(self, *_args):
        if self._focus_active_window() is self.window:
            self.arrival.grab_focus()

    def _select(self, path):
        self.w.select_disk(path)
        self.w.continue_pick()

    def _owner(self, checked, generation):
        if generation != self.generation or self.w.screen not in {Screen.WHAT, Screen.OWNER}:
            return
        self.w.set_owner(checked)
        self.primary.set_sensitive(self.w.owner_ok)

    def _token(self, text, generation):
        if generation != self.generation or self.w.screen != Screen.CONFIRM:
            return
        self.w.set_confirm_input(text)
        self.primary.set_sensitive(self.w.token_ok)

    def _keyboard_check_key(self, event, generation) -> bool:
        """Guided check (#140): the keysym the key printed Z produced."""
        if generation != self.generation or self.w.screen != Screen.KEYBOARD:
            return False
        name = Gdk.keyval_name(event.keyval) or ""
        if len(name) != 1:
            code = Gdk.keyval_to_unicode(event.keyval)
            name = chr(code) if code else ""
        if self.w.check_keyboard_key(name) is not None:
            self._check_fresh = True
            GLib.idle_add(self._rerender_keyboard_check, generation)
        return False  # the key still reaches the box

    def _rerender_keyboard_check(self, generation) -> bool:
        if generation == self.generation and self.w.screen == Screen.KEYBOARD:
            self.render()
        return False

    def _typing(self, text, generation):
        if generation != self.generation or self.w.screen != Screen.KEYBOARD:
            return
        self.w.set_typing_check(text)

    def update_status(self):
        if self.power_label and self.power_label.get_text() != self.w.power_text:
            self.power_label.set_text(self.w.power_text)
        if self.countdown_label:
            text = (
                f"{self.w.countdown_display} {C.COUNTDOWN_CAPTION}"
                if not self.w.erase_enabled
                else C.COUNTDOWN_READY
            )
            if self.countdown_label.get_text() != text:
                self.countdown_label.set_text(text)
            self.primary.set_sensitive(self.w.erase_enabled)
        if self.progress_label:
            view = self.w.progress_view
            if self.w.screen == Screen.STOPPING:
                text = view.stopping_text
                if self.progress_label.get_text() != text:
                    self.progress_label.set_text(text)
            else:
                # Paced (#132): a new step, quiet or resumed progress,
                # stopping or finishing speak promptly; otherwise at most
                # once a minute. No focus theft, no duplicate ATK events.
                spoken = self.progress_announcer.update(view, time.monotonic())
                if spoken is not None:
                    self._show_glance(view, spoken)
        if self.error_label:
            message = _error_text(self.w)
            changed = self.error_label.get_text() != message
            self.error_label.set_text(message)
            if changed and message:
                self.error_label.grab_focus()

    def _finish_toggled(self, widget, generation) -> None:
        if (
            generation != self.generation
            or self.w.screen != Screen.WORKING
            or getattr(self, "_syncing_finish", False)
        ):
            return
        self.w.set_finish_sound(widget.get_active())
        self._sync_finish_sound()

    def _sync_finish_sound(self) -> bool:
        """Update the walk-away line and toggle in place (#133).

        Returns False when a full render is needed instead (another sound
        message to show). In-place updates keep focus where it is.
        """
        toggle = self.finish_toggle
        if toggle is None or self.w.screen != Screen.WORKING:
            return False
        if self.w.sound_message != self._rendered_sound_message:
            return False
        enabled = self.w.finish_sound_toggle_enabled
        active = bool(self.w.sounds_enabled and enabled)
        if toggle.get_active() != active:
            # set_active emits "toggled"; this is not a person's choice.
            self._syncing_finish = True
            try:
                toggle.set_active(active)
            finally:
                self._syncing_finish = False
        toggle.set_sensitive(enabled)
        reason = self.w.finish_sound_reason
        toggle.get_accessible().set_description(reason)
        for label, text in (
            (self.walk_away_label, self.w.walk_away_text),
            (self.finish_reason_label, reason),
        ):
            if label is not None and label.get_text() != text:
                label.set_text(text)
        if self.finish_reason_label is not None:
            self.finish_reason_label.set_visible(bool(reason))
        self.sound_revision = getattr(self.w, "sound_revision", 0)
        return True

    def _show_glance(self, view, spoken: str) -> None:
        label = self.progress_label
        if label is None:
            return
        lines = list(view.glance_lines)
        if view.glance_stale:
            lines.append(view.glance_stale)
        lines.extend(view.glance_notes)
        if lines:
            head, rest = lines[0], lines[1:]
            markup = f'<span size="xx-large" weight="bold">{_markup_escape(head)}</span>'
            if rest:
                markup += "\n" + _markup_escape("\n".join(rest))
            label.set_markup(markup)
        label.get_accessible().set_name(spoken)
        if self.progress_bar is not None:
            percent = view.percent
            self.progress_bar.set_fraction(
                0.0 if percent is None else max(0.0, min(percent, 99.9)) / 100.0
            )

    def _begin_refresh_scan(self) -> bool:
        """Keep GTK and Orca responsive while inventory I/O runs."""
        seq = self.w.begin_refresh()
        if seq is None:
            return False
        launch_decided = None
        launch_allowed = [False]

        def run_if_launched() -> None:
            if launch_decided is None:
                return
            launch_decided.wait()
            with self._refresh_lock:
                accepted = launch_allowed[0]
            if accepted:
                self._refresh_worker(seq)

        try:
            launch_decided = threading.Event()
            threading.Thread(
                target=run_if_launched,
                name=f"beamo-accessible-refresh-{seq}",
                daemon=True,
            ).start()
            with self._refresh_lock:
                launch_decided.set()
                launch_allowed[0] = True
        except BaseException as exc:
            if launch_decided is not None:
                try:
                    launch_decided.set()
                except BaseException as cleanup:
                    add_note = getattr(exc, "add_note", None)
                    if callable(add_note):
                        add_note(f"Refresh wake also failed: {type(cleanup).__name__}")
            self.w.finish_refresh(seq, exc)
            return True
        return True

    def _refresh_worker(self, seq: int) -> None:
        try:
            outcome = self.w._run_rediscovery()
        except BaseException as exc:
            outcome = exc
        # The GTK timer applies the result; the worker never calls GTK or
        # mutates wizard state. Close may discard this daemon's final result.
        with self._refresh_lock:
            self._refresh_result = (seq, outcome)

    def _drain_refresh_result(self) -> None:
        with self._refresh_lock:
            pending = self._refresh_result
            self._refresh_result = None
        if pending is not None:
            self.w.finish_refresh(*pending)

    def tick(self):
        if self.closed:
            return False
        self._drain_refresh_result()
        self.w.tick()
        dialog = getattr(self, "_sound_dialog", None)
        if dialog is not None:
            dialog.poll()
        if self.w.wants_shutdown or self.w.wants_new_session:
            self.close()
            return False
        if (
            self.shown == self.w.screen == Screen.WORKING
            and getattr(self, "sound_revision", 0) != getattr(self.w, "sound_revision", 0)
        ):
            self._sync_finish_sound()
        if (
            self.shown != self.w.screen
            or self.report_revision != self.w.report_view.revision
            or (self.w.screen in {Screen.DONE, Screen.WORKING} and getattr(self, "sound_revision", 0) != getattr(self.w, "sound_revision", 0))
        ):
            self.render()
        else:
            self.update_status()
        return True

    def _remember_key_press(self, event):
        key = event.keyval
        guarded = key in {
            Gdk.KEY_Return,
            Gdk.KEY_KP_Enter,
            Gdk.KEY_space,
            Gdk.KEY_F5,
            Gdk.KEY_Escape,
        }
        event_time = getattr(event, "time", None)
        repeat_pair = (
            guarded
            and type(event_time) is int
            and event_time > 0
            and self._release_times.get(key) == event_time
        )
        # X11 auto-repeat can deliver a KeyRelease/KeyPress pair with the
        # same server timestamp. A held Enter must not become a new Erase
        # action just because the review countdown completed between them.
        if guarded and (key in self.held or repeat_pair):
            self.held.add(key)
            return True
        self._release_times.pop(key, None)
        self.held.add(key)
        return False

    def _modal_key_press(self, _window, event):
        # A modal may close on key-down. Its held key still belongs to the
        # same physical press when auto-repeat reaches the parent window.
        return self._remember_key_press(event)

    def _key_press(self, _window, event):
        if getattr(self, "closed", False):
            return True
        # Someone is back (#133): stop repeating the finish sound.
        getattr(self.w, "acknowledge_finish_sound", lambda: None)()
        if self._remember_key_press(event):
            return True
        key = event.keyval
        if key in (Gdk.KEY_l, Gdk.KEY_L) and self.w.screen == Screen.METHOD:
            self.w.open_limits()
            self.render()
            return True
        if key in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and self.w.screen == Screen.LAST_CHANCE:
            # Enter must not activate a default Erase button while focus is
            # on the warning label. Match Tk: only a current, focused enabled
            # control, including the keyboard and refresh utilities.
            focused = self.window.get_focus()
            if (focused is not None
                    and any(control is focused for control in self.actions.values())
                    and focused.get_sensitive()):
                focused.clicked()
            return True
        if key == Gdk.KEY_F5 and self.w.can_refresh:
            if self.w.screen == Screen.REFRESH_CONFIRM:
                # A second F5 accepts only the unguarded (Pick) dialog (#136).
                if not self.w.refresh_guarded:
                    self._begin_refresh_scan()
            elif self.w.refresh_offered:
                self.w.open_refresh_confirm()
            self.render()
            return True
        if key == Gdk.KEY_Escape:
            if self.w.screen == Screen.WORKING:
                if self.w.stop_confirmation is not None:
                    self.w.keep_erasing()
                else:
                    self.w.request_stop()
                self.render()
                return True
            self.w.back()
            self.render()
            return True
        return False

    def _key_release(self, _window, event):
        key = event.keyval
        self.held.discard(key)
        event_time = getattr(event, "time", None)
        if (
            key in {Gdk.KEY_Return, Gdk.KEY_KP_Enter, Gdk.KEY_space, Gdk.KEY_F5, Gdk.KEY_Escape}
            and type(event_time) is int
            and event_time > 0
        ):
            self._release_times[key] = event_time
        else:
            self._release_times.pop(key, None)
        return False

    def _close(self, *_args):
        if self.w.screen == Screen.WORKING:
            self.w.request_stop()
            self.render()
        else:
            self.w.shutdown()
            if self.w.wants_shutdown or self.w.wants_new_session:
                self.close()
            else:
                self.render()
        return True

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.generation = getattr(self, "generation", 0) + 1
        errors = []

        def cleanup(action):
            try:
                action()
            except BaseException as error:
                errors.append(error)

        cleanup(getattr(self.w, "cancel_audio", lambda: None))
        dialog = getattr(self, "_sound_dialog", None)
        if dialog is not None:
            cleanup(dialog.close)
        if self.timer:
            timer, self.timer = self.timer, 0
            cleanup(lambda: GLib.source_remove(timer))
        if self.window is not None:
            cleanup(self.window.destroy)

        def quit_owned_loop():
            level = Gtk.main_level()
            # Old __new__ callers have no recorded loop. Real views record
            # ownership before entering Gtk.main, never during construction.
            owned = getattr(self, "_main_loop_level", level)
            if level and owned == level:
                Gtk.main_quit()

        cleanup(quit_owned_loop)
        if errors:
            add_note = getattr(errors[0], "add_note", None)
            if callable(add_note):
                for error in errors[1:]:
                    add_note(f"GTK cleanup also failed: {type(error).__name__}")
            raise errors[0]

    def _close_preserving_error(self, original):
        try:
            self.close()
        except BaseException as cleanup_error:
            if original is None:
                raise
            add_note = getattr(original, "add_note", None)
            if callable(add_note):
                add_note(f"GTK view cleanup also failed: {type(cleanup_error).__name__}")

    def _runtime_failure(self, _kind, error, _traceback):
        self.failed = True
        try:
            from beamo_wipe.diagnostics import log_diag

            log_diag("ui", "accessible_runtime_failed", type(error).__name__)
        except BaseException:
            # Logging is optional; losing it must never release a live erase.
            pass
        try:
            self.w.settle_failed_interface()
        finally:
            self.close()

    def run(self):
        previous = sys.excepthook
        original = None
        try:
            self._main_loop_level = Gtk.main_level() + 1
            sys.excepthook = self._runtime_failure
            Gtk.main()
        except BaseException as error:
            original = error
            raise
        finally:
            sys.excepthook = previous
            try:
                self._close_preserving_error(original)
            finally:
                self._main_loop_level = None
        return 3 if self.failed else 0


def start_live_reader():
    """Start PulseAudio and Orca on the live USB. Returns the Orca Popen or None.

    Off the live USB (preview) nothing is started. Audio or reader failures
    never raise: the view stays usable without speech and the failure is logged.
    """
    from beamo_wipe.safety import running_on_live_usb, session_exec_env

    if not running_on_live_usb():
        return None
    session_env = session_exec_env()
    try:
        subprocess.run(
            ["/usr/bin/pulseaudio", "--start", "--exit-idle-time=60"],
            check=True,
            timeout=10,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            env=session_env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        try:
            from beamo_wipe.diagnostics import log_diag

            log_diag("accessible", "pulseaudio_failed", type(exc).__name__)
        except Exception:
            pass
    try:
        return subprocess.Popen(
            ["/usr/bin/orca"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            env=session_env,
        )
    except OSError as exc:
        try:
            from beamo_wipe.diagnostics import log_diag

            log_diag("accessible", "orca_failed", type(exc).__name__)
        except Exception:
            pass
        return None


def stop_live_reader(reader) -> None:
    if reader is None:
        return
    try:
        if reader.poll() is not None:
            return
        try:
            reader.terminate()
        except ProcessLookupError:
            # Orca may exit between poll and terminate; still reap it.
            pass
        try:
            reader.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                reader.kill()
            except ProcessLookupError:
                pass
            reader.wait(timeout=5)
    except (OSError, subprocess.SubprocessError):
        # Reader cleanup is best effort and must not replace the UI outcome.
        pass


def run_accessible(wizard: Wizard, fullscreen: bool = False, reader=None) -> int:
    owned = start_live_reader() if reader is None else None
    try:
        return AccessibleWizard(wizard, fullscreen).run()
    finally:
        stop_live_reader(owned)


def _ensure_gtk_display() -> None:
    """Raise StartupDisplayUnavailable when no display is reachable.

    Same fail-safe idea as the Tk probe: a child process attempts the
    display connection, so a headless host becomes a catchable error and
    app.py keeps its existing graphical-failure path.
    """
    from beamo_wipe.safety import session_exec_env

    try:
        probe = subprocess.run(
            [sys.executable, "-c",
             "from gi.repository import Gtk as _G; "
             "_w = _G.Window(); _w.destroy()"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
            check=False,
            shell=False,
            env=session_exec_env(),
        )
    except (OSError, subprocess.SubprocessError):
        raise StartupDisplayUnavailable("no accessible display for startup stages")
    if probe.returncode != 0:
        raise StartupDisplayUnavailable("no accessible display for startup stages")


def run_accessible_startup(build, *, fullscreen: bool = False,
                           stall_after_s: float | None = None) -> tuple:
    """Show startup stages in the screen-reader view while ``build()`` runs.

    Same worker discipline and return protocol as ``run_tk_startup``:
    ("wizard", wizard), ("failed", exc), or ("abandoned", None) on window
    close or Escape. Stage rows are plain labels; the status line takes
    keyboard focus and is selectable so a screen reader announces it.
    Raises StartupDisplayUnavailable (never aborts) when no display is reachable.
    """
    _ensure_gtk_display()
    from beamo_wipe.startup_stages import STALL_AFTER_S, StartupRun

    run = StartupRun(
        build,
        stall_after_s=STALL_AFTER_S if stall_after_s is None else stall_after_s,
    )
    outcome: list = []
    try:
        window = Gtk.Window(title=C.STARTING_TITLE)
    except Exception as exc:
        raise StartupDisplayUnavailable(f"no accessible display for startup stages: {exc}") from exc
    poll_source = None
    original = None
    try:
        window.set_name("beamo-accessible")
        window.set_default_size(640, 420)
        if fullscreen:
            display = window.get_display()
            monitor = display.get_primary_monitor() or display.get_monitor(0)
            if monitor is not None:
                geometry = monitor.get_geometry()
                window.set_default_size(geometry.width, geometry.height)
                window.move(geometry.x, geometry.y)
            window.fullscreen()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_border_width(24)
        window.add(box)
        rows = []
        for _i in range(3):
            status = Gtk.Label()
            title = Gtk.Label()
            title.get_style_context().add_class("screen-heading")
            hint = Gtk.Label()
            hint.set_line_wrap(True)
            hint.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
            box.pack_start(status, False, False, 0)
            box.pack_start(title, False, False, 0)
            box.pack_start(hint, False, False, 6)
            rows.append((status, title, hint))
        stall = Gtk.Label()
        stall.set_line_wrap(True)
        box.pack_start(stall, False, False, 6)
        status_line = Gtk.Label(label="")
        status_line.set_can_focus(True)
        status_line.set_selectable(True)
        box.pack_start(status_line, False, False, 6)

        _STATUS_WORDS = {"pending": C.STARTUP_STATE_WAITING, "active": C.STARTUP_STATE_WORKING, "done": C.STARTUP_STATE_DONE}

        def render() -> None:
            snap = run.drain()
            for (status, title, hint), row in zip(rows, snap):
                status.set_text(_STATUS_WORDS[row["state"]])
                title.set_text(row["title"])
                hint.set_text(row["hint"])
            note = run.stalled_note(persistent=True)
            stall.set_text(note or "")
            active = [row for row in snap if row["state"] == "active"]
            if active:
                status_line.set_text(f"{active[0]['title']} — {C.STARTUP_STATE_WORKING}")

        loop_level = None

        def quit_owned_loop() -> None:
            if loop_level is not None and Gtk.main_level() == loop_level:
                Gtk.main_quit()

        def finish(result) -> bool:
            outcome.append(result)
            window.destroy()
            quit_owned_loop()
            return False

        def close(*_args):
            if not outcome:
                outcome.append(("abandoned", None))
            window.destroy()
            quit_owned_loop()
            return False

        def poll() -> bool:
            if outcome:
                return False
            render()
            result = run.poll()
            if result is None:
                return True
            # run.poll() applied the final report; announce it before closing.
            render()
            return finish(result)

        window.connect("delete-event", close)
        window.connect("key-press-event", lambda _w, event: close()
                       if event.keyval in (Gdk.KEY_Escape,) else None)
        window.show_all()
        window.present()
        if window.get_window():
            window.get_window().focus(Gdk.CURRENT_TIME)
        status_line.grab_focus()
        render()
        try:
            run.start()
        except Exception as exc:
            # A failed worker launch cannot produce a poll result. Release the
            # startup window before the caller opens its blocked support view.
            window.destroy()
            return ("failed", exc)
        poll_source = GLib.timeout_add(100, poll)
        loop_level = Gtk.main_level() + 1
        Gtk.main()
        if outcome:
            return outcome[0]
        return ("abandoned", None)
    except BaseException as error:
        original = error
        raise
    finally:
        # Startup owns exactly this window and timeout. Retire them even when
        # setup, worker launch or the main loop is interrupted; peer windows,
        # timers and nested event loops belong to their own callers.
        cleanup_errors = []
        try:
            if poll_source is not None:
                pending = GLib.MainContext.default().find_source_by_id(poll_source)
                if pending is not None:
                    pending.destroy()
        except BaseException as error:
            cleanup_errors.append(error)
        try:
            window.destroy()
        except BaseException as error:
            cleanup_errors.append(error)
        if cleanup_errors:
            first = original if original is not None else cleanup_errors[0]
            add_note = getattr(first, "add_note", None)
            if callable(add_note):
                for cleanup_error in cleanup_errors:
                    if cleanup_error is not first:
                        add_note(f"GTK startup cleanup also failed: {type(cleanup_error).__name__}")
            if original is None:
                raise first
