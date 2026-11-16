"""Finalizer caller binding with exact AST and a wholly in-memory transaction.

Verification, generation, package inventory and QEMU inputs are explicit fakes;
these tests qualify caller behavior only, not the verifier or release artifacts.
"""
from __future__ import annotations

import builtins
import hashlib
import json
import re
import stat
from types import SimpleNamespace

from test_manifest_writer_cleanup import MemoryFS, MemoryPath, assert_closed, capture, load_ast, make_rm


def finalizer_case(initial='absent', injection=None, guard=None):
    fs = MemoryFS()
    rm = make_rm(fs)
    root = MemoryPath('/root')
    dist = root / 'dist'
    iso = dist / 'beamo-wipe-0.2.14-amd64.iso'
    dest = dist / 'beamo-wipe-0.2.14-amd64.manifest.json'
    sums = dist / 'SHA256SUMS'
    manifest = dict(schema_version=2, beamo_wipe_version='0.2.14',
                    source={'commit': 'a' * 40}, build={'release_build_id': 'local'},
                    dependencies={}, live_build_inputs={}, nwipe={},
                    artifact=dict(iso_name=iso.name, iso_path=iso.name, iso_size_bytes=3,
                                  iso_sha256=hashlib.sha256(b'iso').hexdigest()))

    def encode(value):
        value = dict(value)
        value['_manifest_sha256'] = hashlib.sha256(json.dumps(
            value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        return (json.dumps(value, sort_keys=True) + '\n').encode()

    build_raw = encode(manifest)
    final = dict(manifest, test_evidence={'measured': True})
    final_raw = encode(final)
    fs.put(iso, b'iso')
    fs.put(dest, build_raw)
    fs.put(str(iso) + '.sha256', rm['_sidecar_blob'](hashlib.sha256(b'iso').hexdigest(), iso.name))
    fs.put(str(dest) + '.sha256', rm['_sidecar_blob'](hashlib.sha256(build_raw).hexdigest(), dest.name))
    if initial == 'regular':
        fs.put(sums, rm['_sidecar_blob'](hashlib.sha256(b'iso').hexdigest(), iso.name)
               + rm['_sidecar_blob'](hashlib.sha256(build_raw).hexdigest(), dest.name))
    target = fs.put('/root/sentinel', b'keep target')
    initial_link = None
    if initial == 'link':
        initial_link = fs.put(sums, b'/root/sentinel', stat.S_IFLNK | 0o777)
    if initial == 'foreign':
        fs.put(sums, b'foreign initial entry')
    state = dict(writes=0, summary=[], snapshots=[], path_hashes=[], foreign=None)
    prior = rm['require_verified_prior_checksum_list']

    def check_prior(path, **kwargs):
        snapshot = prior(path, **kwargs)
        state['snapshots'].append(snapshot)
        return snapshot

    def write_manifest(value, path):
        assert value is final and path == dest
        state['writes'] += 1
        fs.put(dest, final_raw)
        if injection in ('late_regular', 'late_link'):
            state['foreign'] = fs.put(sums,
                b'/root/sentinel' if injection == 'late_link' else b'late foreign data',
                stat.S_IFLNK | 0o777 if injection == 'late_link' else stat.S_IFREG | 0o600)

    def verify_manifest(path, **kwargs):
        assert fs.node(path).data == final_raw
        if injection == 'manifest_swap':
            fs.put(dest, b'UNVERIFIED REPLACEMENT\n')
        if injection == 'iso_swap':
            fs.put(iso, b'UNVERIFIED ISO\n')
        return final_raw

    path_hash = rm['sha256_file']

    def hash_path(path):
        state['path_hashes'].append(str(path))
        return path_hash(path)

    if guard == 'source':
        manifest['source']['commit'] = 'b' * 40
        build_raw = encode(manifest)
    if guard == 'artifact':
        final['artifact'] = dict(final['artifact'], iso_sha256='c' * 64)
    if guard == 'inputs':
        final['dependencies'] = {'different': True}
    receipt = dict(gate='qemu', status='pass', environment={'qemu_evidence_sha256': 'd' * 64})
    receipts = [receipt] if guard == 'qemu' else []
    rm.update(verify_build_manifest=lambda *args, **kwargs: build_raw,
              git_commit=lambda: 'a' * 40, require_verified_prior_checksum_list=check_prior,
              generate_manifest=lambda **kwargs: final, write_manifest=write_manifest,
              verify_manifest=verify_manifest, sha256_file=hash_path)
    fake_package = SimpleNamespace(release_manifest=SimpleNamespace(**rm))

    def fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        assert name == 'beamo_wipe' and tuple(fromlist) == ('release_manifest',)
        return fake_package

    namespace = dict(__builtins__=dict(vars(builtins), __import__=fake_import),
                     Path=MemoryPath, os=fs, json=json, hashlib=hashlib, re=re,
                     __version__='0.2.14', _unique_json_fields=rm['_unique_manifest_fields'],
                     load_receipts=lambda path: receipts,
                     _open_evidence_directory=lambda path: fs.open(dist, fs.O_DIRECTORY),
                     _load_receipts_at=lambda fd: receipts, _read_regular_at=lambda *args, **kwargs: b'{}',
                     _require_evidence_binding=lambda *args: None,
                     _completed_qemu_evidence_digest=lambda path: 'e' * 64,
                     print=lambda *args, **kwargs: state['summary'].append(args[0]))
    # Future annotation compilation needs its normal stdlib import boundary.
    def import_boundary(name, globals=None, locals=None, fromlist=(), level=0):
        if name == '__future__':
            return builtins.__import__(name, globals, locals, fromlist, level)
        return fake_import(name, globals, locals, fromlist, level)

    namespace['__builtins__']['__import__'] = import_boundary
    load_ast('src/beamo_wipe/ci_evidence.py', ('_close_reader_fds', 'finalize'), namespace)
    error = capture(lambda: namespace['finalize'](root))
    return SimpleNamespace(fs=fs, rm=rm, error=error, state=state, sums=sums,
                           iso=iso, dest=dest, accepted=final_raw, initial_link=initial_link,
                           target=target)


def summary(case):
    assert len(case.state['summary']) == 1
    return json.loads(case.state['summary'][0].removeprefix('Final verified evidence: '))


def test_finalizer_hashes_exact_accepted_manifest_and_iso_record():
    for injection in (None, 'manifest_swap', 'iso_swap'):
        case = finalizer_case(injection=injection)
        assert case.error is None
        accepted = json.loads(case.accepted)
        manifest_sha = hashlib.sha256(case.accepted).hexdigest()
        iso_sha = accepted['artifact']['iso_sha256']
        assert case.fs.node(case.sums).data == (
            f'{iso_sha}  {case.iso.name}\n{manifest_sha}  {case.dest.name}\n').encode()
        printed = summary(case)
        assert printed['manifest_sha256'] == manifest_sha and printed['iso_sha256'] == iso_sha
        if injection is not None:
            assert not case.state['path_hashes'], 'finalizer hashed an unverified later pathname'
        if injection == 'manifest_swap':
            assert hashlib.sha256(case.fs.node(case.dest).data).hexdigest() != manifest_sha
        if injection == 'iso_swap':
            assert hashlib.sha256(case.fs.node(case.iso).data).hexdigest() != iso_sha
        assert_closed(case.fs)


def test_finalizer_normal_prior_regular_and_initial_link_controls():
    for initial in ('absent', 'regular', 'link'):
        case = finalizer_case(initial=initial)
        assert case.error is None
        assert stat.S_ISREG(case.fs.node(case.sums).mode)
        assert case.target.data == b'keep target'
        snapshot = case.state['snapshots'][0]
        if initial == 'absent':
            assert snapshot is None
        else:
            assert snapshot.kind == ('symlink' if initial == 'link' else 'regular')
        if initial == 'link':
            assert sum(node is case.initial_link for node in case.fs.files.values()) == 1
        assert_closed(case.fs)


def test_finalizer_refuses_late_regular_and_link_without_moving_foreign_entry():
    for initial in ('absent', 'regular', 'link'):
        for injection in ('late_regular', 'late_link'):
            case = finalizer_case(initial=initial, injection=injection)
            assert isinstance(case.error, (RuntimeError, FileExistsError))
            assert not case.state['summary']
            assert case.fs.node(case.sums) is case.state['foreign']
            assert sum(node is case.state['foreign'] for node in case.fs.files.values()) == 1
            assert case.target.data == b'keep target'
            assert_closed(case.fs)


def test_finalizer_refuses_initial_foreign_before_manifest_publication():
    case = finalizer_case(initial='foreign')
    assert isinstance(case.error, RuntimeError)
    assert case.fs.node(case.sums).data == b'foreign initial entry'
    assert not case.state['writes'] and not case.state['summary']
    assert_closed(case.fs)


def test_finalizer_retains_source_artifact_input_and_qemu_checks():
    for guard in ('source', 'artifact', 'inputs', 'qemu'):
        case = finalizer_case(guard=guard)
        assert isinstance(case.error, RuntimeError), guard
        assert not case.state['writes'] and not case.state['summary']
        assert str(case.sums) not in case.fs.files
        assert_closed(case.fs)


def test_checksum_preflight_disallows_link_unless_explicitly_allowed():
    fs = MemoryFS()
    rm = make_rm(fs)
    path = MemoryPath('/root/dist/SHA256SUMS')
    link = fs.put(path, b'/root/sentinel', stat.S_IFLNK | 0o777)
    assert isinstance(capture(lambda: rm['require_verified_prior_checksum_list'](path.parent)), RuntimeError)
    snapshot = rm['require_verified_prior_checksum_list'](path.parent, replace_link=True)
    assert snapshot.kind == 'symlink' and snapshot.contents == '/root/sentinel'
    assert snapshot.fields[1] == link.inode
    assert_closed(fs)
