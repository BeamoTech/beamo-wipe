"""Fresh fake-only refresh/reset/late-callback model with real reauthorization."""
from dataclasses import replace
from itertools import product
from pathlib import Path
import hashlib
import json
import os

from pytest import MonkeyPatch
from beamo_wipe import app, discover, sound
from beamo_wipe.demo import make_demo_wizard
from beamo_wipe.models import DiscoveryResult, MethodId, Screen
from beamo_wipe.nwipe_runner import DryRunRunner, NwipeRunner
from beamo_wipe.wizard import Wizard

counts = {"scenarios": 0, "refresh_claims": 0, "invalid_outcome_refusals": 0,
          "stale_completions_ignored": 0, "duplicate_completions_ignored": 0,
          "empty_inventory_controls": 0, "clean_retries": 0,
          "blocked_erase_calls": 0, "explicit_fake_starts": 0,
          "native_callbacks": 0, "mismatches": 0}


class Clock:
    value = 100.0
    def __call__(self): return self.value


def forbidden(*args, **kwargs):
    counts["native_callbacks"] += 1
    raise AssertionError("Native action forbidden")


def blocked(w):
    w.confirm_erase()
    assert not w.runner.started
    counts["blocked_erase_calls"] += 1


def move_to(w, method, stage):
    w.skip_intro()
    if stage == "owner": return
    w.set_owner(True); w.continue_owner()
    if stage == "pick": return
    w.select_disk(w.selectable[0].path); w.continue_pick()
    if stage == "confirm": return
    w.set_confirm_input(w.confirm.token); w.continue_confirm()
    w.set_method(method)
    if stage == "method": return
    w.continue_method()
    w._clock.value += 5
    assert w.erase_enabled and not w.runner.started


def outcome(initial, name):
    if name == "unchanged": return replace(initial)
    if name == "serial-change":
        old = initial.selectable[0]
        new = replace(old, serial="FAKE-CHANGED-12345")
        return replace(initial, disks=tuple(new if d == old else d for d in initial.disks),
                       selectable=tuple(new if d == old else d for d in initial.selectable))
    if name == "peer-added":
        peer = replace(initial.selectable[0], name="sdz", path="/dev/sdz",
                       serial="FAKE-PEER-98765", wwn="FAKE-PEER-WWN", layout_id="FAKE-PEER-LAYOUT")
        return replace(initial, disks=(*initial.disks, peer), selectable=(*initial.selectable, peer))
    if name == "empty":
        return replace(initial, disks=(initial.boot,), selectable=(), excluded=())
    if name == "unidentified": return replace(initial, boot=None, boot_identified=False)
    if name == "error": return OSError("Controlled fake refresh failure")
    if name == "interrupt": return KeyboardInterrupt("Controlled fake refresh interruption")
    if name == "wrong-type": return {}
    if name == "boot-in-targets": return replace(initial, selectable=(*initial.selectable, initial.boot))
    raise AssertionError(name)


