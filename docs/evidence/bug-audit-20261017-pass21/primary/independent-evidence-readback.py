"""Independent stdlib-only artifact/source readback; never imports the app."""

import ast
import collections
import datetime
import hashlib
import json
from pathlib import Path
import struct
import tarfile
import xml.etree.ElementTree as ET
import zlib

root = Path('/root/dev/Beamo Wipe')
out = Path('/tmp/pass21-primary')
runner = Path('/tmp/pass21-runner')
ui = Path('/tmp/pass21-ui')
evidence = root/'docs/evidence/bug-audit-20261017-pass21'
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda path: json.loads(Path(path).read_text())
hashed = {}


def authenticate(path):
    path = Path(path)
    assert path.is_file() and not path.is_symlink(), path
    hashed[str(path)] = sha(path.read_bytes())
    return hashed[str(path)]


freeze = read(out/'source-freeze.json')
freeze_sha = authenticate(out/'source-freeze.json')
assert len(freeze) == 788
assert all(authenticate(root/n) == h for n, h in freeze.items())
start = read(out/'starting-freeze.json')
assert len(start) == 779
for name, mapping in [('starting-inputs.tar.gz', start), ('final-source-inputs.tar.gz', freeze)]:
    authenticate(out/name)
    with tarfile.open(out/name) as archive:
        members = archive.getmembers()
        assert len(members) == len(mapping) and {m.name for m in members} == set(mapping)
        assert all(m.isfile() and sha(archive.extractfile(m).read()) == mapping[m.name] for m in members)
source = read(out/'source-review.json')
peer = read(evidence/'runner/final-source-review.json')
assert authenticate(evidence/'runner/final-source-review.json') == '394b309f0bdbf701e7db1bd5b15a31ec8ff69c3fdd5f0efeb72c8d751ac214cd'
reviewed = {n: r['reviewed_sha256'] for n, r in peer['runtime'].items()}
reviewed.update(peer['tests'])
assert len(reviewed) == 13 and all(freeze[n] == h for n, h in reviewed.items())
assert sorted(n for n in start if start[n] != freeze[n]) == sorted(source['changed'])
assert sum(start[n] == freeze[n] for n in start) == 775
digest = hashlib.sha256()
for name, value in sorted(freeze.items()):
    if name.startswith('src/beamo_wipe/'):
        nb, hb = name.encode(), value.encode()
        digest.update(f'{len(nb)}:'.encode()+nb)
        digest.update(f'{len(hb)}:'.encode()+hb)
assert digest.hexdigest() == source['runtime_source_sha256'] == '8e18e259414408eff434768ad24b38432bf913b12a864439f40b585a264496c1'
with tarfile.open(out/'starting-inputs.tar.gz') as archive:
    originals = [p for p in (out/'original-replay/src').rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix not in {'.pyc', '.pyo'}]
    assert len(originals) == 58
    for path in originals:
        name = 'src/'+path.relative_to(out/'original-replay/src').as_posix()
        assert sha(path.read_bytes()) == start[name]
        assert archive.extractfile(name).read() == path.read_bytes()


def cases(path):
    authenticate(path)
    return ET.parse(path).getroot().findall('.//testcase')


original = cases(out/'final-canonical-original.xml')
focused = cases(out/'final-focused-corrected.xml')
new_names = set(source['added'])
by_module = lambda cc: collections.Counter('tests/'+c.get('classname', '').split('.')[-1]+'.py' for c in cc)
original_counts = by_module(original)
assert len(original) == 219 and set(original_counts) == new_names
assert sum(c.find('failure') is not None for c in original) == 89
assert not any(c.find('error') is not None or c.find('skipped') is not None for c in original)
assert len(focused) == 290 and not any(any(c.find(k) is not None for k in ('failure', 'error', 'skipped')) for c in focused)
assert {n: v for n, v in by_module(focused).items() if n in new_names} == dict(original_counts)
invalid = read(out/'final-focused-status.json')
assert invalid['exit_code'] == 4 and not cases(out/'final-focused.xml')

