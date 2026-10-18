import ast
import difflib
import hashlib
import json
from pathlib import Path
base=Path('/tmp/pass20-primary/private-candidate4-agent.py')
raw=base.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='68b25648c658e5dc9de1e9f7edf3663c90f4dc52520852a8ea8458aa40f8327f'
s=raw.decode()
s=s.replace('_RETIRED_INTERPRETERS: list[tuple[threading.Thread, object]] = []','_RETIRED_INTERPRETERS: dict[int, tuple[threading.Thread, object]] = {}')
s=s.replace('_RETIRED_NATIVE_ASSETS: list[tuple[threading.Thread, object]] = []','_RETIRED_NATIVE_ASSETS: dict[int, tuple[threading.Thread, object]] = {}')
start=s.index('def _pin_retired_interpreter(')
end=s.index('\n\ndef _drain_retired_native()',start)
s=s[:start]+'''def _pin_retired_interpreter(root: tk.Misc, owner: threading.Thread | None = None) -> None:
    if not isinstance(root, tk.Misc):
        return  # Callable lightweight roots do not own a native Tk interpreter.
    # Tk.__getattr__ delegates through self.tk, which does not exist yet when
    # the real initializer fails before its first statement.
    interpreter = root.__dict__.get("tk")
    if interpreter is not None:
        _RETIRED_INTERPRETERS.setdefault(id(interpreter), (owner or threading.current_thread(), interpreter))


def _pin_retired_assets(assets, owner: threading.Thread) -> None:
    for asset in assets:
        if isinstance(asset, _TK_ASSET_CLASSES):
            _RETIRED_NATIVE_ASSETS.setdefault(id(asset), (owner, asset))


def _drain_retired_assets() -> None:
    owner = threading.current_thread()
    for identity, record in list(_RETIRED_NATIVE_ASSETS.items()):
        # Dict/snapshot/loop references own the same record tuple. The tuple
        # owns one asset reference; getrefcount adds only its argument.
        if record[0] is owner and sys.getrefcount(record[1]) == 2:
            if _RETIRED_NATIVE_ASSETS.get(identity) is record:
                del _RETIRED_NATIVE_ASSETS[identity]


def _drain_retired_interpreters() -> None:
    owner = threading.current_thread()
    for identity, record in list(_RETIRED_INTERPRETERS.items()):
        if record[0] is owner and sys.getrefcount(record[1]) == 2:
            if _RETIRED_INTERPRETERS.get(identity) is record:
                del _RETIRED_INTERPRETERS[identity]
''' + s[end:]

# Partial real root cleanup uses only its actual initialized instance dictionary.
s=s.replace('        if getattr(root, "tk", None) is not None:\n            try:\n                root.destroy()', '        if root.__dict__.get("tk") is not None:\n            try:\n                root.destroy()')

# A single complete boundary covers direct callers as well as run_tk's wrapper.
old='''        if self.root.winfo_ismapped():
            self.root.after_idle(claim_input)
        else:
            mapping = self.root.bind("<Map>", mapped, add="+")
        try:
            self.root.mainloop()
'''
new='''        try:
            if self.root.winfo_ismapped():
                self.root.after_idle(claim_input)
            else:
                mapping = self.root.bind("<Map>", mapped, add="+")
            self.root.mainloop()
'''
assert s.count(old)==1
s=s.replace(old,new)

