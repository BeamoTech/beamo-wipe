import ast
from pathlib import Path
p=Path('src/beamo_wipe/ui/tk_wizard.py');s=p.read_text();old='''    try:
        factory.__init__(resource, *args, **kwargs)
    except BaseException:
        owner = threading.current_thread()
        _pin_retired_assets((resource,), owner)
        _pin_retired_interpreter(native_root, owner)
        raise
''';new='''    owner = threading.current_thread()
    # Own successful local resources too: a later widget initializer can fail
    # before the caller adopts them into its teardown graph.
    _pin_retired_assets((resource,), owner)
    _pin_retired_interpreter(native_root, owner)
    if isinstance(resource, _TK_ASSET_CLASSES[2]) and "name" not in resource.__dict__:
        # Image.__init__ normally establishes this before allocating a handle.
        # Preserve the original destructor when initialization fails earlier.
        resource.name = None
    factory.__init__(resource, *args, **kwargs)
''';assert s.count(old)==1;s=s.replace(old,new);old='if self._ui_dead or self.w.screen != expected_screen';assert s.count(old)==1;s=s.replace(old,'if getattr(self, "_ui_dead", False) or self.w.screen != expected_screen');p.write_text(s)
p=Path('tests/test_tk_native_constructor_pass20.py');old=p.read_text();v=Path('docs/evidence/bug-audit-20261017-pass20/tk-lifetime/constructor-boundary-probe-v5.py').read_text()
def function(text,name):
 n=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name);lines=text.splitlines(True);return ''.join(lines[n.lineno-1:n.end_lineno])
v=v[v.index('import gc'):];v='# SPDX-License-Identifier: GPL-3.0-or-later\n"""Native constructor, retained-exception and startup ownership regressions."""\n\n'+v
for name in ['_admit','test_partial_native_and_row_constructor_releases_ownership']:v=v.replace(function(v,name),function(old,name))
p.write_text(v)
p=Path('tests/test_tk_native_image_pass20.py');v=Path('docs/evidence/bug-audit-20261017-pass20/tk-lifetime/image-preinit-boundary-probe.py').read_text();v='# SPDX-License-Identifier: GPL-3.0-or-later\n"""Native PhotoImage partial initialization and original finalizer regressions."""\n\n'+v[v.index('import gc'):];v=v.replace(function(v,'_admit'),function(old,'_admit'));v=v.replace('env=dict(os.environ, PYTHONFAULTHANDLER="1")','env=dict(os.environ, PYTHONFAULTHANDLER="1",\n                                         BEAMO_TK_PROBE_SOURCE=provenance["source"],\n                                         BEAMO_TK_PROBE_SHA256=provenance["sha256"])');p.write_text(v)