gate = read(out/'gate-verification.json')
statuses = read(out/'local-gate-status.json')
assert gate['source_freeze_sha256'] == freeze_sha
assert gate['status_sha256'] == authenticate(out/'local-gate-status.json')
assert [s['phase'] for s in statuses] == ['lint','preview','negative','go-version','go-race','go-vet','go-windows-crossbuild','go-fuzz','final']
assert all(s['exit_code'] == 0 and s['source_freeze_sha256'] == freeze_sha and s['pytest_plugins'] is None for s in statuses)
assert all(a['ended_utc'] <= b['started_utc'] for a, b in zip(statuses, statuses[1:]))
assert all(s['started_utc'] <= s['ended_utc'] for s in statuses)
for s in statuses:
    authenticate(out/(s['phase']+'.txt'))
assert statuses[-1]['command'] == ['./scripts/ci-hosted.sh', 'tests']
assert statuses[7]['command'] == ['go', 'test', '-run=^$', '-fuzz=FuzzBootOption', '-fuzztime=350000x', '-parallel=2']
assert (out/'go-version.txt').read_text().strip() == 'go version go1.26.8 linux/amd64'
all_cases = cases(out/'final.xml')+cases(out/'final.xml.orca.xml')
ids = [(c.get('classname'), c.get('name')) for c in all_cases]
assert len(ids) == len(set(ids)) == 10141
assert not any(c.find('failure') is not None or c.find('error') is not None for c in all_cases)
skips = {(c.get('classname'), c.get('name')): c.find('skipped').get('message','') for c in all_cases if c.find('skipped') is not None}
assert len(skips) == 14 and len(all_cases)-len(skips) == gate['passed'] == 10127
assert skips == {(r['classname'], r['name']): r['reason'] for r in gate['skips']}
prior = root/'docs/evidence/bug-audit-20261017-pass18/primary'
prior_hashes = read(prior/'raw-evidence-sha256.json')
with tarfile.open(prior/'raw-evidence.tar.gz') as archive:
    prior_cases = []
    for name in ('final.xml','final.xml.orca.xml'):
        raw = archive.extractfile(name).read()
        assert sha(raw) == prior_hashes[name]
        prior_cases.extend(ET.fromstring(raw).findall('.//testcase'))
assert set(skips) == {(c.get('classname'), c.get('name')) for c in prior_cases if c.find('skipped') is not None}
regressions = read(out/'new-tests-sha256.json')
assert len(regressions) == 59 and all(freeze[n] == h for n, h in regressions.items())
full_counts = {n: v for n, v in by_module(all_cases).items() if n in regressions}
assert len(full_counts) == 59 and sum(full_counts.values()) == 3924
assert full_counts == gate['regressions']
assert {n: full_counts[n] for n in new_names} == dict(original_counts)
assert not any(c.find('skipped') is not None for c in all_cases if 'tests/'+c.get('classname','').split('.')[-1]+'.py' in regressions)
for name, value in gate['report_sha256'].items():
    assert authenticate(out/name) == value
assert gate['failures'] == gate['errors'] == gate['duplicates'] == 0
binary = (out/'desktop-windows.test.exe').read_bytes()
offset = struct.unpack_from('<I',binary,0x3c)[0]
assert binary[:2] == b'MZ' and binary[offset:offset+4] == b'PE\0\0'
assert struct.unpack_from('<H',binary,offset+4)[0] == 0x8664 and struct.unpack_from('<H',binary,offset+24)[0] == 0x20b
assert len(binary) == gate['windows_crossbuild']['bytes'] == 9021440
assert authenticate(out/'desktop-windows.test.exe') == gate['windows_crossbuild']['sha256']
assert gate['windows_crossbuild']['native_acceptance'] is False

