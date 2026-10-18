"""Exercise guard authority with intercepted exec/log calls; no CLI executes."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
from unittest.mock import patch

guard=Path('/tmp/beamo-pass18-fallback-guard/gcloud')
rows=[]
class ExecReached(Exception):
    pass
with tempfile.TemporaryDirectory(prefix='pass18-guard-',dir='/tmp/pytest-of-root') as private, tempfile.TemporaryDirectory(prefix='pass18-outside-') as outside:
    base=Path(private);base.chmod(0o700)
    upload=base/'upload';upload.mkdir();(upload/'.gcloudignore').write_text('ignored\n')
    other=Path(outside)/'upload';other.mkdir();(other/'.gcloudignore').write_text('ignored\n')
    config=base/'gcloud-config'
    alias=base/'aliased-upload';alias.symlink_to(upload,target_is_directory=True)
    config_link=base/'config-link';config_link.symlink_to(base/'missing')
    variants=['fresh','no-config','outside','dotdot','upload-link','config-link','existing-config','public-parent','remote-build','auth','extra-arg','wrong-meta']
    original_open=Path.open
    for name in variants:
        args=['meta','list-files-for-upload',str(upload)]
        env={'CLOUDSDK_CONFIG':str(config),'GOOGLE_APPLICATION_CREDENTIALS':'FAKE-UNREAD',
             'CLOUDSDK_AUTH_ACCESS_TOKEN':'FAKE-UNREAD'}
        if name=='no-config':env.pop('CLOUDSDK_CONFIG')
        elif name=='outside':args[-1]=str(other)
        elif name=='dotdot':args[-1]=str(base/'..'/base.name/'upload')
        elif name=='upload-link':args[-1]=str(alias)
        elif name=='config-link':env['CLOUDSDK_CONFIG']=str(config_link)
        elif name=='existing-config':config.mkdir(mode=0o700)
        elif name=='public-parent':base.chmod(0o755)
        elif name=='remote-build':args=['builds','submit',str(upload)]
        elif name=='auth':args=['auth','print-access-token']
        elif name=='extra-arg':args.append('--extra')
        elif name=='wrong-meta':args[1]='something-else'
        calls=[];captured=io.StringIO()
        def opened(path,*a,**k):
            if str(path) in {'/tmp/pass18-primary/permitted-offline-gcloud.jsonl','/tmp/pass18-primary/forbidden-fallback-attempts.txt'}:
                return contextlib.nullcontext(captured)
            return original_open(path,*a,**k)
        def intercepted(executable,argv):
            calls.append((executable,argv))
            assert os.environ['CLOUDSDK_AUTH_DISABLE_CREDENTIALS']=='true'
            assert os.environ['CLOUDSDK_COMPONENT_MANAGER_DISABLE_UPDATE_CHECK']=='true'
            assert os.environ['CLOUDSDK_CORE_DISABLE_USAGE_REPORTING']=='true'
            assert 'GOOGLE_APPLICATION_CREDENTIALS' not in os.environ
            assert 'CLOUDSDK_AUTH_ACCESS_TOKEN' not in os.environ
            raise ExecReached
        outcome=None
        try:
            with patch.dict(os.environ,env,clear=True),patch('sys.argv',[str(guard),*args]),patch('os.execv',intercepted),patch.object(Path,'open',opened):
                runpy.run_path(str(guard),run_name='__main__')
        except ExecReached:outcome='permitted-intercepted-local-exec'
        except SystemExit as error:
            assert error.code==97
            outcome='rejected'
        finally:
            if name=='existing-config':config.rmdir()
            if name=='public-parent':base.chmod(0o700)
        assert bool(calls) is (name=='fresh')
        if calls:assert calls[0]==('/usr/bin/gcloud',['/usr/bin/gcloud',*args])
        rows.append(dict(case=name,outcome=outcome,intercepted_execs=len(calls)))
assert len(rows)==12
Path('/tmp/pass18-primary/fallback-guard-probe.json').write_text(json.dumps(dict(cases=rows,actual_cli_execs=0),indent=2)+'\n')
print('12 guard cases PASS; 0 actual CLI executions')
