"""One valid contrary WWN must not erase a malformed candidate's uncertainty."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path.cwd() / 'tests'))
from test_unresolved_physical_bridge_pass17 import _disk, scan_fake  # noqa: E402,F401


@pytest.mark.parametrize('bad', ('bad\nwwn', 'X' * 129, 7, ['FAKE-WWN']))
@pytest.mark.parametrize('reverse', (False, True))
@pytest.mark.parametrize('nested', (False, True))
@pytest.mark.parametrize('mode', ('protected', 'unrelated', 'authoritative'))
def test_malformed_wwn_retains_an_unknown_alias_candidate(scan_fake, bad, reverse, nested, mode):
    boot = _disk('sdz', tran='usb', size=16_000_000_000,
                 serial='ROOT-SERIAL', wwn='0x50014ee20aa00001')
    values = [('OTHER-SERIAL' if mode == 'unrelated' else 'ROOT-SERIAL', '0x50014ee20aa00002'),
              ('LEAF-SERIAL', bad)]
    if reverse:
        values.reverse()
    children = []
    for index, (serial, wwn) in enumerate(values, 1):
        part = dict(name=f'sda{index}', path=f'/dev/sda{index}', type='part',
                    pkname='sda', size=1_000_000_000, mountpoints=[])
        if nested:
            part['children'] = [dict(name=f'fake_wwn_{index}', path=f'/dev/mapper/fake_wwn_{index}',
                                     type='crypt', pkname=part['name'], mountpoints=[],
                                     serial=serial, wwn=wwn)]
        else:
            part.update(serial=serial, wwn=wwn)
        children.append(part)
    bridge = _disk('sda', children=children)
    if mode == 'authoritative':
        bridge['wwn'] = '0x50014ee20aa00002'
    leaf = _disk('sdc', serial='LEAF-SERIAL')
    unrelated = _disk('sdb', serial='FAKE-UNRELATED')
    result = scan_fake([boot, bridge, leaf, unrelated])
    paths = {disk.path for disk in result.selectable}
    if mode == 'protected':
        assert leaf['path'] not in paths
    else:
        assert result.boot_identified and not result.error
        assert leaf['path'] in paths and unrelated['path'] in paths