native = read(out/'native-final-readback.json')
expected_modules = {'tests.test_tk_native_boundary_pass20':24,'tests.test_tk_native_collector_pass20':4,'tests.test_tk_native_constructor_pass20':22,'tests.test_tk_native_image_pass20':3,'tests.test_tk_variable_interpreter_pass21':7,'tests.test_tk_trace_adoption_pass21':4}
observed = collections.Counter()
native_rows = []
direct = 0
tk_source = root/'src/beamo_wipe/ui/tk_wizard.py'
for c in all_cases:
    module = c.get('classname')
    if module not in expected_modules:
        continue
    props = []
    for p in c.iter('property'):
        try:
            row = json.loads(p.get('value'))
        except (TypeError, ValueError):
            continue
        if isinstance(row, dict) and 'returncode' in row:
            props.append(row)
    assert len(props) == 1
    row = props[0]
    assert row['returncode'] == 0 and not row['timed_out'] and row['stderr'] == ''
    assert '"event": "child-complete"' in row['stdout']
    if module not in {'tests.test_tk_native_boundary_pass20','tests.test_tk_native_collector_pass20'}:
        assert row['provenance'] == {'source':str(tk_source),'sha256':freeze[str(tk_source.relative_to(root))]}
        direct += 1
    for line in row['stdout'].splitlines():
        event = json.loads(line)
        assert event.get('event') != 'unraisable'
        assert not event.get('unraisables')
    observed[module] += 1
    native_rows.append(dict(module=module,name=c.get('name'),exit_code=0,stderr_bytes=0,timed_out=False,stdout_sha256=sha(row['stdout'].encode())))
assert dict(observed) == expected_modules and direct == 36 and len(native_rows) == 64
assert native['rows'] == native_rows and native['final_junit_sha256'] == gate['report_sha256']['final.xml']

campaign = read(out/'campaign-verification.json')
campaign_status = read(out/'campaign-status.json')
assert campaign['source_freeze_sha256'] == freeze_sha
assert campaign['gate_verification_sha256'] == authenticate(out/'gate-verification.json')
assert campaign['peer_review_sha256'] == authenticate(evidence/'runner/final-source-review.json')
assert campaign['campaign_status_sha256'] == authenticate(out/'campaign-status.json')
assert [s['phase'] for s in campaign_status] == ['runner-fresh','runner-cancel','geometry','reports']
assert all(s['exit_code'] == 0 and authenticate(s['command'][1]) == s['script_sha256'] for s in campaign_status)
assert campaign_status[0]['started_utc'] >= statuses[-1]['ended_utc']
assert all(a['ended_utc'] <= b['started_utc'] for a,b in zip(campaign_status,campaign_status[1:]))
fresh = read(runner/'fresh-summary.json')
assert fresh['short_cases'] == fresh['actual_large_cases'] == 153 and fresh['successful_roundtrips'] == 90 and fresh['mixed_advisory_traces'] == 54
assert fresh['mismatches'] == fresh['semantic_errors'] == fresh['native_acquisitions'] == 0 and fresh['source_unchanged']
assert not read(runner/'fresh-mismatches.json') and not read(runner/'fresh-semantic-errors.json')
assert all(freeze['src/beamo_wipe/'+n] == h for n,h in fresh['source'].items())
large = read(runner/'fresh-actual.json')
assert len(large) == 153
for i,row in enumerate(large,1):
    path = runner/'fixtures'/f'{i:04d}'/'fake.log'
    assert path.stat().st_size == row['bytes'] > 1024*1024 and authenticate(path) == row['sha256']
fixture_hashes = read(out/'runner-final-fixtures-sha256.json')
assert len(fixture_hashes) == 621
assert sum(n.startswith('fixtures/') for n in fixture_hashes) == 333
assert sum(n.startswith('cancellation/') for n in fixture_hashes) == 288
assert all(authenticate(runner/n) == h for n,h in fixture_hashes.items())
with tarfile.open(out/'runner-final-fixtures.tar.gz') as archive:
    members = archive.getmembers()
    assert len(members) == 621 and {m.name for m in members} == set(fixture_hashes)
    assert all(m.isfile() and sha(archive.extractfile(m).read()) == fixture_hashes[m.name] for m in members)
evidence_pairs = 0
for n in fixture_hashes:
    if n.endswith('.json'):
        raw = (runner/n).read_bytes()
        sidecar = (runner/(n+'.sha256')).read_text()
        assert sidecar.split()[0] == sha(raw)
        result = json.loads(raw)
        assert result['verification']['verified'] is (result['outcome'] == 'verified')
        evidence_pairs += 1
assert evidence_pairs == 90
cancel = read(runner/'cancel-summary.json')
assert cancel['cases'] == 144 and cancel['source_unchanged'] and cancel['native_acquisitions'] == 0
assert all(freeze['src/beamo_wipe/'+n] == h for n,h in cancel['source'].items())
cancel_rows = read(runner/'cancel-results.json')
assert len(cancel_rows) == len({r['index'] for r in cancel_rows}) == 144
for row in cancel_rows:
    assert Path(row['logfile']).parent == Path(row['lockfile']).parent == runner/'cancellation'/f"{row['index']:04d}"
    assert authenticate(row['logfile']) == row['log_sha256'] and row['free_after_terminal']
    assert row['retried'] == row['retained_on_uncertainty'] == (row['mode'] in {'never_exits','wait_error_once'})

