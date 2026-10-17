import ast
import difflib
import hashlib
import json
from pathlib import Path

base = Path('/tmp/pass20-primary/private-graph-candidate3.py')
raw = base.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'b3d66bdb83213000c9623a2a48c25cf39b089289a388aba67507f117b4a59546'
source = raw.decode()

pool_start = source.index('# Closed Tcl interpreters can remain in preserved traceback/widget cycles.')
pool_end = source.index('\n\nclass TkWizard:', pool_start)
source = source[:pool_start] + '''# Retained frames and peer observers can outlive a closed window. Keep their
# native resources until the creating thread can release the final reference.
_TK_ROOT_CLASS = tk.Tk
_TK_ASSET_CLASSES = (tkfont.Font, tk.Variable, tk.Image)
_RETIRED_INTERPRETERS: list[tuple[threading.Thread, object]] = []
_RETIRED_NATIVE_ASSETS: list[tuple[threading.Thread, object]] = []


def _pin_retired_interpreter(root: tk.Misc, owner: threading.Thread | None = None) -> None:
    interpreter = getattr(root, "tk", None)
    if interpreter is not None and not any(record[1] is interpreter for record in _RETIRED_INTERPRETERS):
        _RETIRED_INTERPRETERS.append((owner or threading.current_thread(), interpreter))


def _pin_retired_assets(assets, owner: threading.Thread) -> None:
    for asset in assets:
        if isinstance(asset, _TK_ASSET_CLASSES) and not any(record[1] is asset for record in _RETIRED_NATIVE_ASSETS):
            _RETIRED_NATIVE_ASSETS.append((owner, asset))


def _drain_retired_assets() -> None:
    owner = threading.current_thread()
    for record in _RETIRED_NATIVE_ASSETS[:]:
        # The tuple owns one asset reference; getrefcount adds its argument.
        if record[0] is owner and sys.getrefcount(record[1]) == 2:
            _RETIRED_NATIVE_ASSETS.remove(record)


def _drain_retired_interpreters() -> None:
    owner = threading.current_thread()
    for record in _RETIRED_INTERPRETERS[:]:
        if record[0] is owner and sys.getrefcount(record[1]) == 2:
            _RETIRED_INTERPRETERS.remove(record)


def _drain_retired_native() -> None:
    # The asset helper must return first: its loop/snapshot tuple references
    # can otherwise keep the last asset's raw interpreter alive for this pass.
    _drain_retired_assets()
    _drain_retired_interpreters()


def _collect_retired_interpreters() -> None:
    gc.collect()
    _drain_retired_native()


def _note_tk_cleanup_failure(original: BaseException, cleanup: BaseException) -> None:
    # Keep the original failure/traceback; report the distinct cleanup failure.
    add_note = getattr(original, "add_note", None)
    if callable(add_note):
        add_note(f"Tk cleanup also failed: {type(cleanup).__name__}")
    try:
        from beamo_wipe.diagnostics import log_diag
        log_diag("ui", "tk_cleanup_failed", type(cleanup).__name__)
    except Exception:
        pass


def _retire_tk_owner(owner, original: BaseException | None = None) -> None:
    try:
        owner._teardown()
    except BaseException as cleanup:
        if original is None:
            raise
        _note_tk_cleanup_failure(original, cleanup)


def _new_owned_root(owner: threading.Thread):
    factory = tk.Tk
    if not isinstance(factory, type) or not issubclass(factory, _TK_ROOT_CLASS):
        return factory()  # Callable lightweight test factories retain their contract.
    root = factory.__new__(factory)
    if not isinstance(root, factory):
        return root
    try:
        factory.__init__(root)
    except BaseException as original:
        _pin_retired_interpreter(root, owner)
        if getattr(root, "tk", None) is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass
            except BaseException as cleanup:
                _note_tk_cleanup_failure(original, cleanup)
        raise
    return root


def _new_owned_native(root, factory, *args, **kwargs):
    if not isinstance(factory, type) or not issubclass(factory, _TK_ASSET_CLASSES):
        return factory(*args, **kwargs)
    resource = factory.__new__(factory)
    if not isinstance(resource, factory):
        return resource
    try:
        factory.__init__(resource, *args, **kwargs)
    except BaseException:
        owner = threading.current_thread()
        _pin_retired_assets((resource,), owner)
        _pin_retired_interpreter(root, owner)
        raise
    return resource
''' + source[pool_end:]

