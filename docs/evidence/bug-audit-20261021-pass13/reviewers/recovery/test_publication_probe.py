import os
from pathlib import Path
import pytest
from beamo_wipe import evidence
from beamo_wipe.safety import SafetyError

@pytest.mark.parametrize('mutation', ['normal','rewrite','mode','hardlink'])
def test_publication_binds_exact_private_inode_bytes(tmp_path, monkeypatch, mutation):
    target = tmp_path/'result.json'
    original_link = os.link
    touched = []
    def publish(source, destination, *args, **kwargs):
        touched.append(source)
        fd = kwargs['src_dir_fd']
        if mutation == 'rewrite':
            changed = os.open(source, os.O_WRONLY|os.O_TRUNC, dir_fd=fd)
            try:
                os.write(changed, b'foreign')
            finally:
                os.close(changed)
        elif mutation == 'mode':
            os.chmod(source, 0o644, dir_fd=fd)
        elif mutation == 'hardlink':
            original_link(source, 'foreign-link', src_dir_fd=fd, dst_dir_fd=fd)
        return original_link(source, destination, *args, **kwargs)
    monkeypatch.setattr(os, 'link', publish)
    if mutation == 'normal':
        identity = evidence._atomic_write_bytes(target, b'original')
        assert identity == (target.stat().st_dev, target.stat().st_ino)
        assert target.read_bytes() == b'original'
        assert target.stat().st_mode & 0o777 == 0o600
        assert target.stat().st_nlink == 1
    else:
        with pytest.raises((SafetyError, OSError)):
            evidence._atomic_write_bytes(target, b'original')
    assert touched
