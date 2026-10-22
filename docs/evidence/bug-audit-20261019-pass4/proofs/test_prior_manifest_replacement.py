"""Prior manifest validation cannot authorize deleting a replacement receipt."""
from pathlib import Path

import pytest

from test_desktop_output_replacement_pass2_20261019 import _setup, builder  # noqa: F401


@pytest.mark.parametrize('host', ('posix', 'nt'))
@pytest.mark.parametrize('mutation', ('replace', 'edit', 'symlink'))
def test_foreign_prior_receipt_survives_retirement(builder, tmp_path, monkeypatch, host, mutation):
    output = _setup(builder, tmp_path, monkeypatch, host, True)
    manifest = output / 'desktop-build.json'
    outside = tmp_path / 'outside-receipt'
    foreign = b'foreign report must survive'
    outside.write_bytes(foreign)
    original = builder._require_generated_prior_manifest

    def validate_then_replace(*args, **kwargs):
        result = original(*args, **kwargs)
        if mutation != 'edit':
            manifest.unlink()
        if mutation == 'symlink':
            manifest.symlink_to(outside)
        else:
            manifest.write_bytes(foreign)
        return result

    monkeypatch.setattr(builder, '_require_generated_prior_manifest', validate_then_replace)
    with pytest.raises(RuntimeError):
        builder.build(output)
    assert manifest.read_bytes() == foreign
    assert manifest.is_symlink() is (mutation == 'symlink')
    assert outside.read_bytes() == foreign
    for name in builder.LAUNCHERS:
        assert (output / name).read_bytes() == b'prior compiled launcher'


@pytest.mark.parametrize('host', ('posix', 'nt'))
def test_unchanged_prior_receipt_is_rebuildable(builder, tmp_path, monkeypatch, host):
    output = _setup(builder, tmp_path, monkeypatch, host, True)
    builder.build(output)
    builder.verify_desktop_bundle(tmp_path, output, 'a'*40, '0.2.13', False)
