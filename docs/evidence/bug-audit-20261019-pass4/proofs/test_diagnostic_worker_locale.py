"""Replay production controller JSON through the worker, stopping before I/O."""
import hashlib
import io
import json
from pathlib import Path
import time
from types import SimpleNamespace

import pytest
from beamo_wipe import diagnostic_report, lang, support_export as export
from beamo_wipe.models import DiscoveryResult


class EndOfProbe(RuntimeError):
    pass


@pytest.mark.parametrize('controller_language,worker_language', [('en','en'),('fr','fr'),('de','de'),('fr','en'),('de','en')])
def test_diagnostic_controller_bytes_survive_clean_worker(monkeypatch, controller_language, worker_language):
    effects=[]
    def forbidden(*_args,**_kwargs):
        effects.append(True)
        raise AssertionError('Real device/process/mount/power action reached')
    for target in ('subprocess.run','subprocess.Popen','beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.nwipe_runner.DryRunRunner.start','beamo_wipe.app._shutdown','beamo_wipe.discover.run_lsblk','beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources'):
        monkeypatch.setattr(target,forbidden)
    monkeypatch.setattr(export,'_emit_export_marker',lambda *_:None)
    before=lang.current()
    scans=[]
    caught=[]
    try:
        lang.set_language(controller_language)
        report=diagnostic_report.create_report('discovery_failed',DiscoveryResult(error='controlled failure'),ui='accessible',session_started=time.monotonic())
        verified=diagnostic_report.verified_report(report)
        volume=export.ExportVolume(export.DeviceFingerprint('/dev/sdz',2_000_000_000,'Fake USB','fake-export',''),'/dev/sdz1',1_000_000_000,'vfat','FAT32','FAKE-UUID')
        request=json.dumps(export._request_dict(verified,volume,[],[],b'','unavailable')).encode()
        # The subprocess has no inherited module globals and starts in English.
        lang.set_language(worker_language)
        def before_inventory():
            scans.append('validated request reached inventory boundary')
            raise EndOfProbe()
        monkeypatch.setattr(export,'run_lsblk',before_inventory)
        monkeypatch.setattr(export.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(request)))
        try:
            export._worker()
        except BaseException as error:
            caught.append(error)
        print(json.dumps(dict(controller=controller_language,worker=worker_language,title=json.loads(report)['title'],worker_title=diagnostic_report.TITLE,caught=[type(e).__name__ for e in caught],scans=scans)))
        assert scans==['validated request reached inventory boundary'], 'Worker rejected a controller-validated diagnostic because its session language was lost'
        assert isinstance(caught[0],EndOfProbe)
        assert not effects
    finally:
        lang.set_language(before)
