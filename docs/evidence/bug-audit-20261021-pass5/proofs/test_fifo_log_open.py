"""An invalid replacement log must be rejected before a blocking FIFO open."""
import multiprocessing
import os
from pathlib import Path
import time

import pytest


def _child(folder, replace_with_fifo, ready, done, outcomes):
    from beamo_wipe import nwipe_runner as runner_module, safety
    from beamo_wipe.models import MethodId, WipeRequest

    directory = Path(folder)
    log = directory / 'owned-engine.log'
    process = type('FakeProcess', (), {'returncode': None})()
    runner = runner_module.NwipeRunner(binary=str(directory / 'fake-engine'))
    calls = []
    armed = False
    actual_guard = safety.assert_log_not_on_target
    actual_truncate = runner_module.truncate_log_file

    def forbidden(*_args, **_kwargs):
        raise AssertionError('Native device/process effect reached')

    def guarded_log(path, target, **kwargs):
        actual_guard(path, target, **kwargs)
        if armed:
            assert runner._lock_fd is not None
            assert Path(path).is_file()
            if replace_with_fifo:
                Path(path).unlink()
                os.mkfifo(path, 0o600)
            ready.set()

    def truncate(*args, **kwargs):
        nonlocal armed
        armed = True
        try:
            return actual_truncate(*args, **kwargs)
        finally:
            armed = False

    def fake_spawn(*_args, **_kwargs):
        calls.append('fake spawn')
        return process

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv('BEAMO_WIPE_DRY_RUN', '1')
        patch.delenv('BEAMO_WIPE_LIVE', raising=False)
        patch.setattr(safety, 'default_log_dir', lambda: directory)
        patch.setattr(safety, 'assert_log_not_on_target', guarded_log)
        patch.setattr(runner_module, 'truncate_log_file', truncate)
        patch.setattr(runner_module, 'assert_not_boot', lambda *_a, **_kw: None)
        patch.setattr(runner_module.subprocess, 'Popen', fake_spawn)
        patch.setattr(runner_module.subprocess, 'run', forbidden)
        patch.setattr(runner_module, 'pinned_nwipe_already_running', forbidden)
        patch.setattr('beamo_wipe.discover.run_lsblk', forbidden)
        patch.setattr('beamo_wipe.discover.read_mount_sources', forbidden)
        patch.setattr('beamo_wipe.discover.read_cmdline', forbidden)
        patch.setattr(runner_module, '_try_log_diag', lambda *_a: None)
        try:
            request = WipeRequest('/dev/sda', MethodId.EVERYDAY, '/dev/sr0', str(log))
            runner.start(request)
            outcome = {'result': 'started_fake', 'spawn_calls': len(calls)}
        except BaseException as exc:
            outcome = {'result': type(exc).__name__, 'message': str(exc),
                       'spawn_calls': len(calls)}
        finally:
            runner._release_wipe_lock()
        outcome['lock_released'] = runner._lock_fd is None
        outcomes.put(outcome)
        done.set()


@pytest.mark.parametrize('replace_with_fifo', [False, True], ids=['regular-control', 'fifo-replacement'])
def test_runner_refuses_invalid_log_without_waiting_for_a_reader(tmp_path, replace_with_fifo):
    # This directory, ordinary file, FIFO and helper are owned test fixtures.
    # The helper never receives an actual engine, disk or mount callback.
    log = tmp_path / 'owned-engine.log'
    log.write_bytes(b'ordinary prior log')
    log.chmod(0o600)
    context = multiprocessing.get_context('fork')
    ready, done, outcomes = context.Event(), context.Event(), context.Queue()
    child = context.Process(target=_child, args=(str(tmp_path), replace_with_fifo, ready, done, outcomes))
    child.start()
    completed_before_reader = False
    reader = None
    try:
        assert ready.wait(5), 'helper did not reach validated log boundary'
        started = time.monotonic()
        completed_before_reader = done.wait(1)
        elapsed = time.monotonic() - started
        if not completed_before_reader and replace_with_fifo:
            # Release only this owned FIFO. fstat can now reject it and run
            # cleanup; no arbitrary process or host operation is targeted.
            reader = os.open(log, os.O_RDONLY | os.O_NONBLOCK)
        child.join(5)
        assert not child.is_alive()
        assert child.exitcode == 0
        outcome = outcomes.get(timeout=2)
        print({'replacement': replace_with_fifo, 'completed_before_reader': completed_before_reader,
               'wait_seconds': elapsed, 'outcome': outcome})
        assert completed_before_reader, 'validated log replaced by FIFO blocks runner.start while holding wipe lock'
        assert outcome['lock_released']
        if replace_with_fifo:
            assert outcome['result'] == 'SafetyError' and outcome['spawn_calls'] == 0
        else:
            assert outcome['result'] == 'started_fake' and outcome['spawn_calls'] == 1
            assert log.read_bytes() == b''
    finally:
        if reader is not None:
            os.close(reader)
        if child.is_alive():
            child.terminate()
            child.join(5)
        outcomes.close()
