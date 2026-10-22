"""Actual wizard review detours/layout invalidation, with fake starts only."""
from itertools import product
from pathlib import Path
import hashlib
import json
import os

from pytest import MonkeyPatch
from beamo_wipe import app, sound
from beamo_wipe.demo import discovery_for_scenario
from beamo_wipe.keyboard import ApplyResult
from beamo_wipe.models import MethodId, Screen
from beamo_wipe.nwipe_runner import DryRunRunner, NwipeRunner
from beamo_wipe.wizard import Wizard

counts = {'review_scenarios': 0, 'layout_scenarios': 0, 'detours': 0,
          'nested_overlay_claims': 0, 'overlay_held_refusals': 0,
          'fresh_countdown_checks': 0, 'layout_invalidation_controls': 0,
          'layout_preservation_controls': 0, 'wrong_token_refusals': 0,
          'owner_refusals': 0, 'blocked_erase_calls': 0,
          'explicit_fake_starts': 0, 'native_callbacks': 0, 'mismatches': 0}


class Clock:
    value = 100.0
    def __call__(self): return self.value


def forbidden(*args, **kwargs):
    counts['native_callbacks'] += 1
    raise AssertionError('Native boundary reached')


def blocked(w):
    w.confirm_erase()
    assert not w.runner.started
    counts['blocked_erase_calls'] += 1


def authorize(w, method):
    w.set_owner(True); w.continue_owner()
    assert w.screen == Screen.PICK
    w.select_disk(w.selectable[0].path); w.continue_pick()
    assert w.screen == Screen.CONFIRM
    w.set_confirm_input(w.confirm.token); w.continue_confirm()
    w.set_method(method); w.continue_method()
    assert w.screen == Screen.LAST_CHANCE


def make(method, stage='last'):
    clock = Clock()
    w = Wizard(initial, DryRunRunner(clock=clock), clock=clock,
               wall_clock=lambda: '2026-10-21T00:00:00Z')
    w._write_evidence = lambda **kwargs: None
    w.skip_intro()
    if stage == 'owner': return w, clock
    authorize(w, method)
    if stage == 'method': w.back()
    if stage == 'confirm': w.back(); w.back()
    return w, clock


def detour(w, name):
    if name.startswith('keyboard'):
        w.open_keyboard(); assert w.screen == Screen.KEYBOARD
    elif name.startswith('advanced'):
        w.open_advanced(); assert w.screen == Screen.ADVANCED
        # A report-help visit composes with the advanced return target.
        w.open_report_help(); assert w.screen == Screen.REPORT_HELP
        w.close_report_help(); assert w.screen == Screen.ADVANCED
    elif name.startswith('refresh'):
        assert w.open_refresh_confirm(); assert w.screen == Screen.REFRESH_CONFIRM
    elif name.startswith('diagnostic'):
        w.error = 'Controlled display error'
        w.open_diagnostic(); assert w.screen == Screen.DIAGNOSTIC
    else:
        w.report_wanted = True; w.shutdown(); assert w.screen == Screen.SHUTDOWN_CONFIRM
    blocked(w)
    w._clock.value += 30
    blocked(w)
    method = {'keyboard-accept': 'accept_keyboard', 'keyboard-back': 'back',
              'advanced-close': 'close_advanced', 'advanced-back': 'back',
              'refresh-cancel': 'cancel_refresh_confirm', 'refresh-back': 'back',
              'diagnostic-close': 'close_diagnostic', 'diagnostic-back': 'back',
              'shutdown-keep': 'keep_report_session', 'shutdown-back': 'back'}[name]
    getattr(w, method)()
    assert w.screen == Screen.LAST_CHANCE
    assert w.countdown_left == 5
    assert not w.runner.started
    counts['detours'] += 1
    counts['fresh_countdown_checks'] += 1
    blocked(w)


def finish(w, clock):
    start = clock.value
    clock.value = start + 4.999
    assert not w.erase_enabled; blocked(w)
    clock.value = start + 5.0
    assert w.erase_enabled and not w.runner.started
    w.confirm_erase()
    assert w.runner.started and w.screen == Screen.WORKING
    counts['explicit_fake_starts'] += 1


