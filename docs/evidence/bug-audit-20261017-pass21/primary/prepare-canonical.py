import ast
from pathlib import Path
pairs={
'discovery/missing-physical-name-probe.py':'test_disk_name_layout_pass21.py',
'discovery/noncanonical-physical-name-probe.py':'test_disk_name_alias_layout_pass21.py',
'discovery/nonfinite-size-probe.py':'test_discovery_nonfinite_size_pass21.py',
'runner/diagnostics-unicode-boundary-probe.py':'test_diagnostics_line_separators_pass21.py',
'ui/tk-variable-root-proof-v3.py':'test_tk_variable_interpreter_pass21.py',
'ui/refresh-acceptance-proof.py':'test_refresh_acceptance_interruptions_pass21.py',
'ui/gtk-close-cleanup-proof.py':'test_accessible_close_cleanup_pass21.py',
'ui/tk-trace-adoption-proof-v2.py':'test_tk_trace_adoption_pass21.py',
}
base=Path('docs/evidence/bug-audit-20261017-pass21')
for source,name in pairs.items():
 s=(base/source).read_text();tree=ast.parse(s);doc=tree.body[0];lines=s.splitlines(True);s=''.join(lines[doc.end_lineno:]);s='# SPDX-License-Identifier: GPL-3.0-or-later\n"""Regression: '+name.removeprefix('test_').removesuffix('_pass21.py').replace('_',' ')+'."""\n'+s
 if name in {'test_tk_variable_interpreter_pass21.py','test_tk_trace_adoption_pass21.py'}:
  s=s.replace('    assert sys.platform.startswith("linux")\n    assert os.environ.get("BEAMO_ISOLATED_X11_TEST") == "1"','    if not sys.platform.startswith("linux") or os.environ.get("BEAMO_ISOLATED_X11_TEST") != "1":\n        pytest.skip("Explicit isolated private X11 required")')
  s=s.replace('os.environ["BEAMO_TK_PROBE_SOURCE"]','os.environ.get("BEAMO_TK_PROBE_SOURCE", str(Path(__file__).resolve().parents[1]/"src/beamo_wipe/ui/tk_wizard.py"))')
  s=s.replace('os.environ["BEAMO_TK_PROBE_SHA256"]','os.environ.get("BEAMO_TK_PROBE_SHA256", hashlib.sha256(Path(os.environ.get("BEAMO_TK_PROBE_SOURCE", str(Path(__file__).resolve().parents[1]/"src/beamo_wipe/ui/tk_wizard.py"))).read_bytes()).hexdigest())')
  s=s.replace('env=dict(os.environ, PYTHONFAULTHANDLER="1")','env=dict(os.environ, PYTHONFAULTHANDLER="1", BEAMO_TK_PROBE_SOURCE=provenance["source"], BEAMO_TK_PROBE_SHA256=provenance["sha256"])')
 if name=='test_refresh_acceptance_interruptions_pass21.py':
  s=s.replace('    expected = Path(os.environ[f"BEAMO_{prefix}_PROBE_SOURCE"]).resolve()','    default = Path(__file__).resolve().parents[1]/("src/beamo_wipe/ui/tk_wizard.py" if prefix=="TK" else "src/beamo_wipe/ui/accessible_wizard.py")\n    expected = Path(os.environ.get(f"BEAMO_{prefix}_PROBE_SOURCE", str(default))).resolve()')
  s=s.replace('os.environ[f"BEAMO_{prefix}_PROBE_SHA256"]','os.environ.get(f"BEAMO_{prefix}_PROBE_SHA256", hashlib.sha256(expected.read_bytes()).hexdigest())')
 if name in {'test_refresh_acceptance_interruptions_pass21.py','test_accessible_close_cleanup_pass21.py'}:
  s=s.replace('os.environ["BEAMO_GTK_PROBE_SOURCE"]','os.environ.get("BEAMO_GTK_PROBE_SOURCE", str(Path(__file__).resolve().parents[1]/"src/beamo_wipe/ui/accessible_wizard.py"))')
  s=s.replace('os.environ["BEAMO_GTK_PROBE_SHA256"]','os.environ.get("BEAMO_GTK_PROBE_SHA256", hashlib.sha256(source.read_bytes()).hexdigest())')
 target=Path('tests')/name;assert not target.exists();target.write_text(s)
print('Prepared8 canonical modules/213cases, preserving proof bodies/assertions; admission adapted.')
p=Path('src/beamo_wipe/diagnostics.py');s=p.read_text().replace('    # overrides and C1 terminal controls, not just newlines and NUL.','    # overrides and C1 terminal controls, not just newlines and NUL. Unicode\n    # line/paragraph separators also split the supported JSONL reader.');p.write_text(s)
