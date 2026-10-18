"""Diagnostic observer: record, do not alter, original native GTK key handling."""
import json
import pytest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_call(item):
    if 'first_fresh_native_activation_after_sound_close' not in item.name:
        yield
        return
    from beamo_wipe.ui.accessible_wizard import AccessibleWizard
    original = AccessibleWizard._remember_key_press
    rows = []

    def remember(app, event):
        row = {'key': event.keyval, 'time': event.time,
               'previous_release': app._release_times.get(event.keyval),
               'held_before': event.keyval in app.held}
        result = original(app, event)
        row['blocked'] = result
        rows.append(row)
        return result

    AccessibleWizard._remember_key_press = remember
    try:
        yield
    finally:
        AccessibleWizard._remember_key_press = original
        item.user_properties.append(('diagnostic_native_keys', json.dumps(rows)))
