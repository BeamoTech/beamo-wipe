"""Public entry must not expose live controls without recovery ownership."""
import builtins
import io
import json
import os
from types import SimpleNamespace

import pytest
from beamo_wipe import app, discover, safety, session_recovery, report_intent
from beamo_wipe.models import Disk, DiskKind, DiscoveryResult
from beamo_wipe.nwipe_runner import NwipeRunner
from beamo_wipe.wizard import Wizard


@pytest.fixture
def machine(monkeypatch):
    calls=[];observed=[];effects=[];reads={'cmdline':0,'mountinfo':0}
    mode={'fault':None,'live':True}
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
    monkeypatch.delenv('BEAMO_WIPE_LIVE',raising=False)
    monkeypatch.delenv('BEAMO_WIPE_DEMO',raising=False)
    monkeypatch.setattr(safety.sys,'platform','linux')
    monkeypatch.setattr(app,'running_on_live_usb',safety.running_on_live_usb)
    original=builtins.open
    def fake_proc(path,*args,**kwargs):
        location={'/proc/cmdline':'cmdline',discover.MOUNTINFO_PATH:'mountinfo'}.get(str(path))
        if location:
            reads[location]+=1
            if mode['fault']==location and reads[location]==1:
                calls.append(location+'-OSError')
                raise OSError('fake transient proc read')
            if location=='cmdline':return io.StringIO('boot=live quiet' if mode['live'] else 'quiet')
            return io.StringIO('1 0 0:1 / / rw - overlay overlay rw\n2 1 8:241 / /run/live/medium rw - iso9660 /dev/sdz1 rw\n')
        if str(path).startswith(('/dev/','/proc/','/sys/')):
            effects.append(str(path));raise AssertionError('native path forbidden')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(builtins,'open',fake_proc)
    realpath=os.path.realpath
    monkeypatch.setattr(os.path,'realpath',lambda p,*a,**k:str(p) if str(p).startswith('/dev/') else realpath(p,*a,**k))
    def forbidden(*args,**kwargs):effects.append('native callback');raise AssertionError('native callback forbidden')
    for name in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
                 'beamo_wipe.discover._run_findmnt','beamo_wipe.discover.read_mount_sources'):
        monkeypatch.setattr(name,forbidden)
    monkeypatch.setattr(NwipeRunner,'start',forbidden)
    monkeypatch.setattr(app,'_shutdown',forbidden)
    monkeypatch.setattr(app.signal,'signal',lambda *a:None)
    monkeypatch.setattr('beamo_wipe.diagnostics.log_diag',lambda *a,**k:None)
    monkeypatch.setattr('beamo_wipe.diagnostics.emit_serial_marker',lambda *a,**k:None)
    boot=Disk('/dev/sdz','sdz','Fake boot','BOOT',16_000_000_000,'16',DiskKind.SSD,'USB','',is_boot=True,mountpoints=('/run/live/medium',))
    target=Disk('/dev/sda','sda','Fake target','TARGET',128_000_000_000,'128',DiskKind.SSD,'SATA','')
    inventory=DiscoveryResult(disks=(boot,target),selectable=(target,),boot=boot,boot_identified=True)
    def fake_discover(**kwargs):calls.append('fake-discovery');return inventory
    monkeypatch.setattr(app,'discover',fake_discover)
    # Keep the real builder and entry/session code, use synchronous stages to
    # avoid unrelated worker timing, and stop at the real console boundary.
    monkeypatch.setattr(app,'_build_wizard_with_console_stages',app._build_wizard)
    class Store:
        previous=False;invalid=False
        def __init__(self):calls.append('store-created')
        def open(self):calls.append('store-open')
        def close(self):calls.append('store-close')
    monkeypatch.setattr(session_recovery,'SessionStore',Store)
    monkeypatch.setattr(report_intent,'ReportIntentStore',lambda:object())
    monkeypatch.setattr(Wizard,'enable_report_intent_recovery',lambda self,store:calls.append('report-intent'))
    def ui(wizard):
        observed.append({'dry_run':wizard.dry_run,'runner':type(wizard.runner).__name__,
                         'has_session_store':wizard._session_store is not None})
        return 23
    monkeypatch.setattr('beamo_wipe.ui.console_wizard.run_console',ui)
    result=SimpleNamespace(mode=mode,calls=calls,observed=observed,reads=reads,effects=effects)
    yield result
    assert effects==[]


@pytest.mark.parametrize('location',['cmdline','mountinfo'])
def test_transient_initial_proc_read_cannot_dispatch_unowned_live_wizard(machine,location,request):
    machine.mode['fault']=location
    code=app.main(['--console','--dry-run'])
    request.node.user_properties.append(('trace',json.dumps({'fault':location,'code':code,'calls':machine.calls,'reads':machine.reads,'ui':machine.observed,'native_callbacks':len(machine.effects)})))
    assert code==3
    assert machine.observed==[]


def test_stable_live_session_preserves_owned_real_wizard(machine):
    assert app.main(['--console','--dry-run'])==23
    assert machine.observed==[{'dry_run':False,'runner':'NwipeRunner','has_session_store':True}]
    assert machine.calls[:2]==['store-created','store-open']
    assert machine.calls[-1]=='store-close'


def test_desktop_preview_preserves_unowned_fake_wizard(machine):
    machine.mode['live']=False
    assert app.main(['--console','--demo'])==23
    assert machine.observed==[{'dry_run':True,'runner':'DryRunRunner','has_session_store':False}]
    assert 'store-created' not in machine.calls
