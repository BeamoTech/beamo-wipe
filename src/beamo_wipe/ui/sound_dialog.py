# SPDX-License-Identifier: GPL-3.0-or-later
"""GTK sound controls. All GTK and wizard changes stay on the GTK loop."""

from beamo_wipe import copy as C, sound
from beamo_wipe.audio_jobs import worker
from beamo_wipe.models import Screen


class SoundDialog:
    def __init__(self, gtk, window, wizard, on_stop=None):
        self.Gtk = gtk
        self.w = wizard
        self.screen = wizard.screen
        self.screen_epoch = wizard._screen_epoch
        self.on_stop = on_stop
        self.ticket = None
        self.done = None
        self.dialog = gtk.Dialog(title=C.SOUND_CHECK_TITLE)
        self.dialog.set_transient_for(window)
        self.dialog.set_modal(True)
        self.dialog.set_destroy_with_parent(True)
        self.dialog.set_default_size(560, 480)
        box = self.dialog.get_content_area()
        box.set_spacing(6)
        box.set_border_width(16)
        self.status = self._label(C.SOUND_CHECKING)
        self.status.set_can_focus(True)
        self.status.set_selectable(True)
        box.pack_start(self.status, False, False, 4)
        self.orca_notice = self._label("")
        box.pack_start(self.orca_notice, False, False, 4)
        self.output_box = gtk.Box(orientation=gtk.Orientation.VERTICAL, spacing=3)
        box.pack_start(self.output_box, False, False, 0)
        self.chosen = None
        self.muted = False
        self.radios = []
        self.volume_label = self._label(C.SOUND_VOLUME_UNKNOWN)
        controls = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=8)
        box.pack_start(controls, False, False, 4)
        controls.pack_start(self.volume_label, True, True, 0)
        self.controls = controls
        louder = gtk.Button.new_with_label(C.SOUND_LOUDER)
        quieter = gtk.Button.new_with_label(C.SOUND_QUIETER)
        self.mute_button = gtk.Button.new_with_label(C.SOUND_MUTE)
        for button in (louder, quieter, self.mute_button):
            controls.pack_start(button, False, False, 0)
        louder.connect("clicked", self._nudge, sound.VOLUME_STEP)
        quieter.connect("clicked", self._nudge, -sound.VOLUME_STEP)
        self.mute_button.connect("clicked", self._mute)
        self.play_button = gtk.Button.new_with_label(C.SOUND_PLAY_TEST)
        box.pack_start(self.play_button, False, False, 4)
        self.play_button.connect("clicked", self._play_speech)
        outcome_row = gtk.Box(orientation=gtk.Orientation.HORIZONTAL, spacing=8)
        box.pack_start(outcome_row, False, False, 4)
        toggle = gtk.Button.new_with_label(wizard.sound_toggle_text)
        self.hear_button = gtk.Button.new_with_label(C.SOUND_HEAR)
        outcome_row.pack_start(toggle, False, False, 0)
        outcome_row.pack_start(self.hear_button, False, False, 0)
        toggle.connect("clicked", self._toggle, toggle)
        self.hear_button.connect("clicked", self._hear_outcomes)
        box.pack_start(self._label(C.SOUND_RECOVERY), False, False, 4)
        if wizard.screen == Screen.WORKING:
            stop_button = gtk.Button.new_with_label(C.STOP_ASK)
            box.pack_start(stop_button, False, False, 4)
            stop_button.connect("clicked", self._request_stop)
        self.dialog.add_button(C.SOUND_CLOSE, gtk.ResponseType.CLOSE)
        self.dialog.connect("response", lambda *_: self.dialog.destroy())
        self.dialog.connect("close", lambda *_: self.dialog.destroy())
        self.review_overlay = wizard.begin_review_overlay()
        self.dialog.connect("destroy", self._destroyed)
        self.remembered = wizard.sound_output
        self._busy(True)
        try:
            self.dialog.show_all()
            self.status.grab_focus()
            self._submit(self._discover, self._discovered)
        except BaseException:
            self.dialog.destroy()
            raise

    def _label(self, message):
        label = self.Gtk.Label(label=message)
        label.set_line_wrap(True)
        label.set_xalign(0)
        label.set_max_width_chars(65)
        return label

    def _announce(self, message):
        self.status.set_text(message)
        self.status.grab_focus()

    def _busy(self, busy):
        enabled = self.chosen is not None and not busy
        for widget in (self.controls, self.play_button, self.hear_button):
            widget.set_sensitive(enabled)
        for radio in self.radios:
            radio.set_sensitive(not busy)

    def _submit(self, action, done):
        if self.ticket is not None:
            self.ticket.cancel()
        self._busy(True)
        self._announce(C.SOUND_CHECKING)
        self.done = done
        self.ticket = worker.submit(action)

    def poll(self):
        if self.dialog is None:
            return
        if self.screen != self.w.screen or self.screen_epoch != self.w._screen_epoch:
            self.close()
            return
        ticket = self.ticket
        if ticket is None:
            return
        ready, value = ticket.poll()
        if not ready:
            return
        self.ticket = None
        done = self.done
        self.done = None
        self._busy(False)
        if value is None or isinstance(value, BaseException):
            try:
                from beamo_wipe.diagnostics import log_diag

                log_diag("audio", "dialog_operation_failed", type(value).__name__)
            except Exception:
                pass
            self._announce(C.SOUND_ACTION_FAILED)
        else:
            done(value)

    def close(self):
        if self.dialog is not None:
            self.dialog.destroy()

    def _request_stop(self, _button):
        self.w.request_stop()
        self.close()
        if self.on_stop is not None:
            self.on_stop()

    def _destroyed(self, *_):
        if self.ticket is not None:
            self.ticket.cancel()
            self.ticket = None
        self.done = None
        self.dialog = None
        if self.review_overlay:
            self.w.end_review_overlay()

    def _show_volume(self, state):
        if state is not None and state.available and state.volume_percent is not None:
            text = f"{C.SOUND_VOLUME}: {state.volume_percent}%"
            if state.muted:
                text += f", {C.SOUND_MUTED_STATE}"
            elif state.volume_percent < 20:
                text += f" {C.SOUND_VOLUME_LOW}"
            self.muted = bool(state.muted)
        else:
            text = C.SOUND_VOLUME_UNKNOWN
        self.volume_label.set_text(text)
        self.mute_button.set_label(C.SOUND_UNMUTE if self.muted else C.SOUND_MUTE)

    def _discover(self):
        state = sound.list_outputs()
        applied = None
        if state.available and self.remembered:
            applied = sound.set_output(self.remembered)
            if applied.ok:
                state = sound.list_outputs()
        return state, applied, sound.orca_running()

    def _discovered(self, value):
        state, applied, orca = value
        if orca is False:
            self.orca_notice.set_text(C.SOUND_ORCA_MISSING)
        if not state.available:
            self._announce(state.message)
            return
        self.chosen = sound.resolve_output(self.w.sound_output, state)
        group = None
        for output in state.outputs:
            choice = self.Gtk.RadioButton.new_with_label_from_widget(group, output.label)
            choice.get_accessible().set_description(output.detail)
            choice.get_child().set_line_wrap(True)
            choice.get_child().set_max_width_chars(65)
            group = choice
            self.output_box.pack_start(choice, False, False, 3)
            self.radios.append(choice)
            if self.chosen is not None and output.id == self.chosen.id:
                choice.set_active(True)
            choice.connect("toggled", self._output_toggled, output)
            choice.show_all()
        self._show_volume(state)
        self._busy(False)
        self._announce(applied.message if applied is not None and not applied.ok else C.SOUND_DIALOG_LEAD)

    def _output_toggled(self, choice, output):
        if not choice.get_active():
            return
        def action():
            result = sound.set_output(output.id)
            return result, sound.list_outputs() if result.ok else None
        def done(value):
            result, state = value
            if result.ok:
                self.w.set_sound_output(output.id)
                self.chosen = output
                self._show_volume(state)
                self._announce(f"{output.label} {C.SOUND_SELECTED}")
            else:
                self._announce(result.message)
        self._submit(action, done)

    def _nudge(self, _button, delta):
        if self.chosen is None:
            return
        sink_id = self.chosen.id
        def action():
            result = sound.nudge_volume(sink_id, delta)
            return result, sound.list_outputs() if result.ok else None
        def done(value):
            result, state = value
            if result.ok:
                self._show_volume(state)
                self._announce(C.SOUND_DIALOG_LEAD)
            else:
                self._announce(result.message)
        self._submit(action, done)

    def _mute(self, _button):
        if self.chosen is None:
            return
        sink_id, muted = self.chosen.id, not self.muted
        def action():
            result = sound.set_muted(sink_id, muted)
            return result, sound.list_outputs() if result.ok else None
        def done(value):
            result, state = value
            if result.ok:
                self._show_volume(state)
                self._announce(C.SOUND_DIALOG_LEAD)
            else:
                self._announce(result.message)
        self._submit(action, done)

    def _play_speech(self, _button):
        if self.chosen is None:
            return
        sink_id = self.chosen.id
        def action():
            applied = sound.set_output(sink_id)
            return applied, sound.play_speech_test() if applied.ok else None
        def done(value):
            applied, result = value
            if applied.ok:
                self.w.set_sound_output(sink_id)
                self._announce(result.message)
            else:
                self._announce(applied.message)
        self._submit(action, done)

    def _toggle(self, _button, toggle):
        self.w.toggle_sounds()
        toggle.set_label(self.w.sound_toggle_text)
        self._announce(self.w.sound_message)

    def _hear_outcomes(self, _button):
        if self.chosen is None:
            return
        sink_id = self.chosen.id
        def action():
            applied = sound.set_output(sink_id)
            if not applied.ok:
                return applied, None
            first = sound.play_test(sound.KIND_FINISHED)
            if not first.ok:
                return applied, first
            second = sound.play_test(sound.KIND_ATTENTION)
            return applied, sound.SoundResult(
                second.ok,
                first.message + " " + second.message if second.ok else second.message,
            )
        def done(value):
            applied, result = value
            if applied.ok:
                self.w.set_sound_output(sink_id)
                self.w.set_sound_message(result.message)
                self._announce(result.message)
            else:
                self._announce(applied.message)
        self._submit(action, done)
