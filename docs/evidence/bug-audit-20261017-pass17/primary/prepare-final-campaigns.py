from pathlib import Path
root=Path.cwd();out=Path('/tmp/pass17-primary');ui=Path('/tmp/pass17-ui')
ui.mkdir(mode=0o700)
prior=root/'docs/evidence/bug-audit-20261017-pass16'
for name in ('geometry-matrix.py','run-geometry.py'):
    (ui/name).write_text((prior/'ui'/name).read_text().replace('pass16','pass17'))
(out/'report-checks-matrix.py').write_text((prior/'primary/report-checks-matrix.py').read_text().replace('pass16','pass17').replace('2026/10/16','2026/10/17'))
print('Prepared fresh geometry and report campaigns; no runtime executed')