with MonkeyPatch.context() as patch:
    patch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    patch.delenv('BEAMO_WIPE_LIVE', raising=False)
    for boundary in ('subprocess.run', 'subprocess.Popen', 'os.kill',
                     'beamo_wipe.discover.run_lsblk', 'beamo_wipe.discover.read_cmdline',
                     'beamo_wipe.discover.read_mount_sources'):
        patch.setattr(boundary, forbidden)
    patch.setattr(NwipeRunner, 'start', forbidden)
    patch.setattr(app, '_shutdown', forbidden)
    patch.setattr(sound, '_run', forbidden); patch.setattr(sound, '_popen', forbidden)
    patch.setattr('beamo_wipe.diagnostics.log_diag', lambda *a, **k: None)
    patch.setattr('beamo_wipe.diagnostics.emit_serial_marker', lambda *a, **k: None)
    original = os.path.realpath
    patch.setattr(os.path, 'realpath', lambda p, *a, **k: str(p) if str(p).startswith('/dev/') else original(p, *a, **k))
    initial = discovery_for_scenario('happy')
    routes = ('keyboard-accept', 'keyboard-back', 'advanced-close', 'advanced-back',
              'refresh-cancel', 'refresh-back', 'diagnostic-close', 'diagnostic-back',
              'shutdown-keep', 'shutdown-back')
    for route, method, depth, elapsed in product(routes, MethodId, (0, 1, 2), (0, 4.999, 5, 30)):
        counts['review_scenarios'] += 1
        w, clock = make(method)
        clock.value += elapsed
        assert not w.runner.started
        for _ in range(depth):
            assert w.begin_review_overlay(); counts['nested_overlay_claims'] += 1
        detour(w, route)
        # A second different public detour must also restart visible review.
        detour(w, routes[(routes.index(route) + 3) % len(routes)])
        if depth:
            clock.value += 100
            assert not w.erase_enabled; blocked(w)
            counts['overlay_held_refusals'] += 1
        for remaining in reversed(range(depth)):
            w.end_review_overlay()
            if remaining:
                assert not w.erase_enabled; blocked(w)
                counts['overlay_held_refusals'] += 1
            else:
                assert w.countdown_left == 5
                counts['fresh_countdown_checks'] += 1
        # Extra late duplicate overlay closes do not authorize or extend a timer.
        before = w._erase_until
        w.end_review_overlay(); w.end_review_overlay()
        assert w._erase_until == before and w._review_overlay_depth == 0
        finish(w, clock)
    for stage, method, case in product(('confirm', 'method', 'last'), MethodId,
                                       ('same', 'unknown', 'none', 'list', 'apply-refuse', 'apply-success-fr', 'apply-success-de')):
        counts['layout_scenarios'] += 1
        w, clock = make(method, stage)
        clock.value += 30
        previous_screen = w.screen
        previous = (w.owner_ok, w.selected, w.confirm_input, w._authorized_operation)
        w.open_keyboard(); assert w.screen == Screen.KEYBOARD
        inputs = {'same': 'us', 'unknown': 'not-a-layout', 'none': None, 'list': ['fr'],
                  'apply-refuse': 'fr', 'apply-success-fr': 'fr', 'apply-success-de': 'de'}
        target = inputs[case]
        applied = []
        def apply(layout_id):
            applied.append(layout_id)
            return ApplyResult(case.startswith('apply-success'), 'Controlled result', layout_id)
        w._apply_keyboard = apply
        result = w.set_keyboard_layout(target)
        changed = case.startswith('apply-success')
        assert result is (changed or case == 'same')
        if changed:
            assert applied == [target]
            assert not w.owner_ok and w.selected is None and w.confirm_input == ''
            assert w._authorized_operation is None and w._erase_until is None
            counts['layout_invalidation_controls'] += 1
        else:
            assert (w.owner_ok, w.selected, w.confirm_input, w._authorized_operation) == previous
            assert applied == (['fr'] if case == 'apply-refuse' else [])
            counts['layout_preservation_controls'] += 1
        blocked(w)
        w.accept_keyboard()
        assert w.screen == (Screen.OWNER if changed else previous_screen)
        if previous_screen == Screen.LAST_CHANCE and not changed:
            assert w.countdown_left == 5
            counts['fresh_countdown_checks'] += 1
        for _ in range(4):
            if w.screen == Screen.OWNER: break
            w.back()
        assert w.screen == Screen.OWNER
        w.set_owner(False); w.continue_owner(); assert w.screen == Screen.OWNER
        blocked(w); counts['owner_refusals'] += 1
        w.set_owner(True); w.continue_owner()
        w.select_disk(w.selectable[0].path); w.continue_pick()
        w.set_confirm_input('WRONG-TOKEN'); w.continue_confirm()
        assert w.screen == Screen.CONFIRM
        blocked(w); counts['wrong_token_refusals'] += 1
        w.set_confirm_input(w.confirm.token); w.continue_confirm()
        w.set_method(method); w.continue_method()
        assert w.screen == Screen.LAST_CHANCE
        finish(w, clock)

assert counts['review_scenarios'] == 360 and counts['layout_scenarios'] == 63
assert counts['explicit_fake_starts'] == 423
assert not counts['native_callbacks'] and not counts['mismatches']
counts['source_sha256'] = {name: hashlib.sha256((Path('/workspace/beamo-wipe')/name).read_bytes()).hexdigest()
    for name in ('src/beamo_wipe/wizard.py', 'src/beamo_wipe/keyboard.py', 'src/beamo_wipe/models.py', 'src/beamo_wipe/safety.py')}
Path(__file__).with_suffix('.json').write_text(json.dumps(counts, indent=2)+'\n')
print(json.dumps(counts))