geometry = read(ui/'geometry-matrix.json')
geo_summary = read(ui/'geometry-summary.json')
assert geometry['hashes'] == geo_summary['hashes'] == geo_summary['final_hashes']
assert all(freeze[n] == h for n,h in geometry['hashes'].items())
assert len(geometry['rows']) == geo_summary['cases'] == geo_summary['passed'] == 270
assert not geometry['forbidden_calls'] and not geo_summary['failed'] and not geo_summary['forbidden_calls']
assert all(r['ok'] and r['state_unchanged'] and not r['callback_errors'] for r in geometry['rows'])
critical = [r for r in geometry['rows'] if r['surface'] == 'tk' and r['screen'] in {'KEYBOARD','OWNER','CONFIRM'}]
assert len(critical) == 27 and all(r['focus_fully_visible'] for r in critical)
captures = [r['capture'] for r in geometry['rows'] if 'capture' in r]
capture_review = read(out/'primary-capture-review.json')
assert len(captures) == len(set(captures)) == 5 and captures == campaign['captures_for_primary_view'] == capture_review['reviewed']
for name in captures:
    raw = (ui/name).read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n' and authenticate(ui/name) == capture_review['sha256'][name]
    assert struct.unpack('>II',raw[16:24]) == (800,600)
report = read(out/'report-checks-matrix-artifacts.json')
assert report['cases'] == len(report['rows']) == 90 and report['runtime_source_sha256'] == source['runtime_source_sha256']
with tarfile.open(out/'report-artifacts.tar.gz') as archive:
    reports = {m.name:archive.extractfile(m).read() for m in archive if m.isfile()}
assert len(reports) == len(report['artifact_files']) == 70
assert {n:sha(b) for n,b in reports.items()} == report['artifact_files']
bundles = {Path(n).parts[0] for n in reports}
assert len(bundles) == 5
for bundle in bundles:
    payload = {n.split('/',1)[1]:b for n,b in reports.items() if n.startswith(bundle+'/')}
    manifest = json.loads(payload['COMPLETE'])
    assert set(payload) == set(manifest['files'])|{'COMPLETE'}
    assert all(sha(payload[n]) == h for n,h in manifest['files'].items())
    assert json.loads(payload['result.json'])['outcome'] == json.loads(payload['SHARE.json'])['outcome']
    assert '<html' in payload['REPORT.html'].decode().lower() and payload['RESULT.txt'] and payload['SHARE.txt']

native_campaign = read(out/'native-final-campaign-review.json')
repeated = read(out/'tk-pool-repeated-final.txt')
pressure = read(out/'tk-drain-gc-pressure-final.txt')
assert native_campaign['repeated'] == repeated
assert repeated['sessions'] == 10 and repeated['resources'] == repeated['finalizers'] == 220
assert repeated['all_owner_thread'] and repeated['all_returned'] and repeated['pools_empty']
assert repeated['max_gc_depth'] == repeated['registered_callbacks'] == 1 and not repeated['effects'] and not repeated['unraisables']
assert len(pressure['runs']) == 12 and not pressure['errors']
assert all(r['native_fonts'] == 128 and r['alive_after_owner_sweep'] == 0 for r in pressure['runs'])
for name,h in native_campaign['status_sha256'].items():
    assert authenticate(out/(name+'-status.json')) == h
    status = read(out/(name+'-status.json'))
    assert status['exit_code'] == 0 and status['started_utc'] >= statuses[-1]['ended_utc']
for name,h in native_campaign['log_sha256'].items():
    assert authenticate(out/(name+'.txt')) == h
for name,h in native_campaign['script_sha256'].items():
    assert authenticate(out/name) == h