old = '''        _collect_retired_interpreters()
        self._native_retired = False
        try:
            self.w = wizard
            self.root = tk.Tk()
'''
new = '''        _collect_retired_interpreters()
        self._native_owner = threading.current_thread()
        self._native_retired = False
        try:
            self.w = wizard
            self.root = _new_owned_root(self._native_owner)
'''
assert source.count(old) == 1
source = source.replace(old, new)
old = '''        except BaseException:
            self._teardown()
            raise
'''
new = '''        except BaseException as original:
            _retire_tk_owner(self, original)
            raise
'''
assert source.count(old) == 1
source = source.replace(old, new)

row_start = source.index('class _CheckRow(')
row_init = source.index('        bg = parent.cget("bg")', row_start)
source = source[:row_init] + '        self._native_owner = threading.current_thread()\n' + source[row_init:]
start = source.index('    def _retire_variable_trace(self, event) -> None:', row_start)
end = source.index('\n    def _row_bg(self)', start)
source = source[:start] + '''    def _retire_native_refs(self) -> None:
        owner = getattr(self, "_native_owner", threading.current_thread())
        variable = getattr(self, "_variable", None)
        font = getattr(self, "_font", None)
        _pin_retired_assets((variable, font), owner)
        _pin_retired_interpreter(self, owner)
        token = getattr(self, "_variable_trace", None)
        self._variable_trace = None
        try:
            if token is not None and variable is not None:
                variable.trace_remove("write", token)
        except tk.TclError:
            pass
        finally:
            self._command = lambda: None
            for name in ("_variable", "_font", "_label", "_icon"):
                setattr(self, name, None)

    def _retire_variable_trace(self, event) -> None:
        if event.widget is self:
            self._retire_native_refs()

    def destroy(self) -> None:
        try:
            super().destroy()
        finally:
            # Also covers constructor failures before the Destroy binding.
            self._retire_native_refs()
            _drain_retired_native()
''' + source[end:]

start = source.index('    def _teardown(self) -> None:', source.index('class TkWizard:'))
end = source.index('\n    def _tick(self)', start)
source = source[:start] + '''    def _teardown(self) -> None:
        if getattr(self, "_native_retired", False) or getattr(self, "_retiring", False):
            return
        self._retiring = True
        self._ui_dead = True
        owner_thread = getattr(self, "_native_owner", threading.current_thread())
        root = getattr(self, "root", None)
        if isinstance(root, tk.Misc):
            _pin_retired_interpreter(root, owner_thread)
        pins = [getattr(self, name, None) for name in self._NATIVE_ASSETS]
        _pin_retired_assets(pins, owner_thread)
        cleanup_error = None
        try:
            pending = [root] if isinstance(root, tk.Misc) else []
            widget = None
            while pending:
                widget = pending.pop()
                if isinstance(widget, _CheckRow):
                    pins.extend((getattr(widget, "_variable", None), getattr(widget, "_font", None)))
                try:
                    pending.extend(widget.winfo_children())
                except tk.TclError:
                    pass
            widget = None
            _pin_retired_assets(pins, owner_thread)
            for variable_name, token_name in (
                ("_confirm_var", "_confirm_var_trace"), ("_typing_var", "_typing_var_trace"),
            ):
                token = getattr(self, token_name, None)
                variable = getattr(self, variable_name, None)
                if token is not None:
                    setattr(self, token_name, None)
                    if variable is not None:
                        try:
                            variable.trace_remove("write", token)
                        except tk.TclError:
                            pass
            variable = None
            try:
                getattr(self.w, "cancel_audio", lambda: None)()
            except BaseException as error:
                cleanup_error = error
            self._cancel_pick_restore()
            for attr in ("_return_release_after", "_space_release_after", "_after_id"):
                callback = getattr(self, attr, None)
                if callback is not None and root is not None:
                    try:
                        root.after_cancel(callback)
                    except tk.TclError:
                        pass
                    setattr(self, attr, None)
            if root is not None:
                self._cancel_widget_callbacks(root)
                try:
                    root.destroy()
                except tk.TclError:
                    pass
                if getattr(root, "_tk_wizard", None) is self:
                    del root._tk_wizard
            for name in self._NATIVE_FIELDS:
                if hasattr(self, name):
                    setattr(self, name, {} if name in ("_pick_cards", "_keyboard_layout_cards", "_keyboard_language_cards") else None)
            lock = getattr(self, "_refresh_lock", None)
            if lock is not None:
                with lock:
                    self._refresh_results.clear()
                    self._refresh_threads.clear()
            self._native_retired = True
            gc.collect()
        finally:
            pins.clear()
            root = None
            self._retiring = False
            _collect_retired_interpreters()
        if cleanup_error is not None:
            raise cleanup_error
''' + source[end:]