# Preserve the existing actual startup implementation as a private window
# helper; the public owning wrapper covers every setup and mainloop exit.
start=s.index('def run_tk_startup(build, *, fullscreen: bool = False,')
old_startup=s[start:]
marker='    root.title("Beamo Wipe")\n'
body_start=old_startup.index(marker)
body=old_startup[body_start:]
# Root destruction is performed by the public owner after helper cleanup. Close
# and poll callbacks retain their existing immediate window-destroy behavior.
old='''    try:
        render()
        run.start()
'''
new='''    original = None
    try:
        render()
        run.start()
'''
assert body.count(old)==1
body=body.replace(old,new)
old='''        root.mainloop()
    finally:
'''
new='''        root.mainloop()
    except BaseException as error:
        original = error
        raise
    finally:
'''
assert body.count(old)==1
body=body.replace(old,new)
old='''        for callback in (poll_after, focus_after):
            if callback is not None:
                try:
                    root.after_cancel(callback)
                except tk.TclError:
                    pass
        try:
            root.destroy()
        except tk.TclError:
            pass
'''
new='''        cleanup_error = None
        for callback in (poll_after, focus_after):
            if callback is not None:
                try:
                    root.after_cancel(callback)
                except tk.TclError:
                    pass
                except BaseException as cleanup:
                    if original is not None:
                        _note_tk_cleanup_failure(original, cleanup)
                    elif cleanup_error is None:
                        cleanup_error = cleanup
        if cleanup_error is not None:
            raise cleanup_error
'''
assert body.count(old)==1
body=body.replace(old,new)
public='''def _close_owned_startup_root(root, owner: threading.Thread,
                              original: BaseException | None = None) -> None:
    _pin_retired_interpreter(root, owner)
    try:
        root.destroy()
    except tk.TclError:
        pass
    except BaseException as cleanup:
        if original is None:
            raise
        _note_tk_cleanup_failure(original, cleanup)


def run_tk_startup(build, *, fullscreen: bool = False,
                   stall_after_s: float | None = None) -> tuple:
    """Show staged startup on Tk while one worker builds the wizard.

    Returns ("wizard", wizard), ("failed", exc), or ("abandoned", None).
    Native display construction errors retain StartupDisplayUnavailable and
    their original TclError cause. Every owned window closes on setup failure,
    normal return, or propagated interruption.
    """
    from beamo_wipe.startup_stages import STALL_AFTER_S, StartupRun

    _collect_retired_interpreters()
    _ensure_tk_display()
    run = StartupRun(
        build,
        stall_after_s=STALL_AFTER_S if stall_after_s is None else stall_after_s,
    )
    owner = threading.current_thread()
    try:
        root = _new_owned_root(owner)
    except tk.TclError as exc:
        raise StartupDisplayUnavailable(f"no graphical display for startup stages: {exc}") from exc
    _pin_retired_interpreter(root, owner)
    original = None
    try:
        return _run_tk_startup_window(root, run, fullscreen=fullscreen)
    except BaseException as error:
        original = error
        raise
    finally:
        try:
            _close_owned_startup_root(root, owner, original)
        finally:
            root = None
            _collect_retired_interpreters()


def _run_tk_startup_window(root, run, *, fullscreen: bool) -> tuple:
'''
s=s[:start]+public+body
ast.parse(s,filename='private-candidate5-agent.py')
out=Path('/tmp/pass20-primary/private-candidate5-agent.py')
assert not out.exists()
out.write_text(s)
Path('/tmp/pass20-primary/private-candidate5-agent.patch').write_text(''.join(difflib.unified_diff(raw.decode().splitlines(keepends=True),s.splitlines(keepends=True),fromfile='candidate4/tk_wizard.py',tofile='candidate5/tk_wizard.py')))
r={'base':str(base),'base_sha256':hashlib.sha256(raw).hexdigest(),'candidate':str(out),'candidate_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'ast_parse':'PASS','runtime':'NOT RUN by author; no product imports/Tk/threads/tests','shared_and_active_private_edits':'NONE','changes':['partial real wrapper tk lookup via __dict__','identity-keyed asset and raw interpreter dicts; no native object equality in drain','complete direct-run setup boundary','owned startup root wrapper covering all configuration/widget construction/mainloop errors','existing TclError startup translation/cause preserved','callable root factories and actual StartupRun semantics preserved'],'limitations':['Root must independently review and run frozen proofs/gates.','Full sweep at explicit ownership boundaries only; draw drains remain lightweight.','Creator-thread pool deferral while external owners remain is deliberate.']}
Path('/tmp/pass20-primary/private-candidate5-agent.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r,indent=2))
