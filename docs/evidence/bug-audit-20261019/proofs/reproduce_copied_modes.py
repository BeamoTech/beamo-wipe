from __future__ import annotations
import importlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path('/workspace/beamo-wipe')
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT/'tests'),str(ROOT),str(ROOT/'src')]
import pytest
fixture=importlib.import_module('test_iso_copy_binding_pass37_build')
paths=(
    'packaging/live/config/includes.chroot/usr/local/bin/beamo-wipe',
    'packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk',
    'packaging/live/config/hooks/normal/0500-build-nwipe.hook.chroot',
)
results=[]
with tempfile.TemporaryDirectory(prefix='copy-mode-repro-',dir=OUT) as tmp:
    source,copied,helper=fixture._fixture(Path(tmp))
    for relative in paths:
        path=source/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(b'#!/bin/sh\nexit 0\n')
        path.chmod(0o755)
    with pytest.MonkeyPatch.context() as monkeypatch:
        expected=fixture._digest(source,monkeypatch)
        shutil.copytree(source,copied,dirs_exist_ok=True)
        code=fixture._container_check()
        normal=fixture._run_check(code,expected,copied)
        results.append({'case':'normal','copy_check_rc':normal.returncode,'stderr':normal.stderr})
        for relative in paths:
            target=copied/relative
            target.chmod(0o644)
            assert (source/relative).stat().st_mode&0o777==0o755
            assert fixture._digest(source,monkeypatch)==expected
            assert fixture._digest(copied,monkeypatch)==expected
            invalid=fixture._run_check(code,expected,copied)
            results.append({'case':relative,'source_mode':'755','copied_mode':'644','copy_check_rc':invalid.returncode,'stderr':invalid.stderr})
            target.chmod(0o755)
        (copied/helper.relative_to(source)).write_bytes(b'changed helper\n')
        bad_bytes=fixture._run_check(code,expected,copied)
        results.append({'case':'byte-tamper-control','copy_check_rc':bad_bytes.returncode,'stderr':bad_bytes.stderr})
output=json.dumps(results,indent=2)+'\n'
(OUT/'copied-modes-before.json').write_text(output)
print(output)
assert results[0]['copy_check_rc']==0
assert results[-1]['copy_check_rc']!=0
assert all(row['copy_check_rc']!=0 for row in results[1:-1]), 'BUG: copied non-executable boot entrypoints passed trusted copy verification'
