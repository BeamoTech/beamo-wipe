"""PASS10: typed live-source identity laws using only synthetic inventories.

The strict resolver requires a real device-link identity (supplied by a fake
realpath provider). Injected preview discovery deliberately allows a missing
by-* link, while a present conflicting link still refuses. No native I/O.
"""
from pathlib import Path
import builtins
import copy
import hashlib
import io
import itertools
import json
import os
import sys
import tempfile

from pytest import MonkeyPatch

sys.path.insert(0, '/workspace/beamo-wipe/src')
from beamo_wipe import app, discover as D, nwipe_runner, safety as S

ROOT = Path(__file__).parent
metrics = {'states': 0, 'strict_resolver_calls': 0, 'parsed_strict_results': 0,
           'public_fake_discovery_calls': 0, 'strict_successes': 0,
           'strict_refusals': 0, 'fake_successes': 0, 'fake_refusals': 0,
           'missing_link_policy_controls': 0, 'selectable_target_observations': 0,
           'native_callbacks': 0, 'mismatches': []}
identifiers = {
    'LABEL': ('label', 'by-label'), 'PARTLABEL': ('partlabel', 'by-partlabel'),
    'UUID': ('uuid', 'by-uuid'), 'PARTUUID': ('partuuid', 'by-partuuid'),
}
label_values = ['Beamo Wipe', 'LIVE[West]', ' Live Value ', 'Live=USB', 'Caf\u00e9-USB', "Alpha'Beta"]
uuid_values = ['ABCD-1234', 'ABCDEF01-2345-6789-ABCD-EF0123456789',
               '12AB-34CD', 'BOOT-ID-0001', '0000-ABCD', 'A1B2C3D4']


def encoded(value):
    # udev preserves valid Unicode and escapes punctuation/whitespace bytes.
    return ''.join('\\x%02x' % ord(c) if c in " []='\"\\" else c for c in value)


def disk(name, size, bus, serial, child):
    return {'name': name, 'path': '/dev/' + name, 'type': 'disk', 'size': size,
            'tran': bus, 'serial': serial, 'model': 'Fake ' + name, 'ro': False,
            'rota': False, 'mountpoints': [], 'children': [child]}


def part(name, parent):
    return {'name': name, 'path': '/dev/' + name, 'type': 'part', 'pkname': parent,
            'size': 1_000_000_000, 'mountpoints': [], 'fstype': 'ext4'}


def check_result(result, success):
    if success:
        assert result.boot_identified and result.boot is not None
        assert result.boot.path == '/dev/sdz' and not result.error
        assert {d.path for d in S.selectable_disks(result)} == {'/dev/sda'}
        S.assert_boot_excluded(result)
        metrics['selectable_target_observations'] += 1
    else:
        assert not result.boot_identified and not result.selectable


