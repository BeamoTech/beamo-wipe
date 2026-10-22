"""A new child on the covering mount remains reachable above old submounts."""
from pathlib import Path
import pytest
from beamo_wipe import discover as discovery
from beamo_wipe import safety

@pytest.mark.parametrize('log', [False,True], ids=['live','log'])
def test_new_child_above_cover_is_visible(tmp_path,monkeypatch,log):
    parent,old_sub,child=('/tmp','/tmp/beamo-wipe','/tmp/beamo-wipe/logs') if log else ('/run','/run/live','/run/live/medium')
    fs,source=('tmpfs','tmpfs') if log else ('iso9660','/dev/sdz1')
    table=(
        '101 0 0:1 / / rw - overlay overlay rw\n'
        f'7 101 0:7 / {parent} rw - tmpfs tmpfs rw\n'
        f'13 7 8:13 / {old_sub} rw - ext4 /dev/sdb1 rw\n'
        f'9 7 0:9 / {parent} rw - tmpfs tmpfs rw\n'
        f'42 9 0:42 / {child} rw - {fs} {source} rw\n'
    )
    if log:
        path=tmp_path/'mountinfo';path.write_text(table)
        monkeypatch.setattr(discovery,'MOUNTINFO_PATH',str(path))
        assert safety.log_location_is_tmpfs(Path(child)/'engine.log')
    else:
        assert discovery.live_medium_is_mounted(text=table)
