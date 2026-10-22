"""Owned finite process tree for output-drain tests; no inventory or device I/O."""
import subprocess
import sys
import time

mode = sys.argv[1]
if mode == 'normal':
    print('normal-output', flush=True)
elif mode == 'direct-timeout':
    print('before-timeout', flush=True)
    time.sleep(1.2)
else:
    streams = {}
    if mode == 'stdout':
        streams['stderr'] = subprocess.DEVNULL
    elif mode == 'stderr':
        streams['stdout'] = subprocess.DEVNULL
    elif mode != 'both':
        raise ValueError('unknown fixture mode')
    # This descendant only retains a pipe and then exits. It cannot perform
    # actions after the short sleep; no detached indefinite worker is created.
    subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(1.2)'], **streams)
    print('parent-finished', flush=True)
