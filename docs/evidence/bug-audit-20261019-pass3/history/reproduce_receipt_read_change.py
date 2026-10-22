from __future__ import annotations
import importlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path('/workspace/beamo-wipe')
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'developer_tests'),str(ROOT)]
import pytest
fixtures=importlib.import_module('test_desktop_final_receipt_pass3_20261019')
results=[]
with tempfile.TemporaryDirectory(prefix='receipt-read-change-',dir=OUT) as tmp:
    for host in ('posix','nt'):
        for primary in (False,True):
            for mutate in (False,True):
                builder=fixtures.builder.__wrapped__()
                project=Path(tmp)/f'{host}-{primary}-{mutate}'
                project.mkdir()
                changed=[]
                foreign=b'foreign receipt inserted during bounded read'
                with pytest.MonkeyPatch.context() as patch:
                    output=fixtures._setup(builder,project,patch,host,False)
                    manifest=output/'desktop-build.json'
                    if primary:
                        fixtures._during_receipt(builder,patch,host,manifest,'close',lambda:(output/builder.LAUNCHERS[0]).write_bytes(b'foreign launcher'))
                    class ReadStream:
                        def __init__(self,stream):self.stream=stream
                        def __enter__(self):self.stream.__enter__();return self
                        def __exit__(self,*args):return self.stream.__exit__(*args)
                        def __getattr__(self,name):return getattr(self.stream,name)
                        def read(self,*args):
                            data=self.stream.read(*args)
                            if mutate and not changed:
                                manifest.write_bytes(foreign)
                                changed.append(True)
                            return data
                    if host=='posix':
                        original=builder.os.fdopen
                        def fdopen(fd,mode='r',*args,**kwargs):
                            is_manifest=mode=='rb' and manifest.exists() and builder.os.fstat(fd).st_ino==manifest.stat().st_ino
                            stream=original(fd,mode,*args,**kwargs)
                            return ReadStream(stream) if is_manifest else stream
                        patch.setattr(builder.os,'fdopen',fdopen)
                    else:
                        original=Path.open
                        def path_open(path,mode='r',*args,**kwargs):
                            stream=original(path,mode,*args,**kwargs)
                            return ReadStream(stream) if path==manifest and mode=='rb' else stream
                        patch.setattr(Path,'open',path_open)
                    try:builder.build(output)
                    except Exception as error:build_error=f'{type(error).__name__}: {error}'
                    else:build_error=None
                    results.append({'host':host,'primary_launcher_error':primary,'mutate_receipt_during_read':mutate,'mutation_reached':bool(changed),'build_error':build_error,'manifest_exists':manifest.exists(),'foreign_preserved':manifest.exists() and manifest.read_bytes()==foreign})
output=json.dumps(results,indent=2)+'\n'
(OUT/'receipt-read-change-after.json').write_text(output)
print(output)
assert all(row['build_error'] is None for row in results if not row['primary_launcher_error'] and not row['mutate_receipt_during_read'])
assert all(row['build_error'] is not None and not row['manifest_exists'] for row in results if row['primary_launcher_error'] and not row['mutate_receipt_during_read'])
assert all(row['build_error'] is not None and row['foreign_preserved'] for row in results if row['mutate_receipt_during_read']), 'BUG: receipt edit during read produced false success or cleanup removed foreign receipt bytes'
