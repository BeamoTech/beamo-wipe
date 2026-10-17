"""Harmless pass15 source-review probe; run only after root admission.

No subprocesses, native inventory, sysfs, device opens or power actions.
All device paths and hardware strings belong to injected fake inventory.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import importlib
import io
import itertools
import json
import os
from pathlib import Path
from unittest.mock import patch

discovery = importlib.import_module("beamo_wipe.discover")
safety = importlib.import_module("beamo_wipe.safety")
ROOT = Path("/root/dev/Beamo Wipe")
OUT = Path("/tmp/pass15-discovery")
X, Y = "50014ee20aa00001", "50014ee20aa00002"
CHAINS = {
    "root_missing": (("FAKE-A", ""), ("FAKE-A", X), ("FAKE-C", X)),
    "leaf_missing": (("FAKE-A", X), ("FAKE-B", X), ("FAKE-B", "")),
    "contrary": (("FAKE-A", X), ("FAKE-A", ""), ("FAKE-A", Y)),
    "unrelated": (("FAKE-A", ""), ("FAKE-B", X), ("FAKE-C", X)),
}
effects = []


def forbidden(*_args, **_kwargs):
    effects.append("native-acquisition")
    raise AssertionError("Injected fake discovery reached native acquisition")


realpath = os.path.realpath
original_open = open
original_io_open = io.open
original_os_open = os.open
original_lstat = os.lstat


def fake_realpath(path, *args, **kwargs):
    text = os.fspath(path)
    if text.startswith(("/dev/", "/sys/")):
        return text
    return realpath(path, *args, **kwargs)


def guarded_io(original):
    def checked(path, *args, **kwargs):
        if not isinstance(path, int):
            text = os.fsdecode(path)
            if text in {"/dev", "/proc", "/sys"} or text.startswith(("/dev/", "/proc/", "/sys/")):
                effects.append("native-path:" + text)
                raise AssertionError("Injected fake discovery reached a native path")
        return original(path, *args, **kwargs)
    return checked


def run():
    results = []
    with patch.dict(os.environ, {"BEAMO_WIPE_DRY_RUN": "1"}), \
            patch.object(os.path, "realpath", fake_realpath), \
            patch.object(discovery, "run_lsblk", forbidden), \
            patch.object(discovery, "read_mount_sources", forbidden), \
            patch.object(discovery, "read_cmdline", forbidden), \
            patch.object(discovery.subprocess, "run", forbidden), \
            patch.object(discovery.subprocess, "Popen", forbidden), \
            patch("builtins.open", guarded_io(original_open)), \
            patch.object(io, "open", guarded_io(original_io_open)), \
            patch.object(os, "open", guarded_io(original_os_open)), \
            patch.object(os, "lstat", guarded_io(original_lstat)), \
            patch("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None), \
            patch("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a, **_k: None):
        for kind, bridge, chain, order in itertools.product(
            ("boot", "mounted"),
            ("visible", "rom", "hidden_name", "overlong_model", "overlong_layout_label"),
            CHAINS,
            itertools.permutations(range(3)),
        ):
            rows = []
            for index, (name, (serial, wwn)) in enumerate(zip(("sdb", "sdc", "sdd"), CHAINS[chain])):
                rows.append(dict(
                    name=name, path="/dev/" + name, type="disk", tran="sata",
                    size=128_000_000_000, serial=serial, wwn=wwn, model="Fake disk",
                    ro=False, mountpoints=[],
                ))
            rows[0]["mountpoints"] = ["/run/live/medium" if kind == "boot" else "/media/fake-data"]
            if kind == "boot":
                rows[0]["tran"] = "usb"
            if bridge == "rom":
                rows[1].update(name="sr0", path="/dev/sr0", type="rom", tran="usb", ro=True)
            elif bridge == "hidden_name":
                rows[1].update(name="sdlive", path="/dev/sdlive")
            elif bridge == "overlong_model":
                rows[1]["model"] = "M" * 129
            elif bridge == "overlong_layout_label":
                rows[1]["label"] = "L" * 129
            ordered = [copy.deepcopy(rows[i]) for i in order]
            boot = rows[0]
            if kind == "mounted":
                boot = dict(name="sdz", path="/dev/sdz", type="disk", tran="usb",
                            size=16_000_000_000, serial="FAKE-BOOT", wwn="50014ee20aa00009",
                            ro=False, mountpoints=["/run/live/medium"])
                ordered.append(boot)
            result = discovery.discover(lsblk_payload={"blockdevices": ordered},
                                        mount_sources=[boot["path"]], cmdline="", env={})
            leaf = next((d for d in result.disks if d.path == "/dev/sdd"), None)
            selectable = {d.path for d in result.selectable}
            should_protect = chain in {"root_missing", "leaf_missing"}
            expected = "/dev/sdd" not in selectable if should_protect else "/dev/sdd" in selectable
            guard_refused = None
            if kind == "boot":
                try:
                    safety.assert_boot_excluded(result)
                    guard_refused = False
                except safety.SafetyError:
                    guard_refused = True
            identity_accepted = False
            token = ""
            if leaf is not None and leaf.path in selectable:
                try:
                    safety.assert_disk_identity(leaf, result)
                    token = safety.confirm_spec(leaf, safety.listed_disks(result)).token
                    identity_accepted = bool(token)
                except safety.SafetyError:
                    pass
            results.append(dict(kind=kind, bridge=bridge, chain=chain, order=order,
                                payload={"blockdevices": ordered},
                                boot_identified=result.boot_identified, error=result.error,
                                diagnostic=result.diagnostic,
                                selectable=sorted(selectable), should_protect=should_protect,
                                passed=bool(expected), boot_guard_refused=guard_refused,
                                leaf_identity_accepted=identity_accepted, token=token,
                                leaf=asdict(leaf) if leaf else None,
                                bridge_in_disks=any(d.path == rows[1]["path"] for d in result.disks),
                                bridge_inventory=[asdict(d) for d in result.excluded
                                                  if d.path == rows[1]["path"]],
                                excluded=[asdict(d) for d in result.excluded]))
    summary = dict(cases=len(results), passed=sum(x["passed"] for x in results),
                   violations=sum(not x["passed"] for x in results), native_attempts=effects,
                   source_sha256={p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                                  for p in ("src/beamo_wipe/discover.py", "src/beamo_wipe/safety.py")},
                   results=results)
    OUT.mkdir(exist_ok=True)
    (OUT / "omitted-alias-context.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    run()
