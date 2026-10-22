"""Run the exact regression module after an owned thread starts, warnings fatal."""
from pathlib import Path
import threading

import pytest


def main():
    folder = Path(__file__).resolve().parent
    started, stop = threading.Event(), threading.Event()

    def benign_worker():
        started.set()
        stop.wait(30)

    thread = threading.Thread(target=benign_worker, name='pass5-fifo-warning-control')
    thread.start()
    assert started.wait(5)
    try:
        assert thread.is_alive()
        return pytest.main([
            '-o', 'addopts=', '-q', '-W', 'error',
            'tests/test_log_fifo_open_pass5_20261021.py',
            '--junitxml='+str(folder / 'post-thread-spawn.xml'),
        ])
    finally:
        stop.set()
        thread.join(5)
        assert not thread.is_alive()


if __name__ == '__main__':
    raise SystemExit(main())