with MonkeyPatch.context() as patch, tempfile.TemporaryDirectory(prefix='pass10-typed-source-') as folder:
    patch.setenv('BEAMO_WIPE_DRY_RUN', '1')
    patch.delenv('BEAMO_WIPE_LIVE', raising=False)
    alias_state = {'path': '', 'target': ''}
    original_realpath = os.path.realpath

    def realpath(path, *args, **kwargs):
        value = os.fsdecode(path)
        if value == alias_state['path'] and alias_state['target']:
            return alias_state['target']
        if value.startswith(('/dev/', '/sys/', '/proc/')):
            return value
        return original_realpath(path, *args, **kwargs)

    patch.setattr(os.path, 'realpath', realpath)

    def forbidden(*args, **kwargs):
        metrics['native_callbacks'] += 1
        raise AssertionError('Native callback forbidden')

    for name in ('subprocess.run', 'subprocess.Popen', 'beamo_wipe.discover.run_lsblk',
                 'beamo_wipe.discover._run_findmnt', 'beamo_wipe.discover.read_cmdline',
                 'beamo_wipe.discover.read_mount_sources'):
        patch.setattr(name, forbidden)
    patch.setattr(app, '_shutdown', forbidden)
    patch.setattr(nwipe_runner.NwipeRunner, 'start', forbidden)
    patch.setattr('beamo_wipe.diagnostics.log_diag', lambda *a, **k: None)
    patch.setattr('beamo_wipe.diagnostics.emit_serial_marker', lambda *a, **k: None)
    patch.setattr(S, 'default_log_dir', lambda: Path(folder))

    def guarded(fn):
        def wrapped(path, *args, **kwargs):
            if not isinstance(path, int):
                value = os.fsdecode(path)
                if value.startswith(('/dev/', '/proc/', '/sys/')):
                    return forbidden()
            return fn(path, *args, **kwargs)
        return wrapped

    for obj, name in ((builtins, 'open'), (io, 'open'), (os, 'open')):
        patch.setattr(obj, name, guarded(getattr(obj, name)))
    original_lstat = os.lstat

    def fake_lstat(path, *args, **kwargs):
        if os.fsdecode(path).startswith(('/dev/', '/sys/', '/proc/')):
            raise FileNotFoundError('Synthetic node has no host backing')
        return original_lstat(path, *args, **kwargs)

    patch.setattr(os, 'lstat', fake_lstat)
    original_stat = os.stat

    def fake_stat(path, *args, **kwargs):
        if not isinstance(path, int) and os.fsdecode(path).startswith(('/dev/', '/sys/', '/proc/')):
            raise FileNotFoundError('Synthetic node has no host backing')
        return original_stat(path, *args, **kwargs)

    patch.setattr(os, 'stat', fake_stat)
    for key, shape, reverse, scenario, form in itertools.product(
        identifiers, ('tree', 'flat'), (False, True),
        ('unique', 'same-casefold', 'same-exact', 'orphan', 'loop', 'link-foreign', 'link-missing'),
        ('plain-upper', 'plain-lower', 'double-quoted', 'single-quoted', 'by-link'),
    ):
        for value in (uuid_values if key in {'UUID', 'PARTUUID'} else label_values):
            field, link_kind = identifiers[key]
            boot_part, target_part = part('sdz1', 'sdz'), part('sda1', 'sda')
            boot_part[field] = value
            target_part[field] = 'Different-' + value
            if scenario == 'same-exact':
                target_part[field] = value
            elif scenario == 'same-casefold':
                target_part[field] = value.swapcase()
            rows = [disk('sdz', 16_000_000_000, 'usb', 'BOOT-FAKE', boot_part),
                    disk('sda', 500_000_000_000, 'sata', 'TARGET-FAKE', target_part)]
            if shape == 'flat':
                rows += [rows[0].pop('children')[0], rows[1].pop('children')[0]]
            if scenario == 'orphan':
                orphan = part('sdq1', 'sdq')
                orphan[field] = value
                rows.append(orphan)
            elif scenario == 'loop':
                rows.append({'name': 'loop77', 'path': '/dev/loop77', 'type': 'loop',
                             'size': 1_000_000_000, field: value})
            if reverse:
                rows.reverse()
            alias = '/dev/disk/' + link_kind + '/' + encoded(value)
            alias_state.update(path=alias, target=('/dev/sda1' if scenario == 'link-foreign'
                                                  else '' if scenario == 'link-missing' else '/dev/sdz1'))
            sources = {'plain-upper': key + '=' + value, 'plain-lower': key.lower() + '=' + value,
                       'double-quoted': key + '="' + value + '"',
                       'single-quoted': key + "='" + value + "'", 'by-link': alias}
            source = sources[form]
            unique = scenario not in {'same-exact', 'orphan', 'loop'}
            if scenario == 'same-casefold' and key in {'UUID', 'PARTUUID'}:
                unique = False
            strict_ok = unique and not (form == 'by-link' and scenario in {'link-foreign', 'link-missing'})
            fake_ok = unique and not (form == 'by-link' and scenario == 'link-foreign')
            metrics['states'] += 1
            resolved = D.identify_boot_path(copy.deepcopy(rows), mount_sources=[source],
                                            cmdline='boot=live', require_device_link=True)
            metrics['strict_resolver_calls'] += 1
            assert resolved == ('/dev/sdz' if strict_ok else None), (key, value, shape, reverse, scenario, form, resolved)
            strict = D.parse_lsblk_json({'blockdevices': copy.deepcopy(rows)}, boot_path=resolved)
            metrics['parsed_strict_results'] += 1
            check_result(strict, strict_ok)
            result = D.discover(lsblk_payload={'blockdevices': copy.deepcopy(rows)},
                                mount_sources=[source], cmdline='boot=live',
                                env={'BEAMO_WIPE_DRY_RUN': '1'})
            metrics['public_fake_discovery_calls'] += 1
            check_result(result, fake_ok)
            metrics['strict_successes' if strict_ok else 'strict_refusals'] += 1
            metrics['fake_successes' if fake_ok else 'fake_refusals'] += 1
            if strict_ok != fake_ok:
                metrics['missing_link_policy_controls'] += 1

assert metrics['strict_successes'] > 0 and metrics['strict_refusals'] > 0
assert metrics['missing_link_policy_controls'] > 0 and metrics['native_callbacks'] == 0
metrics['source_sha256'] = {str(p.relative_to('/workspace/beamo-wipe')): hashlib.sha256(p.read_bytes()).hexdigest()
                           for p in (Path('/workspace/beamo-wipe/src/beamo_wipe') / name
                                     for name in ('discover.py', 'safety.py', 'models.py'))}
metrics['scope'] = 'Synthetic typed-source/alias conflict and strict-versus-preview identity laws; no native platform qualification.'
(ROOT / 'typed-source-contract-matrix.json').write_text(json.dumps(metrics, indent=2) + '\n')
print(json.dumps(metrics, sort_keys=True))
