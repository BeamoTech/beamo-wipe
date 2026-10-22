"""Owned-file, mocked-compiler proof for manifest retirement on cancellation."""
import importlib.util
from pathlib import Path

import pytest

REPO = Path('/workspace/beamo-wipe')


@pytest.mark.parametrize('failure', [RuntimeError, KeyboardInterrupt, SystemExit])
def test_failed_final_verification_retires_owned_receipt(tmp_path, monkeypatch, failure):
    spec = importlib.util.spec_from_file_location('builder_interrupt_proof', REPO / 'scripts/build_desktop.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    desktop = tmp_path / 'desktop'
    desktop.mkdir()
    (desktop / 'go.mod').write_text('module fixture\n')
    (desktop / 'main.go').write_text('package main\n')
    output = tmp_path / 'output'

    def fake_output(argv, **kwargs):
        if argv[1:] == ['version']:
            return 'go version go1.26.8 linux/amd64\n'
        if argv[1:] == ['rev-parse', 'HEAD']:
            return 'a' * 40 + '\n'
        if argv[1:] == ['status', '--porcelain']:
            return ''
        raise AssertionError(argv)

    def fake_build(argv, **kwargs):
        Path(argv[argv.index('-o') + 1]).write_bytes(b'compiler callback')

    original = builder._require_unchanged_launcher_outputs

    def final_verification(*args):
        if (output / 'desktop-build.json').exists():
            raise failure('final verification interrupted')
        return original(*args)

    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    monkeypatch.setattr(builder.subprocess, 'check_output', fake_output)
    monkeypatch.setattr(builder.subprocess, 'check_call', fake_build)
    monkeypatch.setattr(builder, '_require_unchanged_launcher_outputs', final_verification)
    with pytest.raises(failure):
        builder.build(output)
    assert not (output / '.build.lock').exists()
    assert not (output / 'desktop-build.json').exists(), 'failed build retained success receipt'
