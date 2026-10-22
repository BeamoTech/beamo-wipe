"""Supplemental fake-evidence locale/redaction matrix; no device/process effects."""
from pathlib import Path
import copy
import hashlib
import json
import sys

import pytest
from beamo_wipe import lang, outcomes, privacy, result_summary

sys.path.insert(0, '/workspace/beamo-tools/audit-pass6-20261021/root/report-baseline/tests')
from test_result_presentations import CASES, case_evidence

root = Path(__file__).resolve().parent
patch = pytest.MonkeyPatch()
effects = []

def forbidden(*_args, **_kwargs):
    effects.append(True)
    raise AssertionError('Native effect reached')

for target in ('subprocess.run','subprocess.Popen','beamo_wipe.discover.run_lsblk',
               'beamo_wipe.discover.read_cmdline','beamo_wipe.discover.read_mount_sources',
               'beamo_wipe.nwipe_runner.NwipeRunner.start','beamo_wipe.app._shutdown'):
    patch.setattr(target, forbidden)

serials = ('FAKE-SERIAL-P6-ZX9','FAKE-ßERIAL-P6-Ω9','FAKE-[A].*+P6','FAKE-𐐀-P6-LOW','FAKE-PII-P6-İ','FAKE-PII-P6-é','FAKE-PII-P6-K9','FAKE-PII-P6-汉字')
count = 0
try:
    for saved_language in ('en','fr','de'):
        lang.set_language(saved_language)
        for case in CASES:
            _, base, _ = case_evidence(case)
            for report_language in ('en','fr','de'):
                lang.set_language(report_language)
                for serial in serials:
                    evidence = copy.deepcopy(base)
                    evidence['device']['serial'] = serial
                    evidence['device']['wwn'] = 'FAKE-WWN-P5-ABC9'
                    evidence['device']['model'] = 'Fake drive ' + serial
                    evidence['device']['path'] = '/dev/p5fakedisk'
                    evidence['device']['realpath'] = '/dev/p5fakedisk'
                    evidence['device']['name'] = 'p5fakedisk'
                    evidence['device']['label'] = 'FAKE-LABEL-P5-ABC9'
                    evidence['boot_device'] = '/dev/p5fakeboot'
                    evidence['logfile'] = '/tmp/p5-fake-log-ABC9'
                    evidence['provenance']['evidence_file'] = '/tmp/result-p5fakedisk-1.json'
                    evidence['device_presentation']['id_value'] = serial
                    evidence['device_presentation']['system_path'] = '/dev/p5fakedisk'
                    evidence['device_presentation']['title'] = 'Fake drive ' + serial
                    evidence['warnings'] = ['Fake note ' + serial + ' /dev/p5fakedisk']
                    before = copy.deepcopy(evidence)
                    expected = outcomes.present_evidence(evidence).code
                    assert expected == case[0]
                    shared = privacy.make_sharing_copy(evidence)
                    assert evidence == before
                    raw = privacy.encode_sharing_copy(shared).decode()
                    summary = result_summary.build_result_summary(shared)
                    page = result_summary.build_result_report_html(shared)
                    for token in (serial, 'FAKE-WWN-P5-ABC9', '/dev/p5fakedisk',
                                  'p5fakedisk','FAKE-LABEL-P5-ABC9','/dev/p5fakeboot',
                                  '/tmp/p5-fake-log-ABC9', 'result-p5fakedisk-1.json'):
                        assert token not in raw and token not in summary and token not in page
                    assert outcomes.present_evidence(shared).code == expected
                    assert not set(shared['device']).intersection({'serial','wwn','path','realpath','name','label'})
                    assert privacy.is_sharing_copy(shared)
                    count += 1
            lang.set_language(saved_language)
    assert count == 792 and not effects
finally:
    lang.set_language('en')
    patch.undo()

record = {'cases':count,'saved_languages':['en','fr','de'],'report_languages':['en','fr','de'],
          'outcomes':len(CASES),'identifier_forms':len(serials),'semantic_or_redaction_failures':0,
          'native_effects':0,'original_evidence_mutations':0,
          'source_sha256':{name:hashlib.sha256((Path('/workspace/beamo-wipe')/name).read_bytes()).hexdigest()
                           for name in ['src/beamo_wipe/privacy.py','src/beamo_wipe/result_summary.py','src/beamo_wipe/outcomes.py']}}
(root/'sharing-matrix.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
