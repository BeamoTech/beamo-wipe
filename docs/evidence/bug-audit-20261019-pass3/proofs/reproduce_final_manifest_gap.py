from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT=Path('/workspace/beamo-wipe')
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'src'),str(ROOT)]
import pytest
spec=importlib.util.spec_from_file_location('manifest_gap_builder',ROOT/'scripts/build_desktop.py')
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
class WindowsOSProxy:
    name='nt'
    def __getattr__(self,name):return getattr(os,name)
results=[]
with tempfile.TemporaryDirectory(prefix='manifest-gap-',dir=OUT) as tmp:
    for host in ('posix','nt'):
        for target_index in (None,0,1):
            project=Path(tmp)/f'{host}-{target_index}'
            desktop=project/'desktop'
            desktop.mkdir(parents=True)
            (desktop/'go.mod').write_text('module fixture\n')
            (desktop/'main.go').write_text('package main\nfunc main() {}\n')
            output=project/'output'
            touched=[]
            def fake_output(argv,**kwargs):
                if argv[1:]==['version']:return f'go version {builder.GO_VERSION} {host}/amd64\n'
                if argv[1:]==['rev-parse','HEAD']:return 'a'*40+'\n'
                if argv[1:]==['status','--porcelain']:return ''
                raise AssertionError(argv)
            def fake_build(argv,**kwargs):
                Path(argv[argv.index('-o')+1]).write_bytes(b'compiled launcher')
            original_digest=builder.desktop_source_digest
            def digest_then_change_published(root):
                value=original_digest(root)
                if root==project and not touched and all((output/name).is_file() and (output/name).read_bytes()==b'compiled launcher' for name in builder.LAUNCHERS):
                    touched.append('final-source-check-after-both-launcher-hash-checks')
                    if target_index is not None:
                        (output/builder.LAUNCHERS[target_index]).write_bytes(b'foreign replacement during final source hash')
                return value
            with pytest.MonkeyPatch.context() as patch:
                patch.setattr(builder,'ROOT',project)
                patch.setattr(builder.subprocess,'check_output',fake_output)
                patch.setattr(builder.subprocess,'check_call',fake_build)
                patch.setattr(builder,'desktop_source_digest',digest_then_change_published)
                if host=='nt':patch.setattr(builder,'os',WindowsOSProxy())
                try:builder.build(output)
                except Exception as error:build_error=f'{type(error).__name__}: {error}'
                else:build_error=None
                try:builder.verify_desktop_bundle(project,output,'a'*40,'0.2.13',False)
                except Exception as error:verify_error=f'{type(error).__name__}: {error}'
                else:verify_error=None
            results.append({'host_contract':host,'target_index':target_index,'injection_reached':bool(touched),'build_error':build_error,'manifest_written':(output/'desktop-build.json').exists(),'verify_error':verify_error,'foreign_preserved':target_index is not None and (output/builder.LAUNCHERS[target_index]).read_bytes()==b'foreign replacement during final source hash'})
output=json.dumps(results,indent=2)+'\n'
(OUT/'final-manifest-gap-after.json').write_text(output)
print(output)
assert all(row['build_error'] is None and row['verify_error'] is None for row in results if row['target_index'] is None)
assert all(row['build_error'] is not None and not row['manifest_written'] and row['foreign_preserved'] for row in results if row['target_index'] is not None), 'BUG: builder reported success and emitted a false launcher receipt after final source-hash interval mutation'
