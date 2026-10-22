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
fixtures=importlib.import_module('test_desktop_output_replacement_pass2_20261019')
results=[]
with tempfile.TemporaryDirectory(prefix='manifest-write-gap-',dir=OUT) as tmp:
    for host in ('posix','nt'):
        for kind in ('none','launcher','receipt'):
            builder=fixtures.builder.__wrapped__()
            project=Path(tmp)/f'{host}-{kind}'
            project.mkdir()
            touched=[]
            with pytest.MonkeyPatch.context() as patch:
                output=fixtures._setup(builder,project,patch,host,False)
                manifest=output/'desktop-build.json'
                def after_write():
                    touched.append('manifest-write')
                    if kind=='launcher':
                        (output/builder.LAUNCHERS[0]).write_bytes(b'foreign launcher after receipt write')
                    elif kind=='receipt':
                        manifest.unlink()
                        manifest.write_bytes(b'foreign replacement receipt')
                class WrappedManifest:
                    def __init__(self,stream):self.stream=stream
                    def __enter__(self):self.stream.__enter__();return self
                    def __exit__(self,*args):return self.stream.__exit__(*args)
                    def __getattr__(self,name):return getattr(self.stream,name)
                    def write(self,data):
                        result=self.stream.write(data)
                        after_write()
                        return result
                if host=='posix':
                    original_fdopen=builder.os.fdopen
                    def fdopen(fd,mode='r',*args,**kwargs):
                        stream=original_fdopen(fd,mode,*args,**kwargs)
                        return WrappedManifest(stream) if mode=='w' and kwargs.get('encoding')=='utf-8' else stream
                    patch.setattr(builder.os,'fdopen',fdopen)
                else:
                    original_open=Path.open
                    def path_open(path,mode='r',*args,**kwargs):
                        stream=original_open(path,mode,*args,**kwargs)
                        return WrappedManifest(stream) if path==manifest and mode=='x' else stream
                    patch.setattr(Path,'open',path_open)
                try:builder.build(output)
                except Exception as error:build_error=f'{type(error).__name__}: {error}'
                else:build_error=None
                try:builder.verify_desktop_bundle(project,output,'a'*40,'0.2.13',False)
                except Exception as error:verify_error=f'{type(error).__name__}: {error}'
                else:verify_error=None
                results.append({'host':host,'kind':kind,'write_reached':bool(touched),'build_error':build_error,'verify_error':verify_error,'manifest_exists':manifest.exists(),'foreign_receipt_preserved':kind=='receipt' and manifest.read_bytes()==b'foreign replacement receipt'})
output=json.dumps(results,indent=2)+'\n'
(OUT/'manifest-write-gap-after.json').write_text(output)
print(output)
assert all(row['build_error'] is None and row['verify_error'] is None for row in results if row['kind']=='none')
assert all(row['build_error'] is not None for row in results if row['kind']!='none'), 'BUG: builder reported success after receipt-write interval artifact or receipt mutation'
