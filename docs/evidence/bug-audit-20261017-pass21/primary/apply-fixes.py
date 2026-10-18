from pathlib import Path
p=Path('src/beamo_wipe/discover.py');s=p.read_text();old='''    if isinstance(value, float):
        return int(value)
''';new='''    if isinstance(value, float):
        try:
            return int(value)
        except OverflowError as exc:
            raise ValueError("lsblk size is not finite") from exc
''';assert s.count(old)==1;s=s.replace(old,new);old='''        raise ValueError("lsblk node has no usable device path")
    label = _volume_label(node)''';new='''        raise ValueError("lsblk node has no usable device path")
    if _node_type(node) == "disk" and (not name or "/" in name):
        # Flat PKNAME ancestry uses the kernel name, not a path alias. Do not
        # mint a target whose partition evidence cannot bind to that name.
        raise ValueError("lsblk disk has no canonical kernel name")
    label = _volume_label(node)''';assert s.count(old)==1;p.write_text(s.replace(old,new))
p=Path('src/beamo_wipe/diagnostics.py');s=p.read_text();old='" " if unicodedata.category(ch).startswith("C") else ch';new='" " if unicodedata.category(ch).startswith("C") or unicodedata.category(ch) in {"Zl", "Zp"} else ch';assert s.count(old)==1;p.write_text(s.replace(old,new))
p=Path('src/beamo_wipe/ui/tk_wizard.py');s=p.read_text();pairs={
'_new_owned_native(self.root, tk.StringVar)':'_new_owned_native(self.root, tk.StringVar, master=self.root)',
'_new_owned_native(self.root, tk.IntVar, value=0)':'_new_owned_native(self.root, tk.IntVar, master=self.root, value=0)',
'_new_owned_native(self.root, tk.BooleanVar, value=False)':'_new_owned_native(self.root, tk.BooleanVar, master=self.root, value=False)',
'variable.trace_add("write", self._on_variable)':'_new_owned_trace(self, "_variable_trace", variable, self._on_variable)',
'self._confirm_var.trace_add("write", self._confirm_var_written)':'_new_owned_trace(self, "_confirm_var_trace", self._confirm_var, self._confirm_var_written)',
'self._typing_var.trace_add("write", self._typing_var_written)':'_new_owned_trace(self, "_typing_var_trace", self._typing_var, self._typing_var_written)'}
for old,new in pairs.items():assert old in s;s=s.replace(old,new)
needle='\ndef _pin_retired_interpreter('
helper='''
def _new_owned_trace(owner, field: str, variable, callback) -> str:
    if not isinstance(variable, _TK_ASSET_CLASSES[1]):
        return variable.trace_add("write", callback)
    # trace_add can register its Tcl command before an interruption prevents
    # its return. Adopt our exact command before that boundary; peer commands
    # registered during the call keep their independent ownership.
    missing = object()
    previous = vars(variable).get("_register", missing)
    original_register = getattr(variable, "_register")
    adopted = False

    def register(func):
        nonlocal adopted
        token = original_register(func)
        if func is callback and not adopted:
            setattr(owner, field, token)
            adopted = True
        return token

    setattr(variable, "_register", register)
    try:
        return variable.trace_add("write", callback)
    finally:
        if vars(variable).get("_register") is register:
            if previous is missing:
                delattr(variable, "_register")
            else:
                setattr(variable, "_register", previous)

'''
assert s.count(needle)==1;s=s.replace(needle,'\n'+helper+needle,1)
start=s.index('        launch_decided = threading.Event()',s.index('    def _start_refresh_scan'))
end=s.index('\n    def _refresh_worker(',start)
s=s[:start]+'''        launch_decided = None
        launch_allowed = [False]

        def run_if_launched() -> None:
            if launch_decided is None:
                return
            launch_decided.wait()
            with self._refresh_lock:
                accepted = launch_allowed[0]
            if accepted:
                self._refresh_worker(seq)

        try:
            launch_decided = threading.Event()
            worker = threading.Thread(
                target=run_if_launched,
                daemon=True, name=f"beamo-refresh-{seq}",
            )
            with self._refresh_lock:
                self._refresh_threads[seq] = worker
            worker.start()
            self.root.after(50, lambda: self._poll_refresh(seq, on_done))
            with self._refresh_lock:
                # A set() interrupted after waking the worker has not accepted
                # it yet. The same lock keeps that worker behind this decision.
                launch_decided.set()
                launch_allowed[0] = True
        except BaseException as exc:
            with self._refresh_lock:
                self._refresh_threads.pop(seq, None)
            if launch_decided is not None:
                try:
                    launch_decided.set()
                except BaseException as cleanup:
                    _note_tk_cleanup_failure(exc, cleanup)
            return finish_failed_start(exc)
        return seq
''' +s[end:];p.write_text(s)
p=Path('src/beamo_wipe/ui/accessible_wizard.py');s=p.read_text();start=s.index('        launch_decided = threading.Event()',s.index('    def _begin_refresh_scan'));end=s.index('\n    def _refresh_worker(',start)
s=s[:start]+'''        launch_decided = None
        launch_allowed = [False]

        def run_if_launched() -> None:
            if launch_decided is None:
                return
            launch_decided.wait()
            with self._refresh_lock:
                accepted = launch_allowed[0]
            if accepted:
                self._refresh_worker(seq)

        try:
            launch_decided = threading.Event()
            threading.Thread(
                target=run_if_launched,
                name=f"beamo-accessible-refresh-{seq}",
                daemon=True,
            ).start()
            with self._refresh_lock:
                launch_decided.set()
                launch_allowed[0] = True
        except BaseException as exc:
            if launch_decided is not None:
                try:
                    launch_decided.set()
                except BaseException as cleanup:
                    exc.add_note(f"Refresh wake also failed: {type(cleanup).__name__}")
            self.w.finish_refresh(seq, exc)
            return True
        return True
''' +s[end:]
start=s.index('    def close(self):');end=s.index('\n    def _runtime_failure',start)
s=s[:start]+'''    def close(self):
        if self.closed:
            return
        self.closed = True
        errors = []

        def cleanup(action):
            try:
                action()
            except BaseException as error:
                errors.append(error)

        cleanup(getattr(self.w, "cancel_audio", lambda: None))
        dialog = getattr(self, "_sound_dialog", None)
        if dialog is not None:
            cleanup(dialog.close)
        if self.timer:
            timer, self.timer = self.timer, 0
            cleanup(lambda: GLib.source_remove(timer))
        cleanup(self.window.destroy)
        cleanup(lambda: Gtk.main_quit() if Gtk.main_level() else None)
        if errors:
            for error in errors[1:]:
                errors[0].add_note(f"GTK cleanup also failed: {type(error).__name__}")
            raise errors[0]
''' +s[end:];p.write_text(s)
print('Applied only proved discovery/diagnostic/Tk/GTK fixes.')