# Wrap only explicitly owned constructor calls in this module. The original
# factory arguments are preserved, including current default-master variables.
source = source.replace('tkfont.Font(root=self.root,', '_new_owned_native(self.root, tkfont.Font, root=self.root,')
source = source.replace('self._confirm_var = tk.StringVar()', 'self._confirm_var = _new_owned_native(self.root, tk.StringVar)')
source = source.replace('self._typing_var = tk.StringVar()', 'self._typing_var = _new_owned_native(self.root, tk.StringVar)')
source = source.replace('self._owner_var = tk.IntVar(value=0)', 'self._owner_var = _new_owned_native(self.root, tk.IntVar, value=0)')
source = source.replace('opened = tk.BooleanVar(value=False)', 'opened = _new_owned_native(self.root, tk.BooleanVar, value=False)')
source = source.replace('choice = tk.BooleanVar(master=self.root, value=self.w.report_wanted)', 'choice = _new_owned_native(self.root, tk.BooleanVar, master=self.root, value=self.w.report_wanted)')
source = source.replace('share = tk.BooleanVar(master=self.root, value=self.w.report_share_redacted)', 'share = _new_owned_native(self.root, tk.BooleanVar, master=self.root, value=self.w.report_share_redacted)')
source = source.replace('return tk.PhotoImage(master=self.root, file=str(_ASSETS / name))', 'return _new_owned_native(self.root, tk.PhotoImage, master=self.root, file=str(_ASSETS / name))')
source = source.replace('image = tk.PhotoImage(\n                master=self.root,', 'image = _new_owned_native(\n                self.root, tk.PhotoImage, master=self.root,')

# Avoid full collection in screen rendering; drain only already sole-owned
# wrappers whose exact row references were retired while clearing the old view.
old = '''        self._draw_strip()
        self._shown = screen
'''
new = '''        self._draw_strip()
        _drain_retired_native()
        self._shown = screen
'''
assert source.count(old) == 1
source = source.replace(old, new)

old = '''        try:
            self.root.mainloop()
        finally:
            self._teardown()
        return 3 if self._fatal_ui else (4 if self._accessible_requested else 0)
'''
new = '''        try:
            self.root.mainloop()
        except BaseException as original:
            _retire_tk_owner(self, original)
            raise
        else:
            _retire_tk_owner(self)
        return 3 if self._fatal_ui else (4 if self._accessible_requested else 0)
'''
assert source.count(old) == 1
source = source.replace(old, new)
old = '''def run_tk(wizard: Wizard, fullscreen: bool = False) -> int:
    ui = None
    try:
        ui = TkWizard(wizard, fullscreen=fullscreen)
        return ui.run()
    finally:
        ui = None
        _collect_retired_interpreters()
'''
new = '''def run_tk(wizard: Wizard, fullscreen: bool = False) -> int:
    ui = None
    original = None
    try:
        ui = TkWizard(wizard, fullscreen=fullscreen)
        return ui.run()
    except BaseException as error:
        original = error
        raise
    finally:
        try:
            if ui is not None:
                _retire_tk_owner(ui, original)
        finally:
            ui = None
            _collect_retired_interpreters()
'''
assert source.count(old) == 1
source = source.replace(old, new)

ast.parse(source, filename='private-candidate4-agent.py')
out = Path('/tmp/pass20-primary/private-candidate4-agent.py')
assert not out.exists()
out.write_text(source)
diff = ''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),source.splitlines(keepends=True),fromfile='candidate3/tk_wizard.py',tofile='candidate4/tk_wizard.py'))
Path('/tmp/pass20-primary/private-candidate4-agent.patch').write_text(diff)
receipt={'base':str(base),'base_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(out),'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'ast_parse':'PASS','runtime':'NOT RUN by author; no product imports/threads/tests','shared_source_unchanged_by_author':True,'active_private_graph_unchanged_by_author':True,'owned_native_factory_calls':source.count('_new_owned_native(')-1}
Path('/tmp/pass20-primary/private-candidate4-agent.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
