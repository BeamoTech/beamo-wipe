"""A recovery journal replaced after open cannot supply stale state."""
import os
from pathlib import Path
import pytest
from beamo_wipe import session_recovery as recovery
from beamo_wipe.session_recovery import SessionStore, NAME

BOOT='00000000-0000-0000-0000-000000000001'
BUILD='a'*64

@pytest.mark.parametrize('change',['unchanged','replace','symlink'])
def test_recovery_open_binds_current_journal_name(tmp_path,monkeypatch,change):
    effects=[]
    def forbidden(*a,**kw):
        effects.append(True)
        raise AssertionError('Native effect reached')
    for target in ['subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown']:
        monkeypatch.setattr(target,forbidden)
    directory=tmp_path/'private'
    first=SessionStore(directory,boot=BOOT,build=BUILD).open()
    first.close()
    journal=directory/NAME
    archived=directory/'saved-old-journal'
    foreign=tmp_path/'foreign-journal'
    foreign.write_bytes(b'corrupt replacement journal')
    foreign.chmod(0o600)
    real_open=os.open
    changed=[]
    def open_then_replace(path,*args,**kwargs):
        fd=real_open(path,*args,**kwargs)
        if path==NAME and not changed:
            changed.append(True)
            if change!='unchanged':
                journal.rename(archived)
                if change=='replace':
                    journal.write_bytes(foreign.read_bytes())
                    journal.chmod(0o600)
                else:
                    journal.symlink_to(foreign)
        return fd
    monkeypatch.setattr(recovery.os,'open',open_then_replace)
    store=SessionStore(directory,boot=BOOT,build=BUILD)
    try:
        store.open()
        assert changed
        assert store.invalid is (change!='unchanged'), ('replaced journal supplied stale preflight',store.record)
        assert not effects
    finally:
        store.close()
