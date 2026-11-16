"""Exercise the shipped kiosk's Python absence decision with inert imports."""
import re
from pathlib import Path
from types import SimpleNamespace

import pytest


KIOSK = Path(__file__).resolve().parents[1] / 'packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk'


def decision(probe=None, import_error=None):
    text = KIOSK.read_text()
    power = text.split('power_choice() {', 1)[1].split('\n}\n', 1)[0]
    match = re.search(r"python3 -I -c '([^']+)'", power)
    assert match, 'The kiosk must inspect pinned executable identity before power'
    assert power.index(match.group(0)) < power.index('systemctl --no-block "$1"')

    def fake_import(name, *_args, **_kwargs):
        assert name == 'beamo_wipe.nwipe_runner'
        if import_error:
            raise import_error
        return SimpleNamespace(pinned_nwipe_already_running=probe)

    # This is the exact trusted inline Python; its only import is replaced.
    env = {'__builtins__': {'__import__': fake_import, 'SystemExit': SystemExit}}
    exec(compile(match.group(1), str(KIOSK), 'exec'), env)  # noqa: S102


@pytest.mark.parametrize("value", (False, True, None, 0, 1, '', 'False'))
def test_only_explicit_absence_allows_power(value):
    with pytest.raises(SystemExit) as caught:
        decision(probe=lambda: value)
    assert caught.value.code == (0 if value is False else 1)


@pytest.mark.parametrize(
    "error",
    (OSError('unreadable'), RuntimeError('inspection failed'), KeyboardInterrupt()),
    ids=lambda error: type(error).__name__,
)
def test_inspection_failures_cannot_succeed(error):
    def failed():
        raise error
    with pytest.raises(type(error)):
        decision(probe=failed)


def test_import_failure_cannot_succeed():
    with pytest.raises(ImportError):
        decision(import_error=ImportError('unavailable'))
