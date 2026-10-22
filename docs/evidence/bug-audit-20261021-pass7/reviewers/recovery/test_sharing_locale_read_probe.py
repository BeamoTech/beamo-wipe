"""A valid saved sharing copy must retain its verdict in another reader locale."""
import json
import sys

import pytest
sys.path.insert(0,'/workspace/beamo-wipe/tests')
from test_result_presentations import CASES, case_evidence
from beamo_wipe import lang
from beamo_wipe.outcomes import present_evidence
from beamo_wipe.privacy import make_sharing_copy


@pytest.mark.parametrize('created', ['en','fr'])
@pytest.mark.parametrize('reader', ['en','fr'])
def test_saved_sharing_verdict_is_not_lost_when_reader_language_changes(monkeypatch, created, reader, request):
    monkeypatch.setenv('BEAMO_WIPE_DRY_RUN','1')
    old=lang.current()
    try:
        lang.set_language('en')
        _wizard,evidence,_log=case_evidence(CASES[0])
        assert present_evidence(evidence).code=='verified'
        lang.set_language(created)
        sharing=json.loads(json.dumps(make_sharing_copy(evidence)))
        assert present_evidence(sharing).code=='verified'
        lang.set_language(reader)
        assert present_evidence(evidence).code=='verified'
        code=present_evidence(sharing).code
        trace={'created':created,'reader':reader,'saved_locale':sharing['locale']['language'],
               'presentation_code':sharing['presentation']['code'],'reader_verdict':code}
        request.node.user_properties.append(('trace',json.dumps(trace)));print(json.dumps(trace))
        assert code=='verified',trace
    finally:
        lang.set_language(old)
