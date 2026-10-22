"""External PASS12 model: finished fake results, end-session event words.

No GUI is imported; all process, inventory, sound and power boundaries refuse.
Counts supplement canonical pytest IDs and are not new canonical test cases.
"""
from pathlib import Path
from dataclasses import dataclass
from itertools import product
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import sys
import threading
from unittest.mock import patch

ROOT = Path('/workspace/beamo-wipe')
OUT = Path(__file__).parent
sys.path.insert(0, str(ROOT / 'tests'))
from test_result_presentations import CASES, case_evidence
from test_erase_another import saved
from beamo_wipe.models import Screen

effects = []
def forbidden(*args, **kwargs):
    effects.append(True)
    raise AssertionError('Native side effect forbidden in terminal handoff model')

counts = Counter()
@dataclass
class Model:
    wanted: bool
    saved: bool
    prompt: bool = False
    pending: bool = False
    shutdown: bool = False
    new_session: bool = False
    generation: int = 0
    def event(self, name):
        if name == 'shutdown':
            if self.shutdown or self.new_session or self.prompt:
                return
            if self.wanted and not self.saved:
                self.prompt = True
                self.generation += 1
            else:
                self.shutdown = True
        elif name == 'another':
            if self.prompt or self.shutdown or self.new_session:
                return
            self.pending = True
            if not self.saved:
                self.prompt = True
                self.generation += 1
            else:
                self.new_session = True
        elif name == 'keep':
            if self.prompt and not self.shutdown:
                self.prompt = self.pending = False
        elif name == 'confirm':
            if self.prompt and not self.shutdown and not self.new_session:
                if self.pending:
                    self.new_session = True
                else:
                    self.shutdown = True
        elif name == 'old':
            pass  # generation zero is never a current confirmation
        elif name == 'tick':
            pass

def apply(w, event):
    if event == 'shutdown': w.shutdown()
    elif event == 'another': w.erase_another_disk()
    elif event == 'keep': w.keep_report_session()
    elif event == 'confirm': w.confirm_shutdown_without_saving(w.shutdown_generation)
    elif event == 'old': w.confirm_shutdown_without_saving(0)
    elif event == 'tick': w.tick()

def observe(w):
    return (w.screen == Screen.SHUTDOWN_CONFIRM, w._new_session_pending,
            w.wants_shutdown, w.wants_new_session, w.shutdown_generation)

def expected(m):
    return (m.prompt, m.pending, m.shutdown, m.new_session, m.generation)

boundaries = ['subprocess.run', 'subprocess.Popen',
              'beamo_wipe.discover.run_lsblk', 'beamo_wipe.discover.read_cmdline',
              'beamo_wipe.discover.read_mount_sources',
              'beamo_wipe.nwipe_runner.NwipeRunner.start', 'beamo_wipe.app._shutdown',
              'beamo_wipe.sound._run', 'beamo_wipe.sound._popen']
patches = [patch(name, forbidden) for name in boundaries]
for p in patches: p.start()
try:
    words = list(product(('shutdown', 'another', 'keep', 'confirm', 'old', 'tick'), repeat=3))
    words += [('another', 'keep', 'another', 'old', 'confirm', 'confirm'),
              ('shutdown', 'keep', 'another', 'old', 'confirm', 'tick'),
              ('another', 'keep', 'shutdown', 'old', 'confirm', 'another')]
    for case, wanted, receipt, word in product(CASES, (False, True), (False, True), words):
        w, _, _ = case_evidence(case)
        w.report_wanted = wanted
        if receipt: saved(w)
        m = Model(wanted, receipt)
        original_result = w.wipe_result
        for event in word:
            before = observe(w)
            apply(w, event); m.event(event)
            assert observe(w) == expected(m), (case[0], wanted, receipt, word, event, observe(w), expected(m))
            assert w.wipe_result is original_result
            assert not w.runner.started
            assert not (w.wants_shutdown and w.wants_new_session)
            counts['events'] += 1
            if event == 'old': counts['stale_confirmation_refusals'] += 1
            if observe(w) == before: counts['no_transition_controls'] += 1
        counts['scenarios'] += 1
        counts['shutdown_positive_controls'] += int(w.wants_shutdown)
        counts['new_session_positive_controls'] += int(w.wants_new_session)
    # Every transient busy flag blocks initial admission and the current prompt.
    for case, busy, action in product(CASES, ('_report_exporting', '_evidence_saving', '_diagnostic_busy', '_finishing'), ('shutdown', 'another')):
        w, _, _ = case_evidence(case); w.report_wanted = True
        setattr(w, busy, True); apply(w, action)
        assert w.screen == Screen.DONE and not w.wants_shutdown and not w.wants_new_session
        counts['busy_admission_refusals'] += 1
        setattr(w, busy, False); apply(w, action)
        assert w.screen == Screen.SHUTDOWN_CONFIRM
        generation = w.shutdown_generation
        setattr(w, busy, True); w.confirm_shutdown_without_saving(generation)
        assert not w.wants_shutdown and not w.wants_new_session
        counts['busy_confirmation_refusals'] += 1
        setattr(w, busy, False); w.confirm_shutdown_without_saving(generation)
        assert w.wants_shutdown != w.wants_new_session
        counts['restored_positive_controls'] += 1
    # Fresh harmless Python threads race only public end-session admissions.
    for repeat, wanted, receipt in product(range(16), (False, True), (False, True)):
        w, _, _ = case_evidence(CASES[repeat % len(CASES)])
        w.report_wanted = wanted
        if receipt: saved(w)
        barrier = threading.Barrier(3)
        def invoke(event):
            barrier.wait(timeout=3); apply(w, event)
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(invoke, e) for e in ('shutdown', 'another', 'another')]
            for f in futures: f.result(timeout=5)
        assert not (w.wants_shutdown and w.wants_new_session)
        assert w.shutdown_generation <= 1
        if w.screen == Screen.SHUTDOWN_CONFIRM:
            w.confirm_shutdown_without_saving(w.shutdown_generation)
        assert w.wants_shutdown != w.wants_new_session
        counts['concurrent_admission_scenarios'] += 1
    assert not effects
finally:
    for p in reversed(patches): p.stop()
sources = ['src/beamo_wipe/wizard.py', 'src/beamo_wipe/models.py', 'src/beamo_wipe/demo.py',
           'src/beamo_wipe/app.py', 'src/beamo_wipe/ui/tk_wizard.py',
           'src/beamo_wipe/ui/accessible_wizard.py', 'src/beamo_wipe/ui/console_wizard.py',
           'tests/test_result_presentations.py', 'tests/test_erase_another.py']
result = {'counts': dict(counts), 'mismatches': 0, 'native_callbacks': len(effects),
          'source_sha256': {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in sources},
          'model_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'limits': ['fake terminal result sessions only', 'no GUI import or native renderer event loop',
                     'concurrent admission checks support product invariants; not canonical pytest cases']}
(OUT/'terminal_handoff_model.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps(result, indent=2))
