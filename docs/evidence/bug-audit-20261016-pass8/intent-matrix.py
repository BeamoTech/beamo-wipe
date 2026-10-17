"""Regular-file report-preference corruption, replacement and retry checks."""
import concurrent.futures,json,os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=['src']
from beamo_wipe.report_intent import ReportIntentStore
from beamo_wipe.safety import SafetyError
count=0
with tempfile.TemporaryDirectory(prefix='beamo-pass8-intent-') as directory:
    root=Path(directory);root.chmod(0o700);store=ReportIntentStore(root);path=root/store.NAME
    values=[b'wanted\n',b'not-wanted\n',b'',b'wanted',b'wanted\nextra',b'wanted\n'+b' '*40,b'\xff',b'\0',b' wanted\n',b'not-wanted\n\0']
    for value in values:
        path.write_bytes(value);path.chmod(0o600)
        try:result=store.load()
        except SafetyError:assert value not in values[:2]
        else:assert value in values[:2] and result==(value==b'wanted\n')
        count+=1
    for mode in (0o644,0o400,0o666):
        path.write_bytes(b'wanted\n');path.chmod(mode)
        try:store.load()
        except SafetyError:pass
        else:raise AssertionError(mode)
        count+=1
    path.chmod(0o600)
    real_read=os.read;changed=False
    def replacing_read(fd,n):
        global changed
        data=real_read(fd,n)
        if not changed:
            changed=True;other=root/'replacement';other.write_bytes(b'not-wanted\n');other.chmod(0o600);os.replace(other,path)
        return data
    with patch('beamo_wipe.report_intent.os.read',side_effect=replacing_read):
        try:store.load()
        except SafetyError:pass
        else:raise AssertionError('replaced preference accepted')
    count+=1
    for failing in ('write','fsync'):
        store.save(False)
        with patch('beamo_wipe.report_intent.os.'+failing,side_effect=OSError('fixture I/O')):
            try:store.save(True)
            except OSError:pass
            else:raise AssertionError(failing)
        assert store.load() is False
        assert not list(root.glob('.report-intent-*'))
        store.save(True);assert store.load() is True
        count+=1
    def writer(index):
        for step in range(20):store.save(bool((step+index)%2))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(writer,range(4)))
    assert type(store.load()) is bool and not list(root.glob('.report-intent-*'))
    count+=80
print(json.dumps({'result':'PASS','observations':count,'corrupt_and_valid_values':10,'unsafe_modes':3,'replacement_refusal':1,'I/O_failure_then_retry':2,'concurrent_atomic_writes':80,'regular_files_only':True},indent=2))
