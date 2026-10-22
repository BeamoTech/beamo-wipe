"""Actual worker writes a fake-mounted ordinary-directory bundle."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from beamo_wipe import lang, result_summary, support_export as export

sys.path.insert(0,str(Path('/workspace/beamo-wipe/tests')))
from test_result_presentations import CASES, case_evidence


@pytest.mark.parametrize('controller_language,worker_language',[('en','en'),('fr','fr'),('de','de'),('fr','en'),('de','en')])
def test_worker_keeps_report_language(tmp_path,monkeypatch,controller_language,worker_language):
    effects=[]
    def forbidden(*_a,**_kw):
        effects.append(True)
        raise AssertionError('Real device/process/mount/power action reached')
    for target in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources','beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.nwipe_runner.DryRunRunner.start','beamo_wipe.app._shutdown'):
        monkeypatch.setattr(target,forbidden)
    monkeypatch.setattr(export,'_emit_export_marker',lambda *_:None)
    before=lang.current()
    try:
        lang.set_language(controller_language)
        _wizard,payload,_log=case_evidence(next(case for case in CASES if case[0]=='process_failed'))
        expected_header=result_summary.HEADER_RESULT
        path=tmp_path/'result-sda-123.json'
        payload['provenance']['evidence_file']=str(path)
        raw=(json.dumps(payload)+'\n').encode()
        path.write_bytes(raw)
        Path(str(path)+'.sha256').write_text(hashlib.sha256(raw).hexdigest()+'  '+path.name+'\n')
        evidence=export.prepare_terminal_evidence(path,payload['device']['path'])
        parent=tmp_path/'fake-parent';parent.write_bytes(b'parent')
        child=tmp_path/'fake-child';child.write_bytes(b'child')
        volume=export.ExportVolume(export.DeviceFingerprint(str(parent),2_000_000_000,'Fake USB','fake-serial',''),str(child),1_000_000_000,'vfat','FAT32','FAKE-UUID')
        wire=json.dumps(export._request_dict(evidence,volume,[],[],b'','unavailable')).encode()
        lang.set_language(worker_language)
        monkeypatch.setattr(export.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(wire)))
        monkeypatch.setattr(export,'run_lsblk',lambda:{})
        monkeypatch.setattr(export,'select_export_volume',lambda *_:volume)
        monkeypatch.setattr(export,'_protected_rdevs',lambda *_:())
        monkeypatch.setattr(export,'_volume_with_rdev',lambda value:value)
        monkeypatch.setattr(export,'_assert_partition_parent',lambda *_:None)
        monkeypatch.setattr(export,'MOUNT_ROOT',tmp_path/'mount-root')
        monkeypatch.setattr(export,'_run_command',lambda *_a,**_kw:SimpleNamespace(returncode=0))
        monkeypatch.setattr(export,'_mounted_exact',lambda *_:True)
        monkeypatch.setattr(export,'_verify_mount',lambda *_a,**_kw:None)
        monkeypatch.setattr(export,'_ordinary_unmount',lambda *_:True)
        monkeypatch.setattr(export,'_mount_record',lambda *_:None)
        receipt=export._worker()
        assert receipt.ok and receipt.safe_to_remove
        saved=next((tmp_path/'mount-root').glob('mount-*/BEAMO-WIPE-REPORTS/report-*/RESULT.txt'))
        text=saved.read_text()
        html=(saved.parent/'REPORT.html').read_text()
        print(json.dumps(dict(controller=controller_language,worker=worker_language,expected=expected_header,actual=text.splitlines()[0],saved_html_language=html.split('<html lang="')[1].split('"')[0])))
        assert text.splitlines()[0]==expected_header,'Worker silently generated owner report in a different language'
        assert '<html lang="'+controller_language+'">' in html
        assert not effects
    finally:
        lang.set_language(before)
