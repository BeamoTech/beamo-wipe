"""Replay unchanged regression bodies with fake imports, paths, FDs and power."""
import ast
import copy
import hashlib
import io
import json
from pathlib import Path
import stat
import sys
import threading
import types

HARNESS = Path(__file__).resolve().parent
OUT = Path(__import__('os').environ['BEAMO_SECURITY_OUTPUT'])
ROOT = Path(__import__('os').environ['BEAMO_SECURITY_ROOT'])
bindings = []


def load_prefix(name, stop):
    path = HARNESS / name
    tree = ast.parse(path.read_bytes())
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == stop for t in node.targets
        ):
            break
        nodes.append(node)
    namespace = {"__file__": str(path)}
    saved = sys.argv
    try:
        sys.argv = [str(path), "after"]
        exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    finally:
        sys.argv = saved
    return namespace


def test_bodies(relative, namespace):
    path = ROOT / relative
    raw = path.read_bytes()
    nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef)]
    for node in nodes:
        bindings.append({"path": relative, "file_sha256": hashlib.sha256(raw).hexdigest(),
                         "name": node.name, "line": node.lineno,
                         "ast_sha256": hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()})
        node.decorator_list = []
    future = ast.parse("from __future__ import annotations").body
    exec(compile(ast.fix_missing_locations(ast.Module(body=future + nodes, type_ignores=[])), str(path), "exec"), namespace)


rows = []


def run(name, func, *args):
    try:
        func(*args)
    except BaseException as exc:
        rows.append({"case": name, "match": False, "error_type": type(exc).__name__})
    else:
        rows.append({"case": name, "match": True})


parser = load_prefix("completion-probe.py", "rows")
env = parser["env"]
fake_os = parser["fake_os"]
files = {}


class FakePath:
    def __init__(self, name="/fixture/tmp"):
        self.name = name

    def __truediv__(self, name):
        return FakePath(self.name + "/" + name)

    def __str__(self):
        return self.name

    def write_bytes(self, raw):
        files[self.name] = raw
        return len(raw)

    def stat(self):
        return types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_uid=0,
            st_dev=1, st_ino=2, st_size=len(files[self.name]), st_mtime_ns=3, st_ctime_ns=4)


current = {}


def fake_open(path, *args):
    current["path"] = path
    return 17


class Stream(io.BytesIO):
    def fileno(self):
        return 17


fake_os.open = fake_open
fake_os.close = lambda fd: None
fake_os.fdopen = lambda fd, mode, **kw: Stream(files[current["path"]])
fake_os.fstat = lambda fd: FakePath(current["path"]).stat()
fake_os.chmod = lambda *args: None
fake_os.getuid = lambda: 0
fake_os.O_RDONLY = 0
fake_os.O_NOFOLLOW = 1
fake_os.O_NONBLOCK = 2
env.update(stat=stat, _try_log_diag=lambda *args: None)
env["NwipeRunner"] = type("NwipeRunner", (), {"_scan_completion_log": env["_scan_completion_log"], "__init__": lambda self: setattr(self, "_active_log_identity", None)})
test_bodies("tests/test_security_terminal_progress.py", env)
damaged = ["/dev/sda: 010.00%, round 1 of 1, pass 1 of\n",
           "/dev/sda: 101.00%, round 1 of 1, pass 1 of 1\n",
           "/dev/sda: 100.00%, round 0 of 1, pass 1 of 1\n",
           "/dev/sda: damaged round pass eta\n"]
for method in env["MethodId"]:
    for number, text in enumerate(damaged):
        run(f"terminal-damaged-{method.value}-{number}", env["test_damaged_target_update_clears_prior_completion"], method, text)
    for name in ("test_exact_decimal_above_one_hundred_is_not_completion",
                 "test_other_device_update_does_not_clear_target_completion",
                 "test_independent_erased_table_remains_completion_proof"):
        run(f"{name}-{method.value}", env[name], method)
    run(f"projection-{method.value}", env["test_large_log_projection_preserves_damaged_latest_record"], FakePath(), method)
for number, skip in enumerate(("/dev/sda is reported as IN USE\n", "Unable to open device '/dev/sda'.\n", "/dev/sda: No sane device geometry\n")):
    run(f"activity-{number}", env["test_damaged_progress_cannot_support_nothing_erased"], skip)
for fill, accepted in ((b"x", True), (b"\xff", False)):
    run(f"normalized-budget-{accepted}", env["test_scanner_budget_counts_normalized_utf8"], FakePath(), fill, accepted)
run("deferred-budget", env["test_scanner_budget_includes_deferred_progress"], FakePath())
assert len(rows) == 30

power = load_prefix("startup-power-probe.py", "rows")
g = power["g"]
native = types.SimpleNamespace(pinned_nwipe_already_running=power["probe"])
old_import = g["__builtins__"]["__import__"]


def fake_import(name, *args, **kwargs):
    if name == "beamo_wipe.nwipe_runner":
        return native
    if name == "beamo_wipe.models":
        return types.SimpleNamespace(DiscoveryResult=DiscoveryResult)
    return old_import(name, *args, **kwargs)


class DiscoveryResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class AppProxy:
    def __getattr__(self, name):
        return g[name]

    def __setattr__(self, name, value):
        g[name] = value


class Patch:
    def __init__(self):
        self.saved = []

    def setattr(self, obj, name, value):
        self.saved.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def restore(self):
        for obj, name, value in reversed(self.saved):
            setattr(obj, name, value)


def fail(message):
    raise AssertionError(message)


g["__builtins__"]["__import__"] = fake_import
tests = dict(app=AppProxy(), nwipe_runner=native, threading=threading,
             pytest=types.SimpleNamespace(fail=fail), DiscoveryResult=DiscoveryResult,
             Wizard=g["Wizard"], DryRunRunner=power["DryRunner"], NwipeRunner=power["RealRunner"])
test_bodies("tests/test_security_startup_power_guard.py", tests)
cases = []
for runner_type in (tests["DryRunRunner"], tests["NwipeRunner"]):
    for state in (False, True, None, "error"):
        cases.append((f"live-{runner_type.__name__}-{state}", "test_live_power_request_checks_external_engine", runner_type, state))
for flag in ("dry_run", "preview"):
    cases.append((f"inert-{flag}", "test_inert_modes_do_not_probe_live_processes", flag))
cases.append(("startup-fallback", "test_startup_fallback_remains_live_for_power_safety"))
for name, function, *args in cases:
    patch = Patch()
    try:
        run(name, tests[function], patch, *args)
    finally:
        patch.restore()
assert len(rows) == 41

record = {"scope": "Exact bodies of the 41 security regression cases, with fake OS/FD/path/process/power imports. The journal fixture is adapted to the integrated controller. No product-module imports or native pytest acceptance.",
          "cases": len(rows), "matching": sum(r["match"] for r in rows), "rows": rows, "bindings": bindings}
with (OUT / "final-regression-replay.json").open("x", encoding="utf-8") as output:
    json.dump(record, output, indent=2)
    output.write("\n")
print(json.dumps({k: v for k, v in record.items() if k not in ("rows", "bindings")}, indent=2))
print(json.dumps([r for r in rows if not r["match"]], indent=2))
raise SystemExit(0 if all(r["match"] for r in rows) else 1)
