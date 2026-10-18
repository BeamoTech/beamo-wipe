"""Read-only trace of the four PR90 archived-report CodeQL findings."""
import ast
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import tarfile

ROOT = Path('/root/dev/Beamo Wipe')
OUT = Path(__file__).parent


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.support_text = []
        self.url_attributes = []

    def handle_data(self, data):
        if 'beamosupport.com' in data:
            self.support_text.append(data)

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src', 'action', 'formaction', 'data', 'srcset'):
                self.url_attributes.append([tag, key, value])


records = []
for number, stamp in ((32, '20261016-pass13'), (35, '20261016-pass14'),
                      (34, '20261016-pass15'), (33, '20261017-pass16')):
    base = ROOT / f'docs/evidence/bug-audit-{stamp}/primary'
    script = base / 'review-artifacts.py'
    raw = script.read_bytes()
    committed = subprocess.run(['git', 'show', 'HEAD:' + str(script.relative_to(ROOT))],
                               check=True, capture_output=True).stdout
    assert raw == committed
    tree = ast.parse(raw)
    matches = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)
               and ast.dump(node.test) == ast.dump(ast.parse(
                   "'beamosupport.com' in html", mode='eval').body)]
    assert len(matches) == 1
    alert = json.loads((OUT / f'alert-{number}-before.json').read_text())
    location = alert['most_recent_instance']['location']
    assert location['path'] == str(script.relative_to(ROOT))
    assert location['start_line'] == matches[0].lineno
    matrix = json.loads((base / 'report-checks-matrix-artifacts.json').read_text())
    assert len(matrix['artifact_files']) == 70
    cases = []
    with tarfile.open(base / 'report-artifacts.tar.gz', 'r:gz') as archive:
        assert set(archive.getnames()) == set(matrix['artifact_files'])
        for name, expected in matrix['artifact_files'].items():
            assert hashlib.sha256(archive.extractfile(name).read()).hexdigest() == expected
        for case in ('unknown-count', 'write-error', 'read-error', 'verify-error'):
            name = case + '/REPORT.html'
            content = archive.extractfile(name).read().decode()
            parser = ReportParser()
            parser.feed(content)
            parser.close()
            assert parser.support_text
            assert parser.url_attributes == []
            cases.append({'case': case, 'visible_support_text': parser.support_text,
                          'url_attributes': parser.url_attributes})
    records.append({'alert': number, 'file': location['path'], 'line': matches[0].lineno,
                    'script_sha256': hashlib.sha256(raw).hexdigest(),
                    'committed_bytes_unchanged': True, 'authenticated_artifacts': 70,
                    'failed_reports': cases,
                    'assessment': 'false positive: HTML content assertion; no URL input, '
                                  'parsing, allowlist, redirection or network sink'})
receipt = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
           'findings': records}
(OUT / 'trace-findings.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'findings': len(records), 'artifacts_authenticated': 280,
                  'failed_reports_parsed': 16, 'network_url_attributes': 0,
                  'scripts_match_commit': True}))
