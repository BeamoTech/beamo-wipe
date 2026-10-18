import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from beamo_wipe import sound
from beamo_wipe.ui.sound_dialog import SoundDialog


class Radio:
    def __init__(self, output, active):
        self.output = output
        self.active = active

    def get_active(self):
        return self.active


old = sound.SoundOutput("speakers", "Speakers", "speakers", True)
requested = sound.SoundOutput("headphones", "Headphones", "headphones", False)
previous_radio = Radio(old, False)
requested_radio = Radio(requested, True)
dialog = object.__new__(SoundDialog)
dialog.w = SimpleNamespace(set_sound_output=lambda _sink: None)
dialog.chosen = old
dialog.radios = [previous_radio, requested_radio]
dialog._announce = lambda message: events.append({"announce": message})
dialog._show_volume = lambda _state: None
dialog._submit = lambda action, done: done(action())
events = []

with patch.object(sound, "set_output", lambda sink: sound.SoundResult(False, "controlled failure")):
    dialog._output_toggled(requested_radio, requested)

with patch.object(sound, "nudge_volume", lambda sink, delta: events.append({"nudge_sink": sink}) or sound.SoundResult(False, "controlled failure")):
    dialog._nudge(None, sound.VOLUME_STEP)

trace = {
    "visible_selected_sink": next(radio.output.id for radio in dialog.radios if radio.get_active()),
    "chosen_sink": dialog.chosen.id,
    "events": events,
}
Path("/tmp/pass10-ui/original-sound-selection-trace.json").write_text(json.dumps(trace, indent=2) + "\n")
print(json.dumps(trace, indent=2))
assert trace["visible_selected_sink"] == trace["chosen_sink"], "Visible sink and subsequent volume target disagree after failed selection"
