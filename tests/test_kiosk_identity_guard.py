"""Exercise the shipped kiosk's Python absence decision with inert imports."""
import re
from pathlib import Path
from types import SimpleNamespace
import unittest


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


class KioskIdentityGuardTests(unittest.TestCase):
    def test_only_explicit_absence_allows_power(self):
        for value in (False, True, None, 0, 1, '', 'False'):
            with self.subTest(value=value):
                with self.assertRaises(SystemExit) as caught:
                    decision(probe=lambda: value)
                self.assertEqual(caught.exception.code, 0 if value is False else 1)

    def test_inspection_and_import_failures_cannot_succeed(self):
        for error in (OSError('unreadable'), RuntimeError('inspection failed'), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                def failed():
                    raise error
                with self.assertRaises(type(error)):
                    decision(probe=failed)
        with self.assertRaises(ImportError):
            decision(import_error=ImportError('unavailable'))
