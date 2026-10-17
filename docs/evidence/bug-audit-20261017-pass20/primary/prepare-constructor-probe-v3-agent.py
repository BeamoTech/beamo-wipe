import ast
import hashlib
import json
from pathlib import Path
base=Path('docs/evidence/bug-audit-20261017-pass20/tk-lifetime')
v2=base/'constructor-boundary-probe-v2.py'
raw=v2.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='f37d25cc7cdab71c61ed9bc603109f975d301520ce35954b4c99fa7bcc2506f7'
frozen=base/'constructor-boundary-probe-v2-frozen.py'
if not frozen.exists(): frozen.write_bytes(raw)
assert frozen.read_bytes()==raw
s=raw.decode()
s=s.replace('eleven construction/cleanup fault routes and two live controls.','constructor, startup, and retained-owner native lifetime routes.')
s=s.replace('"local-variable-after-init", "image-after-init", "root-control", "row-control",','"local-variable-after-init", "image-after-init", "root-control", "row-control",\n    "startup-init-before", "startup-load-before", "startup-load-after",\n    "startup-frame", "startup-label", "startup-control",')
insert=s.index('\n\n@pytest.mark.parametrize("case", CASES)')
startup='''

def _startup_child(case):
    from beamo_wipe import startup_stages

    provenance = _admit()
    _emit("admission", case=case, provenance=provenance)
    assert threading.current_thread() is threading.main_thread()
    owner_thread = threading.get_ident()
    was_enabled = gc.isenabled()
    gc.disable()
    roots = []
    widgets = []
    injected_ids = []
    retained_errors = []
    build_calls = []
    finished = threading.Event()
    sentinel = object()
    original_root_init = ui.tk.Tk.__init__
    original_loadtk = ui.tk.Tk._loadtk
    original_frame_init = ui.tk.Frame.__init__
    original_label_init = ui.tk.Label.__init__

    def inject(where):
        error = ControlledNativeConstructorFailure(where)
        injected_ids.append(id(error))
        _emit("startup-fault-injected", where=where, exception_id=id(error))
        raise error

    def root_init(root, *args, **kwargs):
        if case == "startup-init-before":
            inject("startup Tk initialization before native allocation")
        return original_root_init(root, *args, **kwargs)

    def loadtk(root):
        roots.append(dict(reference=weakref.ref(root), interpreter_id=id(root.tk)))
        if case == "startup-load-before":
            inject("startup after native allocation, before original _loadtk")
        original_loadtk(root)
        if case == "startup-load-after":
            inject("startup after original _loadtk, before Tk initializer returned")

    def frame_init(frame, *args, **kwargs):
        original_frame_init(frame, *args, **kwargs)
        widgets.append(dict(kind="Frame", reference=weakref.ref(frame)))
        if case == "startup-frame" and not injected_ids:
            inject("startup first actual native Frame, before presenter's outer try")

    def label_init(label, *args, **kwargs):
        original_label_init(label, *args, **kwargs)
        widgets.append(dict(kind="Label", reference=weakref.ref(label)))
        if case == "startup-label" and not injected_ids:
            inject("startup first actual native Label, before presenter's outer try")

    def root_state():
        state = []
        for entry in roots:
            root = entry["reference"]()
            window_alive = False
            if root is not None:
                try:
                    window_alive = bool(root.winfo_exists())
                except ui.tk.TclError:
                    pass
            state.append(dict(interpreter_id=entry["interpreter_id"],
                              wrapper_alive=root is not None, window_alive=window_alive))
            root = None
        return state

    def build(report):
        # A plain sentinel and real stage queue exercise actual startup poll,
        # GUI, and worker sequencing without an app, disks, engine, or mounts.
        build_calls.append(threading.get_ident())
        try:
            report(startup_stages.STAGE_BOOT_USB)
            report(startup_stages.STAGE_FINDING)
            return sentinel
        finally:
            finished.set()

    with pytest.MonkeyPatch.context() as patch:
        effects = _guard(patch)
        patch.setattr(ui, "_ensure_tk_display", lambda: None)
        patch.setattr(startup_stages, "_emit", lambda *_args: None)
        patch.setattr(ui.tk.Tk, "__init__", root_init)
        patch.setattr(ui.tk.Tk, "_loadtk", loadtk)
        patch.setattr(ui.tk.Frame, "__init__", frame_init)
        patch.setattr(ui.tk.Label, "__init__", label_init)
        try:
            result = None
            try:
                result = ui.run_tk_startup(build, fullscreen=False)
            except BaseException as error:
                retained_errors.append(error)
            fault = case != "startup-control"
            assert len(injected_ids) == int(fault)
            assert len(retained_errors) == int(fault)
            assert [id(error) for error in retained_errors] == injected_ids
            assert all(isinstance(error, ControlledNativeConstructorFailure) for error in retained_errors)
            if fault:
                assert not build_calls and not finished.is_set(), "Build started before failed startup setup completed"
            else:
                assert result == ("wizard", sentinel)
                assert finished.is_set() and len(build_calls) == 1
                assert build_calls[0] != owner_thread, "Live startup control did not use its actual worker"
            if case == "startup-init-before":
                assert not roots and not widgets, "No-native startup control allocated a native object"
            else:
                assert roots
            state = root_state()
            _emit("startup-constructor-boundary", case=case, provenance=provenance,
                  root_state=state, build_threads=build_calls,
                  retained_original_exception_ids=[id(error) for error in retained_errors],
                  retained_original_tracebacks=[
                      [dict(file=f.filename, line=f.lineno, function=f.name)
                       for f in traceback.extract_tb(error.__traceback__)]
                      for error in retained_errors
                  ], widget_kinds=[entry["kind"] for entry in widgets], effects=effects)
            assert not effects
            assert not any(row["window_alive"] for row in state), "Startup construction failure left owned native window open"
            collected = []

            def release_and_collect():
                retained_errors.clear()
                collected.append(gc.collect())

            collector = threading.Thread(target=release_and_collect, daemon=True,
                                         name="owned-startup-release")
            collector.start()
            collector.join(2)
            if collector.is_alive():
                frame = sys._current_frames().get(collector.ident)
                _emit("worker-timeout", stack=[
                    dict(file=f.filename, line=f.lineno, function=f.name)
                    for f in traceback.extract_stack(frame)
                ] if frame is not None else [])
                del frame
                os._exit(91)  # Only this exact owned diagnostic child.
            assert collected
            sweep = getattr(ui, "_collect_retired_interpreters", None)
            if sweep is not None:
                sweep()
            gc.collect()
            _emit("child-complete", case=case, provenance=provenance,
                  root_state=root_state(), build_threads=build_calls, effects=effects)
        finally:
            # Cleanup is outside all boundary assertions. It cannot satisfy
            # an original-source open-window failure. No native frame is edited.
            retained_errors.clear()
            for entry in roots:
                root = entry["reference"]()
                if root is not None:
                    try:
                        root.destroy()
                    except ui.tk.TclError:
                        pass
                root = None
            gc.collect()
            if was_enabled:
                gc.enable()
'''
s=s[:insert]+startup+s[insert:]
s=s.replace('    _child(sys.argv[2])','    if sys.argv[2].startswith("startup-"):\n        _startup_child(sys.argv[2])\n    else:\n        _child(sys.argv[2])')
out=base/'constructor-boundary-probe-v3.py'
assert not out.exists()
ast.parse(s, filename=str(out));out.write_text(s)
receipt={'status':'PREPARED / NOT RUN by author; AST parse only','v2_frozen':str(frozen),'v2_sha256':hashlib.sha256(raw).hexdigest(),'v3':str(out),'v3_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'cases':19,'added_cases':['startup-init-before','startup-load-before','startup-load-after','startup-frame','startup-label','startup-control'],'startup_contract':'Actual run_tk_startup with only _ensure_tk_display bypassed plus native fault observations. Original exact exception retained. Before worker release, owned root window must already be closed. Later worker clears only exception owner and runs collection; raw interpreter must remain safe until creator-thread sweep. Native Tcl abort captured as diagnostic-child failure, not hidden.','startup_control':'Actual StartupRun/build worker + actual Tk mainloop/poll; build reports fake stage keys and returns plain sentinel, never an app or disks. Actual worker completion/thread identity asserted.','provenance':'Mandatory BEAMO_TK_PROBE_SOURCE + BEAMO_TK_PROBE_SHA256 in both parent and child','startup_guards':'App/native/audio/disk/network subprocess effects forbidden; startup serial stage emission replaced by fixture lambda; no inherited PYTEST_PLUGINS','limitations':'Weak root identity/open-window check and bounded owned-child survival prove lifecycle behavior; exact C destructor thread is not directly observed. Allocation-changing observation cannot replace full plain gate.'}
(base/'constructor-boundary-v3-preparation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps(receipt,indent=2))
