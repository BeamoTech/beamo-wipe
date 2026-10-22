from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path('/workspace/beamo-wipe')
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('assets_fixture', ROOT / 'tests/test_iso_live_assets_pass20.py')
fixture_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture_module)
sys.path.insert(0, str(ROOT / 'src'))
from beamo_wipe import release_manifest

results=[]
with tempfile.TemporaryDirectory(prefix='beamo-boot-mode-', dir=OUT) as tmp:
    for mode in (0o755, 0o644):
        base=Path(tmp)/f'mode-{mode:o}'
        base.mkdir()
        project, live, _ = fixture_module._fixture(base)
        kiosk=live/'config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk'
        kiosk.parent.mkdir(parents=True)
        kiosk.write_bytes((ROOT/'packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk').read_bytes())
        kiosk.chmod(0o755)
        subprocess.run(['git','add',str(kiosk.relative_to(project))],cwd=project,check=True)
        subprocess.run(['git','config','core.filemode','false'],cwd=project,check=True)
        kiosk.chmod(mode)
        result=subprocess.run([sys.executable,str(ROOT/'scripts/stage_live_assets.py'),str(project),str(live)],cwd=project,env={**os.environ,'BUILD_ID':'local'},text=True,capture_output=True)
        results.append({'case':f'kiosk-mode-{mode:o}','staging_rc':result.returncode,'stderr':result.stderr,'kiosk_mode':f'{kiosk.stat().st_mode & 0o7777:o}','index_mode':subprocess.check_output(['git','ls-files','--stage','--',str(kiosk.relative_to(project))],cwd=project,text=True).split()[0],'mode_change_visible_to_git':bool(subprocess.check_output(['git','diff','--raw','--',str(kiosk.relative_to(project))],cwd=project,text=True))})

    source=Path(tmp)/'digest-source'
    copied=Path(tmp)/'digest-copy'
    for rel, content in {'packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk':b'#!/bin/sh\nexit 0\n','src/beamo_wipe/__init__.py':b'# wrapper\n','desktop/main.go':b'package main\n'}.items():
        target=source/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    source_kiosk=source/'packaging/live/config/includes.chroot/usr/local/sbin/beamo-wipe-kiosk'
    source_kiosk.chmod(0o755)
    shutil.copytree(source,copied)
    def digest(tree):
        old=release_manifest.ROOT
        try:
            release_manifest.ROOT=tree
            raw=json.dumps(release_manifest.live_build_inputs(),sort_keys=True,separators=(',',':')).encode('ascii')
            return hashlib.sha256(raw).hexdigest()
        finally:
            release_manifest.ROOT=old
    expected=digest(source)
    copied_kiosk=copied/source_kiosk.relative_to(source)
    for name, mode, content in [('normal',0o755,source_kiosk.read_bytes()),('mode-only-change',0o644,source_kiosk.read_bytes()),('byte-change',0o755,b'#!/bin/sh\nexit 1\n')]:
        copied_kiosk.chmod(mode)
        copied_kiosk.write_bytes(content)
        actual=digest(copied)
        results.append({'case':name,'copied_digest_matches':actual==expected,'copied_kiosk_mode':f'{copied_kiosk.stat().st_mode&0o7777:o}'})

output=json.dumps(results,indent=2)+'\n'
(OUT/'kiosk-mode-reproduction.json').write_text(output)
print(output)
assert results[0]['staging_rc']==0
assert results[1]['staging_rc']!=0, 'BUG: non-executable shipped kiosk was accepted by asset staging'
