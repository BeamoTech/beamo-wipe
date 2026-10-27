"""A failed volume query must not prevent an accepted mute state from toggling."""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest


def dialog_type():
    path = Path(__file__).parents[1] / "src/beamo_wipe/ui/sound_dialog.py"
    tree = ast.parse(path.read_bytes())
    original = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "SoundDialog")
    methods = [node for node in original.body if isinstance(node, ast.FunctionDef)
               and node.name in {"_show_volume", "_mute"}]
    node = ast.ClassDef(name="Dialog", bases=[], keywords=[], body=methods, decorator_list=[])
    namespace = {
        "C": SimpleNamespace(SOUND_VOLUME="Volume", SOUND_VOLUME_UNKNOWN="Volume unavailable",
                             SOUND_MUTED_STATE="muted", SOUND_VOLUME_LOW="low",
                             SOUND_UNMUTE="Unmute", SOUND_MUTE="Mute", SOUND_DIALOG_LEAD="Ready"),
    }
    # Only these two repository methods run, with fake sound and widget boundaries.
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), str(path), "exec"), namespace)  # noqa: S102
    return namespace, namespace["Dialog"]


class PartialSoundStateTests(unittest.TestCase):
    def test_known_mute_state_drives_label_and_repeated_toggle_without_volume(self):
        for previous in (False, True):
            for volume in (None, 40):
                for muted in (False, True):
                    with self.subTest(previous=previous, volume=volume, muted=muted):
                        namespace, dialog = dialog_type()
                        state = SimpleNamespace(available=True, volume_percent=volume, muted=muted)
                        writes, labels = [], []

                        def set_muted(sink, wanted):
                            writes.append((sink, wanted))
                            state.muted = wanted
                            return SimpleNamespace(ok=True, message="")

                        namespace["sound"] = SimpleNamespace(set_muted=set_muted, list_outputs=lambda: state)
                        obj = dialog()
                        obj.muted = previous
                        obj.chosen = SimpleNamespace(id="speaker")
                        obj.volume_label = SimpleNamespace(set_text=lambda _text: None)
                        obj.mute_button = SimpleNamespace(set_label=labels.append)
                        obj._announce = lambda _message: None
                        obj._submit = lambda action, done: done(action())
                        obj._show_volume(state)
                        self.assertEqual(labels[-1], "Unmute" if muted else "Mute")
                        obj._mute(None)
                        self.assertEqual(writes, [("speaker", not muted)])
                        self.assertEqual(labels[-1], "Mute" if muted else "Unmute")
                        obj._mute(None)
                        self.assertEqual(writes, [("speaker", not muted), ("speaker", muted)])

    def test_absent_or_unavailable_mute_observation_keeps_last_accepted_state(self):
        for previous in (False, True):
            for state in (None,
                          SimpleNamespace(available=False, volume_percent=None, muted=not previous),
                          SimpleNamespace(available=True, volume_percent=None, muted=None)):
                with self.subTest(previous=previous, state=state):
                    _namespace, dialog = dialog_type()
                    obj = dialog()
                    obj.muted = previous
                    labels = []
                    obj.volume_label = SimpleNamespace(set_text=lambda _text: None)
                    obj.mute_button = SimpleNamespace(set_label=labels.append)
                    obj._show_volume(state)
                    self.assertEqual(labels[-1], "Unmute" if previous else "Mute")