with MonkeyPatch.context() as patch:
    patch.setenv("BEAMO_WIPE_DRY_RUN", "1")
    patch.delenv("BEAMO_WIPE_LIVE", raising=False)
    for boundary in ("subprocess.run", "subprocess.Popen", "os.kill",
                     "beamo_wipe.discover.run_lsblk", "beamo_wipe.discover.read_cmdline",
                     "beamo_wipe.discover.read_mount_sources"):
        patch.setattr(boundary, forbidden)
    patch.setattr(NwipeRunner, "start", forbidden)
    patch.setattr(app, "_shutdown", forbidden)
    patch.setattr(sound, "_run", forbidden)
    patch.setattr(sound, "_popen", forbidden)
    patch.setattr("beamo_wipe.diagnostics.log_diag", lambda *a, **kw: None)
    patch.setattr("beamo_wipe.diagnostics.emit_serial_marker", lambda *a, **kw: None)
    original_realpath = os.path.realpath
    patch.setattr(os.path, "realpath", lambda p, *a, **kw: str(p) if str(p).startswith("/dev/") else original_realpath(p, *a, **kw))
    initial = make_demo_wizard().discovery
    for stage, method, name, delivery in product(
        ("owner", "pick", "confirm", "method", "last-chance"), MethodId,
        ("unchanged", "serial-change", "peer-added", "empty", "unidentified", "error", "interrupt", "wrong-type", "boot-in-targets"),
        ("stale-first", "duplicate", "new-generation"),
    ):
        counts["scenarios"] += 1
        clock = Clock()
        w = Wizard(initial, DryRunRunner(clock=clock), clock=clock,
                   wall_clock=lambda: "2026-10-21T00:00:00Z")
        w._write_evidence = lambda **kw: None
        move_to(w, method, stage)
        old_token = w.confirm.token if w.confirm else "OLD-FAKE-TOKEN"
        seq = w.begin_refresh()
        counts["refresh_claims"] += 1
        assert seq is not None and w.screen == Screen.REFRESHING
        assert w.begin_refresh() is None
        for action in (lambda: w.set_owner(True), w.continue_owner,
                       lambda: w.select_disk(initial.selectable[0].path), w.continue_pick,
                       lambda: w.set_confirm_input(old_token), w.continue_confirm,
                       lambda: w.set_method(method), w.continue_method, w.back):
            action(); blocked(w)
        assert w.selected is None and not w.owner_ok and w.confirm_input == ""
        assert w._authorized_operation is None and w._erase_until is None
        fresh = outcome(initial, name)
        if delivery == "stale-first":
            assert not w.finish_refresh(seq + 1000, initial)
            counts["stale_completions_ignored"] += 1
            assert w.screen == Screen.REFRESHING
        assert w.finish_refresh(seq, fresh)
        invalid = name in {"unidentified", "error", "interrupt", "wrong-type", "boot-in-targets"}
        assert w.screen == (Screen.PICK_BLOCKED if invalid else Screen.OWNER)
        assert not w.owner_ok and w.selected is None and w.confirm_input == ""
        blocked(w)
        committed = w.discovery
        if delivery == "duplicate":
            assert not w.finish_refresh(seq, object()) and w.discovery is committed
            counts["duplicate_completions_ignored"] += 1
        if invalid: counts["invalid_outcome_refusals"] += 1
        if name == "empty":
            w.set_owner(True); w.continue_owner()
            assert w.screen == Screen.PICK_EMPTY
            blocked(w); counts["empty_inventory_controls"] += 1
        if invalid or name == "empty" or delivery == "new-generation":
            next_seq = w.begin_refresh()
            counts["refresh_claims"] += 1
            assert next_seq is not None and next_seq != seq
            assert not w.finish_refresh(seq, initial)
            counts["stale_completions_ignored"] += 1
            assert w.screen == Screen.REFRESHING and w.selected is None
            assert w.finish_refresh(next_seq, initial)
            counts["clean_retries"] += 1
        w.continue_owner(); blocked(w)
        assert w.screen == Screen.OWNER
        w.set_owner(True); w.continue_owner()
        w.select_disk(w.selectable[0].path); w.continue_pick()
        w.continue_confirm(); blocked(w)
        assert w.screen == Screen.CONFIRM
        w.set_confirm_input(w.confirm.token); w.continue_confirm()
        w.set_method(method); w.continue_method()
        assert w.screen == Screen.LAST_CHANCE and not w.erase_enabled
        blocked(w); clock.value += 4.999
        assert not w.erase_enabled
        blocked(w); clock.value += .001
        assert w.erase_enabled and not w.runner.started
        w.confirm_erase()
        assert w.runner.started and w.screen == Screen.WORKING
        assert w._wipe_request.method == method
        counts["explicit_fake_starts"] += 1
        assert not w.finish_refresh(seq, initial)
        counts["stale_completions_ignored"] += 1
        assert w.screen == Screen.WORKING and w.begin_refresh() is None

assert counts["scenarios"] == counts["explicit_fake_starts"] == 405
assert not counts["native_callbacks"] and not counts["mismatches"]
counts["source_sha256"] = {name: hashlib.sha256((Path('/workspace/beamo-wipe') / name).read_bytes()).hexdigest()
    for name in ("src/beamo_wipe/wizard.py", "src/beamo_wipe/models.py", "src/beamo_wipe/identity.py")}
Path(__file__).with_suffix('.json').write_text(json.dumps(counts, indent=2) + '\n')
print(json.dumps(counts))
