"""Actual volatile stores: partial I/O, commit faults, public retries/reopens.

Only private regular files and flock are used. All native discovery/engine/
power callbacks are forbidden. This matrix is supporting evidence, not extra
canonical tests or physical filesystem qualification.
"""
from pathlib import Path
import copy, datetime, errno, hashlib, itertools, json, os, stat, sys, tempfile
from unittest.mock import patch

repo=Path('/workspace/beamo-wipe'); root=Path(__file__).parent
sys.path[:0]=[str(repo/'src'),str(repo/'tests')]
from beamo_wipe.models import MethodId
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.session_recovery import NAME, SessionStore
from beamo_wipe.safety import SafetyError
from test_session_recovery import BOOT, BUILD, armed

counts={k:0 for k in ('cases','positive_transactions','injected_refusals','precommit_old_bytes_preserved','postcommit_new_bytes_retained','postcommit_journals_block_further_save','fresh_reopen_checks','successful_retries','quiescent_controls','native_callbacks')}
mismatches=[]
contexts=[('preference',old,new) for old,new in itertools.product((False,True),repeat=2)]
contexts += [(operation, method,None) for operation in ('arm','disarm') for method in MethodId]
faults=('none','write-start','write-middle','file-sync','replace','directory-sync','readback','close')
postfaults={'directory-sync','readback','close'}

def forbidden(*args,**kwargs):
    counts['native_callbacks']+=1
    raise AssertionError('Native callback forbidden')


def one(index,context,fault,chunk):
    kind,first,new=context
    with tempfile.TemporaryDirectory(prefix='beamo-pass11-volatile-') as outer:
        directory=Path(outer)/'private'
        if kind=='preference':
            directory.mkdir(mode=0o700); store=ReportIntentStore(directory); store.save(first)
            target=directory/store.NAME; prefix='.report-intent-'
            operation=lambda:store.save(new)
            expect=b'wanted\n' if new else b'not-wanted\n'
            old=target.read_bytes()
        else:
            store=SessionStore(directory,boot=BOOT,build=BUILD).open()
            if kind=='disarm':armed(store,first)
            target=directory/NAME; prefix='.recovery-'
            old=target.read_bytes(); previous=copy.deepcopy(store.record)
            operation=(lambda:armed(store,first)) if kind=='arm' else store.disarm_unstarted
            expected_phase='armed' if kind=='arm' else 'preflight'
        tracked=set(); fired=[]; state={'published':False,'writes':0}
        actual={name:getattr(os,name) for name in ('open','write','pread','fsync','replace','close')}
        def inject():
            fired.append(fault); raise OSError(errno.EIO,'explicit owned-fixture fault '+fault)
        def opened(path,flags,*args,**kwargs):
            fd=actual['open'](path,flags,*args,**kwargs)
            if str(path).startswith(prefix):tracked.add(fd)
            return fd
        def wrote(fd,data):
            if fd in tracked:
                state['writes']+=1
                if fault=='write-start' and state['writes']==1:inject()
                if fault=='write-middle':
                    if state['writes']==2:inject()
                    data=data[:max(1,len(data)//2)]
                if chunk:data=data[:chunk]
            return actual['write'](fd,data)
        def synced(fd):
            if fault=='file-sync' and fd in tracked:inject()
            if fault=='directory-sync' and stat.S_ISDIR(os.fstat(fd).st_mode):inject()
            return actual['fsync'](fd)
        def replaced(*args,**kwargs):
            if fault=='replace':inject()
            result=actual['replace'](*args,**kwargs);state['published']=True;return result
        def readback(fd,amount,offset):
            if fd in tracked:
                if fault=='readback' and state['published']:inject()
                if chunk:amount=min(amount,chunk)
            return actual['pread'](fd,amount,offset)
        def closed(fd):
            result=actual['close'](fd)
            if fault=='close' and fd in tracked and state['published'] and not fired:inject()
            return result
        error=None
        with patch.multiple(os,open=opened,write=wrote,pread=readback,fsync=synced,replace=replaced,close=closed):
            try:operation()
            except OSError as exc:error=exc
        if fault=='none':
            assert error is None and not fired
            counts['positive_transactions']+=1
        else:
            assert error is not None and fired==[fault],(fault,error,fired)
            counts['injected_refusals']+=1
        assert not list(directory.glob(prefix+'*'))
        actual_data=target.read_bytes()
        if fault!='none' and fault not in postfaults:
            assert actual_data==old
            counts['precommit_old_bytes_preserved']+=1
            if kind!='preference':assert not store.invalid and store.record==previous
        else:
            if kind=='preference':assert actual_data==expect
            else:assert json.loads(actual_data)['payload']['phase']==expected_phase
            if fault in postfaults:
                counts['postcommit_new_bytes_retained']+=1
                if kind!='preference':
                    assert store.invalid
                    try:store.save({})
                    except SafetyError:counts['postcommit_journals_block_further_save']+=1
                    else:raise AssertionError('uncertain postcommit journal accepted another write')
        if kind=='preference':
            # Re-open exact public preference after every successful or failed save.
            expected_before_retry=(first if fault!='none' and fault not in postfaults else new)
            assert ReportIntentStore(directory).load() is expected_before_retry
            counts['fresh_reopen_checks']+=1
            store.save(new); assert ReportIntentStore(directory).load() is new
        else:
            store.close()
            again=SessionStore(directory,boot=BOOT,build=BUILD).open()
            try:
                assert not again.invalid and again.previous
                before_phase=(previous['phase'] if fault!='none' and fault not in postfaults else expected_phase)
                assert again.record['phase']==before_phase
                counts['fresh_reopen_checks']+=1
                assert again.is_quiescent();counts['quiescent_controls']+=1
                # Old authorization is never resumed. Rotate only a proven
                # stopped session, then build a brand-new fake arm if required.
                again.begin_new_session()
                assert not again.previous and again.record['phase']=='preflight'
                if kind=='arm':armed(again,first)
                assert again.record['phase']==expected_phase
                assert not again.invalid
            finally:again.close()
        counts['successful_retries']+=1;counts['cases']+=1

started=datetime.datetime.now(datetime.timezone.utc).isoformat()
with patch('subprocess.run',forbidden),patch('subprocess.Popen',forbidden),patch('beamo_wipe.discover.run_lsblk',forbidden),patch('beamo_wipe.discover.read_cmdline',forbidden),patch('beamo_wipe.discover.read_mount_sources',forbidden),patch('beamo_wipe.nwipe_runner.NwipeRunner.start',forbidden),patch('beamo_wipe.app._shutdown',forbidden),patch('beamo_wipe.nwipe_runner.pinned_nwipe_already_running',lambda **kwargs:False):
    for index,(context,fault,chunk) in enumerate(itertools.product(contexts,faults,(None,1,7))):
        try:one(index,context,fault,chunk)
        except BaseException as exc:
            mismatches.append({'index':index,'context':list(context),'fault':fault,'chunk':chunk,'error':repr(exc)})
            raise
result={'started_utc':started,'contexts':len(contexts),'faults':list(faults),'write_read_chunk_limits':[None,1,7],'counts':counts,'mismatches':mismatches,'source_sha256':{n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in ['src/beamo_wipe/session_recovery.py','src/beamo_wipe/report_intent.py','src/beamo_wipe/models.py','src/beamo_wipe/safety.py','tests/test_session_recovery.py','tests/test_usb_report_workflow.py']},'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'physical_qualification':False}
(root/'volatile-transaction-matrix.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
