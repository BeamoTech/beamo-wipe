import pytest
from test_accessible_focus_input_pass11 import native, fake_effects, ui, Gdk
from test_accessible_focus_input_pass11 import test_first_fresh_native_activation_after_sound_close_is_not_lost as original

@pytest.mark.parametrize("iteration", range(80))
def test_first_fresh_native_activation_after_sound_close_iteration(ui, native, iteration):
    original(ui, native, Gdk.KEY_Return)
