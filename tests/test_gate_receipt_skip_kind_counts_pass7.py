"""A gate's skip records must agree with each declared outcome kind."""

import pytest

from beamo_wipe.verification_evidence import (
    build_gate_receipt, canonical_digest, verify_gate_receipt,
)


@pytest.mark.parametrize(
    ('skipped', 'xfailed', 'kinds'),
    [(1, 0, ['xfail']), (0, 1, ['skip']), (2, 0, ['skip', 'xfail']),
     (0, 2, ['xfail', 'skip'])],
)
def test_gate_rejects_skip_kind_counts_that_only_match_in_total(skipped, xfailed, kinds):
    with pytest.raises(RuntimeError, match='skip list does not match its counts'):
        _receipt(skipped, xfailed, kinds)


@pytest.mark.parametrize('kinds', [[], ['skip'], ['xfail'], ['skip', 'xfail']])
def test_gate_accepts_matching_per_kind_skip_counts(kinds):
    receipt = _receipt(kinds.count('skip'), kinds.count('xfail'), kinds)
    assert verify_gate_receipt(receipt) == receipt
    assert receipt['status'] == 'pass'
    assert len(receipt['skips']) == len(kinds)


def _receipt(skipped, xfailed, kinds):
    return build_gate_receipt(
        gate='tests', status='pass', command='python3 -m pytest',
        source_commit='a' * 40, build_id='fixture', environment={'platform': 'linux'},
        measured={'passed': 1, 'failed': 0, 'errors': 0, 'skipped': skipped,
                  'xfailed': xfailed, 'deselected': 0, 'total': 1 + skipped + xfailed},
        skips=[{'id': f'test_fake_{n}', 'kind': kind, 'reason': 'fixture-only'}
               for n, kind in enumerate(kinds)],
        log_sha256='b' * 64, started_at='2026-10-16T00:00:00Z',
        ended_at='2026-10-16T00:00:01Z',
    )


@pytest.mark.parametrize('kind', ['skip', 'xfail'])
def test_stored_gate_rejects_misclassified_skip_records_even_with_valid_digest(kind):
    receipt = _receipt(int(kind == 'skip'), int(kind == 'xfail'), [kind])
    receipt['skips'][0]['kind'] = 'xfail' if kind == 'skip' else 'skip'
    receipt['receipt_sha256'] = canonical_digest(
        {key: value for key, value in receipt.items() if key != 'receipt_sha256'}
    )
    with pytest.raises(RuntimeError, match='skip list does not match its counts'):
        verify_gate_receipt(receipt)