assert repeated['provenance'] == native_campaign['provenance'] == {'source':str(tk_source),'sha256':freeze[str(tk_source.relative_to(root))]}
assert pressure['source'] == str(tk_source) and pressure['sha256'] == repeated['provenance']['sha256']
gtk = read(out/'gtk-owner-focus-final-review.json')
assert gtk['cases'] == len(gtk['rows']) == 9 and not gtk['forbidden_calls']
assert all(freeze[n] == h for n,h in gtk['source'].items())
assert {(r['language'],r['text_size']) for r in gtk['rows']} == {(l,s) for l in ('en','fr','de') for s in ('standard','large','extra')}
for row in gtk['rows']:
    x,y,w,h = row['owner_checkbox_rect']
    assert row['fully_visible'] and row['authorization_unchanged'] and row['tab_steps'] == 3
    assert all(x >= a and y >= b and x+w <= a+c and y+h <= b+d for a,b,c,d in row['viewport_clips'])
gtk_status = read(out/'gtk-owner-focus-final-status.json')
assert gtk_status['exit_code'] == 0 and gtk_status['started_utc'] >= campaign_status[-1]['ended_utc']
gtk_preparation = read(out/'gtk-owner-focus-preparation.json')
assert authenticate(out/'gtk-owner-focus-final.py') == gtk_preparation['sha256']
assert authenticate(root/gtk_preparation['original']) == gtk_preparation['original_sha256']
gtk_lines = []
for line in (out/'gtk-owner-focus-final.txt').read_text().splitlines():
    try:
        value = json.loads(line)
    except ValueError:
        continue
    if isinstance(value,dict) and 'rows' in value:
        gtk_lines.append(value)
assert gtk_lines == [gtk]

guards = read(out/'guard-manifest.json')
assert len(guards) == 8 and all(authenticate(n) == h for n,h in guards.items())
assert not (out/'forbidden-fallback-attempts.txt').exists()
permitted = [json.loads(line) for line in (out/'permitted-offline-gcloud.jsonl').read_text().splitlines()]
assert len(permitted) == gate['permitted_offline_sdk_calls'] == 1
assert all(r['command'][:2] == ['meta','list-files-for-upload'] and 'test_cloud_upload_excludes_local_captures_and_env_files' in r['test'] for r in permitted)
helper = read(out/'verification-helper-preparation.json')
assert all(authenticate(out/n) == h for n,h in helper['scripts'].items())
old_prep = read(out/'campaign-preparation.json')
new_prep = read(out/'campaign-preparation-v2.json')
assert authenticate(out/'campaign-preparation.json') == new_prep['supersedes_preparation_sha256']
for name,h in old_prep['files'].items():
    path = Path(name)
    if not path.is_absolute():
        path = root/path
    if name in new_prep['scripts']:
        assert authenticate(path) == new_prep['scripts'][name]
        original_text = path.read_text().replace('Pass21', 'Pass20', 1)
        assert sha(original_text.encode()) == h
        original_ast = ast.parse(original_text)
        new_ast = ast.parse(path.read_text())
        assert ast.dump(ast.Module(body=original_ast.body[1:],type_ignores=[]),include_attributes=False) == ast.dump(ast.Module(body=new_ast.body[1:],type_ignores=[]),include_attributes=False)
    else:
        assert authenticate(path) == h

