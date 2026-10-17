from pathlib import Path
import collections,hashlib,json,re,shutil,xml.etree.ElementTree as E
root=Path.cwd();ev=root/'docs/evidence/bug-audit-20261016-pass8'
log=Path('/tmp/beamo-pass8-final2.txt').read_text();assert '[ci-hosted] PASS phase=tests' in log
seen=set();groups=[];skips=[]
for name in ['final2.xml','final2.xml.orca.xml']:
    document=E.parse('/tmp/beamo-pass8-'+name).getroot();cases=document.findall('.//testcase');assert cases
    for case in cases:
        ident=(case.get('classname',''),case.get('name',''));assert ident not in seen,ident;seen.add(ident)
        assert case.find('failure') is None and case.find('error') is None,ident
        skipped=case.find('skipped')
        if skipped is not None:skips.append({'id':'.'.join(ident),'reason':skipped.get('message','')})
    groups.append({'report':name,'tests':len(cases),'passed':sum(c.find('skipped') is None for c in cases),'skipped':sum(c.find('skipped') is not None for c in cases),'junit_seconds':sum(float(s.get('time','0')) for s in document.findall('testsuite'))})
assert len(seen)==6237 and len(skips)==14,(len(seen),len(skips))
assert collections.Counter('.'.join(s['id'].split('.')[:2]) for s in skips)=={'tests.test_live_image':2,'tests.test_release_manifest':12}
frozen=json.loads(Path('/tmp/beamo-pass8-frozen-source.json').read_text())
for p,h in frozen.items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
for phase in ['lint','preview','negative']:assert '[ci-hosted] PASS phase='+phase in Path('/tmp/beamo-pass8-'+phase+'.txt').read_text()
assert 'PASS' in Path('/tmp/beamo-pass8-go-fuzz.txt').read_text()
summary={'baseline':'35107a8d1a701093eac876a58ab4efd50e291673','groups':groups,'unique_passed':len(seen)-len(skips),'skipped':skips,'failures':0,'errors':0,'duplicate_case_ids':0,'frozen_source_hashes_match':True,'runtime_source_sha256':Path('/tmp/beamo-pass8-runtime-digest.txt').read_text().strip(),'implementation':'pending commit','source_branch_pushed':False,'hosted_ci_dispatched':False,'release_published':False}
(ev/'final-summary.json').write_text(json.dumps(summary,indent=2)+'\n');shutil.copyfile('/tmp/beamo-pass8-final2.txt',ev/'final-tests.txt')
wall=re.findall(r'6222 passed, 14 skipped in ([0-9.]+)s',log);assert len(wall)==1,wall
p=ev/'README.md';s=p.read_text();start=s.index('Full frozen-source pytest/private-Orca gate is running.');end=s.index('## Harness history and limits',start)
s=s[:start]+f'''Final frozen-source local gate passed:

- [Main pytest](final-tests.txt): **6,222 passed /14 expected image-only skips**,
  no failures/errors, in {wall[0]}s; mandatory GTK result guard passed.
- Separate private Orca: **1 passed**, giving **6,223 unique passes**. The
  [JUnit-derived summary](final-summary.json) confirms no duplicate IDs and
  lists every skip: two generated lb-config and twelve manufacturing-ISO cases.
- [Lint/types/security/shell/developer formatting](lint.txt), [preview](preview.txt)
  and [private negative safety mutation](negative.txt) passed.
- Pinned [Go1.26.8](go-version.txt) [uncached race](go-race.txt), [vet](go-vet.txt)
  and [350,000 fuzz executions](go-fuzz.txt) passed. Native inventory stayed unset.
- All [four frozen source/test hashes](source-sha256.txt) match tested bytes.
  Runtime source digest: `{summary['runtime_source_sha256']}`.

The unchanged TODO-regex warning in release_manifest.py:40 and mypy untyped-body
notes are informational; no material lint/type warning remains. The local
ci-hosted.sh tests invocation used BEAMO_GATE_CHILD=1, pinned Go and the no-space
Python-venv alias on PATH, GOTOOLCHAIN=local, and explicit scratch JUnit paths.
Suite/Orca ran in private XDG/D-Bus/Xvfb sessions at72DPI. No dependency upgrade,
hosted execution or source/test change after final freeze was involved.

'''+s[end:];p.write_text(s)
print(json.dumps({'groups':groups,'unique_passed':summary['unique_passed'],'skips':len(skips),'hashes_match':True},indent=2))
