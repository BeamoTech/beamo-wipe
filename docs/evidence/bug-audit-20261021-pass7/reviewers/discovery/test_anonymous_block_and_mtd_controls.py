"""Narrow supplemental controls for anonymous block superblocks and MTD/FUSE refusal."""
import pytest
from beamo_wipe import discover as D


@pytest.fixture(autouse=True)
def no_native_reads_or_processes(monkeypatch):
    def forbidden(*_args, **_kwargs):
        raise AssertionError('Pure provided-text check attempted native I/O')
    monkeypatch.setattr('builtins.open', forbidden)
    monkeypatch.setattr('subprocess.run', forbidden)
    monkeypatch.setattr('subprocess.Popen', forbidden)


@pytest.mark.parametrize('filesystem', ['btrfs', 'fuseblk'])
def test_anonymous_mount_device_id_does_not_disqualify_block_filesystem(filesystem):
    text = ('1 0 0:1 / / rw - overlay overlay rw\n'
            f'2 1 0:48 / /run/live/medium rw - {filesystem} /dev/sdb1 rw\n')
    assert D.live_medium_is_mounted(text=text)
    assert D.read_mountinfo_sources(text=text) == ['/dev/sdb1']


@pytest.mark.parametrize('filesystem', ['jffs2', 'fuse'])
def test_mtd_only_or_generic_fuse_type_is_not_block_proof(filesystem):
    text = ('1 0 0:1 / / rw - overlay overlay rw\n'
            f'2 1 0:48 / /run/live/medium rw - {filesystem} /dev/sdb1 rw\n')
    assert not D.live_medium_is_mounted(text=text)
    with pytest.raises(ValueError):
        D.read_mountinfo_sources(text=text)