# Compare the complete index's reconstructed root tree ID with HEAD. This
# stdlib calculation needs no git process or packed-object access.
git = root/'.git'
head_ref = (git/'HEAD').read_text().strip()
assert head_ref == 'ref: refs/heads/fix/safety-audit-20261015'
head = (git/head_ref[5:]).read_text().strip()
assert head == source['head']
obj = zlib.decompress((git/'objects'/head[:2]/head[2:]).read_bytes())
assert hashlib.sha1(obj).hexdigest() == head
header,commit = obj.split(b'\0',1)
assert header.startswith(b'commit ')
head_tree = commit.split(b'\n',1)[0].split()[1].decode()
index = (git/'index').read_bytes()
assert hashlib.sha1(index[:-20]).digest() == index[-20:]
magic,version,count = struct.unpack('>4sII',index[:12])
assert magic == b'DIRC' and version == 2
trie = {}
pos = 12
for _ in range(count):
    start_pos = pos
    entry = index[pos:pos+62]
    mode = struct.unpack_from('>I',entry,24)[0]
    oid = entry[40:60]
    flags = struct.unpack_from('>H',entry,60)[0]
    assert not flags & 0x4000 and ((flags>>12)&3) == 0
    end = index.index(b'\0',pos+62)
    name = index[pos+62:end]
    pos = start_pos+((end+1-start_pos+7)//8)*8
    cursor = trie
    parts = name.split(b'/')
    for part in parts[:-1]:
        cursor = cursor.setdefault(part,{})
    assert parts[-1] not in cursor
    cursor[parts[-1]] = (mode,oid)


def index_tree(tree):
    result = []
    for name,value in tree.items():
        if isinstance(value,dict):
            result.append((name+b'/',b'40000 '+name+b'\0'+bytes.fromhex(index_tree(value))))
        else:
            mode,oid = value
            result.append((name,f'{mode:o} '.encode()+name+b'\0'+oid))
    raw = b''.join(value for _,value in sorted(result))
    return hashlib.sha1(f'tree {len(raw)}\0'.encode()+raw).hexdigest()


assert index_tree(trie) == head_tree
index_review = dict(head=head,head_tree=head_tree,index_entries=count,index_sha256=sha(index),staged_changes=0,method='Independent stdlib Git index root-tree reconstruction; HEAD loose commit authenticated; no git process')
readme = (evidence/'README.md').read_text()
assert '10,127' in readme and '89 failures and 130' in readme and '3,924' in readme
assert 'NOT RUN / BLOCKED' in readme and 'remain unattributed' in readme
assert 'retention-verification.json' in readme and 'SHA256SUMS' in readme
assert not (evidence/'primary/retention-verification.json').exists()
assert not (evidence/'SHA256SUMS').exists()
record = dict(reviewed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reviewer='Codex /root/pass21_runner_reports',method='Independent stdlib file/AST/XML/archive/Git-index readback only; no app imports, tests, GUI/native commands, network or frozen source edits',verdict='PASS current source/gates/native/campaign/readback claims; retention and final manifest acceptance PENDING',source_freeze_sha256=freeze_sha,runtime_source_sha256=digest.hexdigest(),frozen_inputs=788,starting_inputs=779,unchanged_starting_inputs=775,reviewed_inputs=13,original=dict(cases=219,failures=89,controls=130,errors=0,skips=0,source_files=58),focused=dict(passed=290,canonical=219,errors=0,failures=0,skips=0,invalid_selection_exit4_preserved=True),full_gate=dict(fresh_phases=9,passed=10127,skipped=14,duplicates=0,errors=0,failures=0,audit_modules=59,audit_cases=3924,exact_prior_skip_ids=True,exact_new219_cases=True,windows_crossbuild_bytes=9021440,native_windows_acceptance=False),native=dict(children=64,direct_source_provenance=36,inherited_admitted_environment=28,zero_exits=64,empty_stderr=64,timeouts=0,reported_unraisables=0,sessions=10,original_creator_finalizers=220,pressure_runs=12,fonts_per_pressure_run=128),campaigns=dict(short_logs=153,actual_large_logs=153,evidence_sidecar_pairs=90,advisory_traces=54,cancel_retry_cases=144,fixture_files=621,report_cases=90,bundle_files=70,bundles=5,geometry_views=270,critical_tk_focus_views=27,captures_hashed=5,root_visual_review_recorded=True,delegate_visual_inspection=False,gtk_followup=9,gtk_tabs=3,source_and_artifact_archive_readback=True),guards=dict(forbidden_fallbacks=0,permitted_owned_offline_gcloud_calls=1,guard_files=8),index=index_review,readme_sha256=authenticate(evidence/'README.md'),helper_preparation_verified=True,campaign_preparation_docstring_only_changes_verified=True,retention='PENDING; root must retain/hash/reread final manifest after this review',platform_limits=['Python3.11/live-bookworm','ISO/QEMU','native Windows','firmware','physical reconnect/readback','hardware'],historical_limits=['pass19 two uncanceled native aborts unattributed','pass18 original GTK latency','pass16 loop incident','pass8 SIGTERM attribution','pass9 original timing trace'],authenticated_file_hashes=hashed)
target = evidence/'runner/final-verification-review.json'
assert not target.exists()
target.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
print(json.dumps({k:v for k,v in record.items() if k != 'authenticated_file_hashes'},indent=2))
print('authenticated_files',len(hashed),'review_sha256',sha(target.read_bytes()))
