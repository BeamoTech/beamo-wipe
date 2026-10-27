#!/usr/bin/env python3
"""Rescan a published release's package inventory for fixed Debian vulnerabilities.

The image gate runs `debsecan --only-fixed` once, at build time. Sticks are
offline and never update, so a release that was clean when built can later
lack security fixes Debian has since published. This reads the measured dpkg
inventory from a release manifest (verify it first with
scripts/verify-usb-download.py) and the Debian Security Tracker data, and
lists every source package whose installed version is older than a version
Debian has marked as fixed for the suite. It reads only; it never builds,
publishes or changes anything.

  rescan_release_packages.py MANIFEST.json [--tracker tracker.json] [--suite bookworm]

Without --tracker it downloads https://security-tracker.debian.org/tracker/data/json
into memory. Exit 0 = no fixed vulnerability is missing, 1 = some are, 2 = error.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, Iterable, List, Mapping, Optional
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from beamo_wipe.verification_evidence import verify_package_inventory  # noqa: E402
from corresponding_source import _source_of  # noqa: E402

TRACKER_URL = "https://security-tracker.debian.org/tracker/data/json"
MAX_TRACKER_BYTES = 512 * 1024 * 1024


def _order(char: str) -> int:
    if char == "~":
        return -1
    if char.isdigit():
        return 0
    if char.isalpha():
        return ord(char)
    return ord(char) + 256


def _compare_part(a: str, b: str) -> int:
    """dpkg's verrevcmp for one upstream-version or revision string."""
    while a or b:
        a_text = re.match(r"[^0-9]*", a).group(0)
        b_text = re.match(r"[^0-9]*", b).group(0)
        for i in range(max(len(a_text), len(b_text))):
            ca = _order(a_text[i]) if i < len(a_text) else 0
            cb = _order(b_text[i]) if i < len(b_text) else 0
            if ca != cb:
                return -1 if ca < cb else 1
        a, b = a[len(a_text):], b[len(b_text):]
        a_num = re.match(r"[0-9]*", a).group(0)
        b_num = re.match(r"[0-9]*", b).group(0)
        if int(a_num or 0) != int(b_num or 0):
            return -1 if int(a_num or 0) < int(b_num or 0) else 1
        a, b = a[len(a_num):], b[len(b_num):]
    return 0


def compare_versions(a: str, b: str) -> int:
    """Compare two Debian versions like `dpkg --compare-versions`."""
    def split(version: str) -> tuple[int, str, str]:
        epoch, _, rest = version.partition(":") if ":" in version else ("0", "", version)
        upstream, _, revision = rest.rpartition("-") if "-" in rest else (rest, "", "0")
        return int(epoch or 0), upstream, revision
    ea, ua, ra = split(a)
    eb, ub, rb = split(b)
    if ea != eb:
        return -1 if ea < eb else 1
    return _compare_part(ua, ub) or _compare_part(ra, rb)


def rescan(manifest: Mapping[str, Any], tracker: Mapping[str, Any], suite: str) -> List[Dict[str, Any]]:
    inventory = manifest.get("installed_packages")
    if not isinstance(inventory, Mapping) or inventory.get("measured") is not True:
        raise RuntimeError("manifest has no measured package inventory")
    inventory = verify_package_inventory(inventory)
    installed: Dict[str, str] = {}
    for entry in inventory["packages"]:
        source, version = _source_of(entry)
        if installed.setdefault(source, version) != version:
            # Mixed source versions: compare against the oldest one installed.
            if compare_versions(version, installed[source]) < 0:
                installed[source] = version
    findings = []
    for source, version in sorted(installed.items()):
        for issue, record in sorted((tracker.get(source) or {}).items()):
            release = ((record or {}).get("releases") or {}).get(suite) or {}
            fixed = release.get("fixed_version")
            if release.get("status") != "resolved" or not fixed or fixed == "0":
                continue
            if compare_versions(version, fixed) < 0:
                findings.append({
                    "source": source, "installed": version, "fixed": fixed,
                    "issue": issue, "urgency": release.get("urgency", ""),
                })
    return findings


def _load_tracker(path: Optional[Path]) -> Mapping[str, Any]:
    if path is not None:
        return json.loads(path.read_bytes())
    request = Request(TRACKER_URL, headers={"User-Agent": "beamo-wipe-rescan/1"})
    with urlopen(request, timeout=300) as response:  # noqa: S310 - fixed HTTPS URL
        data = response.read(MAX_TRACKER_BYTES + 1)
    if len(data) > MAX_TRACKER_BYTES:
        raise RuntimeError("security tracker data exceeds the size bound")
    return json.loads(data)


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--tracker", type=Path)
    parser.add_argument("--suite", default="bookworm")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        manifest = json.loads(args.manifest.read_bytes())
        findings = rescan(manifest, _load_tracker(args.tracker), args.suite)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(findings, indent=2, sort_keys=True))
    else:
        packages = sorted({item["source"] for item in findings})
        print(f"{manifest.get('beamo_wipe_version', '?')}: {len(findings)} fixed issues missing "
              f"across {len(packages)} source packages ({args.suite})")
        for item in findings:
            print(f"  {item['source']} {item['installed']} < {item['fixed']}  {item['issue']} {item['urgency']}")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
