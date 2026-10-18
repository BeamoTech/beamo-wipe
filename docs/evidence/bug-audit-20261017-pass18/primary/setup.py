import gzip, hashlib, io, json, os, subprocess, tarfile
from pathlib import Path

root=Path.cwd()
evidence=root/'docs/evidence/bug-audit-20261017-pass18/primary'
evidence.mkdir(parents=True,exist_ok=True)
out=Path('/tmp/pass18-primary');out.mkdir(mode=0o700)
alias=Path('/tmp/beamo-pass18-python')
assert not os.path.lexists(alias)
alias.symlink_to(root/'.venv-linux',target_is_directory=True)
guard=Path('/tmp/beamo-pass18-fallback-guard');guard.mkdir(mode=0o700)
prior=root/'docs/evidence/bug-audit-20261017-pass17/primary'
for filename in ('interpreter-path-probe.py','probe-fallback-guard.py','run-gates.py'):
    (out/filename).write_text((prior/filename).read_text().replace('pass17','pass18').replace('PASS17','PASS18'))
for name in ('curl','sudo','losetup','docker','qemu-system-x86_64','gh','gcloud','aws'):
    template='guards/'+name
    path=guard/name
    path.write_text((prior/template).read_text().replace('pass17','pass18'))
    path.chmod(0o700)
manifest={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(guard.iterdir())}
(out/'guard-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z']).decode().split('\0')
prefixes=('src/','tests/','developer_tests/','scripts/','packaging/','desktop/','helper/','.github/')
selected=sorted({n for n in names if n.startswith(prefixes) or n in {'dev.py','preview','pyproject.toml'}})
freeze={n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in selected}
(out/'starting-freeze.json').write_text(json.dumps(freeze,indent=2)+'\n')
priorfreeze=json.loads((prior/'source-freeze.json').read_text())
delta={n:dict(prior=priorfreeze.get(n),current=freeze.get(n)) for n in sorted(set(freeze)|set(priorfreeze)) if freeze.get(n)!=priorfreeze.get(n)}
assert not delta,delta
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as arc:
    for n in selected:
        data=(root/n).read_bytes();info=tarfile.TarInfo(n);info.size=len(data);info.mtime=0
        arc.addfile(info,io.BytesIO(data))
(out/'starting-inputs.tar.gz').write_bytes(gzip.compress(buf.getvalue(),mtime=0))
(out/'starting-diff.patch').write_bytes(subprocess.check_output(['git','diff','--','src','tests']))
(out/'starting-status.txt').write_bytes(subprocess.check_output(['git','status','--short']))
assert not subprocess.check_output(['git','diff','--cached','--name-only'])
receipt=dict(head=subprocess.check_output(['git','rev-parse','HEAD']).decode().strip(),branch=subprocess.check_output(['git','branch','--show-current']).decode().strip(),frozen_inputs=len(freeze),delta_from_pass17=delta,shared_guide='absent; previously acknowledged',new_alias=str(alias),fallback_guard=str(guard),environment_status_tool='not exposed in current tool catalog',hosted_or_privileged_actions=False)
(out/'starting-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
record=root/'.ai/memory/unfinished-work.md'
text=record.read_text()
entry='''## BW-BUG-AUDIT-20261017-PASS18 — IN PROGRESS (fresh audit; previous acceptance blockers retained)

- Date/author: 2026-10-17 / Codex. Request: another comprehensive pass.
- Repo/worktree: BeamoTech/beamo-wipe; `/root/dev/Beamo Wipe`; branch
  `fix/safety-audit-20261015`; HEAD `35107a8d1a701093eac876a58ab4efd50e291673`.
- Baseline: 762 source/test/build inputs exactly match final pass17 freeze;
  all previous uncommitted fixes/tests preserved; index empty.
- Work: three bounded source audits (discovery/safety, runner/recovery,
  UI/boot/build), primary harness isolation and reports/audio/power review.
- Remaining acceptance: prove any new candidate before changing product code,
  regressions/adjacent cases, complete applicable local gate, final source and
  artifact review. Use no-space interpreter and rejecting child-PATH guards.
- Blockers retained: pass17 loop-test boundary incident review, pass8 original
  unexplained SIGTERM and pass9 original timing trace. ISO/QEMU/native Windows/
  physical/firmware acceptance remain NOT RUN/BLOCKED on this host.
- Next action: validate harmless interpreter/guard probes, then serialize fake
  runtime campaigns. No commit/push/hosted job/release authorized by evidence.
- Evidence/result in progress: `docs/evidence/bug-audit-20261017-pass18/`;
  `/tmp/pass18-primary/` is working staging, retained before handoff.

'''
assert 'BW-BUG-AUDIT-20261017-PASS18' not in text
record.write_text(text.replace('# Unfinished work\n','# Unfinished work\n\n'+entry,1))
for filename in ('starting-receipt.json','starting-freeze.json','guard-manifest.json'):
    (evidence/filename).write_bytes((out/filename).read_bytes())
print(json.dumps(receipt,indent=2))
