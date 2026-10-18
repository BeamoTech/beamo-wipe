"""Prepared duplicate-observation proof; root runtime admission required."""
from __future__ import annotations

import copy
from dataclasses import asdict
import itertools
import json
import os
from unittest.mock import patch

import omitted_alias_context_probe as base


def run():
    results = []
    conflicts = {"read_only": ("ro", True), "serial": ("serial", "OTHER-SERIAL"),
                 "wwn": ("wwn", base.Y), "size": ("size", 256_000_000_000),
                 "bus": ("tran", "iscsi"), "mounted": ("mountpoints", ["/media/fake-data"])}
    with patch.dict(os.environ, {"BEAMO_WIPE_DRY_RUN": "1"}), \
            patch.object(os.path, "realpath", base.fake_realpath), \
            patch.object(base.discovery, "run_lsblk", base.forbidden), \
            patch.object(base.discovery, "read_mount_sources", base.forbidden), \
            patch.object(base.discovery, "read_cmdline", base.forbidden), \
            patch.object(base.discovery.subprocess, "run", base.forbidden), \
            patch.object(base.discovery.subprocess, "Popen", base.forbidden), \
            patch("builtins.open", base.guarded_io(base.original_open)), \
            patch.object(base.io, "open", base.guarded_io(base.original_io_open)), \
            patch.object(os, "open", base.guarded_io(base.original_os_open)), \
            patch.object(os, "lstat", base.guarded_io(base.original_lstat)), \
            patch("beamo_wipe.diagnostics.log_diag", lambda *_a, **_k: None), \
            patch("beamo_wipe.diagnostics.emit_serial_marker", lambda *_a, **_k: None):
        for conflict, display, order in itertools.product(conflicts,
                ("valid", "overlong_model", "overlong_layout_label"), ((0, 1), (1, 0))):
            boot = dict(name="sdz", path="/dev/sdz", type="disk", tran="usb",
                        size=16_000_000_000, serial="FAKE-BOOT", wwn="50014ee20aa00009",
                        ro=False, mountpoints=["/run/live/medium"])
            first = dict(name="sda", path="/dev/sda", type="disk", tran="sata", size=128_000_000_000,
                         serial="FAKE-TARGET", wwn=base.X, model="Good model", ro=False, mountpoints=[])
            second = copy.deepcopy(first)
            field, value = conflicts[conflict]
            second[field] = value
            if display == "overlong_model":
                second["model"] = "M" * 129
            elif display == "overlong_layout_label":
                second["label"] = "L" * 129
            rows = [first, second]
            payload = {"blockdevices": [copy.deepcopy(rows[i]) for i in order] + [boot]}
            result = base.discovery.discover(lsblk_payload=payload, mount_sources=["/dev/sdz"], cmdline="", env={})
            selectable = {d.path for d in result.selectable}
            target = next((d for d in result.selectable if d.path == "/dev/sda"), None)
            identity_accepted, token = False, ""
            if target:
                try:
                    base.safety.assert_boot_excluded(result)
                    base.safety.assert_disk_identity(target, result)
                    token = base.safety.confirm_spec(target, base.safety.listed_disks(result)).token
                    identity_accepted = bool(token)
                except base.safety.SafetyError:
                    pass
            results.append(dict(conflict=conflict, display=display, order=order, payload=payload,
                                boot_identified=result.boot_identified, error=result.error,
                                diagnostic=result.diagnostic, selectable=sorted(selectable),
                                target=asdict(target) if target else None,
                                target_identity_accepted=identity_accepted, token=token,
                                passed="/dev/sda" not in selectable))
    summary = dict(cases=len(results), passed=sum(r["passed"] for r in results),
                   violations=sum(not r["passed"] for r in results),
                   native_attempts=base.effects, results=results)
    (base.OUT / "omitted-duplicate-observation.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    run()
