"""Keep the regular-file USB walkthrough discoverable and its links portable."""

import json
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/release-verification.md"


def usb_section():
    text = DOC.read_text(encoding="utf-8")
    return text.split("### USB image download verification\n", 1)[1].split("### ISO verification", 1)[0]


def test_versioned_example_matches_inventory_filenames_and_approved_key():
    section = usb_section()
    version = re.search(r"BEAMO_VERSION='([0-9]+\.[0-9]+\.[0-9]+)'", section)[1]
    commit = re.search(r"BEAMO_COMMIT='([0-9a-f]{40})'", section)[1]
    fingerprint = re.search(r"BEAMO_KEY_SHA256='([0-9a-f]{64})'", section)[1]
    registry = json.loads((ROOT / "packaging/release-keys/keys.json").read_text(encoding="utf-8"))
    assert any(key["fingerprint"] == fingerprint and key["status"] == "active"
               for key in registry["keys"].values())
    assert f"/releases/tag/v{version}" in section
    assert f"/blob/{commit}/packaging/release-keys/KEYS.md" in section
    artifacts = DOC.read_text(encoding="utf-8").split("## What the manifest contains", 1)[0]
    for suffix in ("img.gz", "img.gz.sha256", "img", "img.json", "manifest.json", "manifest.json.sig"):
        assert f"`beamo-wipe-{version}-amd64.{suffix}`" in artifacts
    assert "`release-downloads.json` + `release-downloads.json.sig`" in artifacts


def test_download_block_authenticates_before_download_and_extract():
    section = usb_section()
    block = section.split("```sh\n", 1)[1].split("```", 1)[0]
    steps = ["set -euC", "mktemp -d", 'cd "$BEAMO_USB_WORK"',
             "fetch_usb_file 'release-downloads.json'",
             "fetch_usb_file 'release-downloads.json.sig'",
             'fetch_usb_file "$BEAMO_STEM.manifest.json"',
             'fetch_usb_file "$BEAMO_STEM.manifest.json.sig"',
             'fetch_usb_file "$BEAMO_STEM.img.json"',
             "verify_usb_files metadata", 'fetch_usb_file "$BEAMO_STEM.img.gz"',
             "verify_usb_files extract", "verify_usb_files verify"]
    positions = [block.index(step) for step in steps]
    assert positions == sorted(positions)
    assert '--directory "$BEAMO_USB_WORK"' in block
    assert '--registry "$BEAMO_SOURCE/packaging/release-keys/keys.json"' in block
    assert '"$BEAMO_PYTHON" "$BEAMO_SOURCE/scripts/verify-usb-download.py"' in block
    assert 'BEAMO_PYTHON="$BEAMO_SOURCE/.venv-linux/bin/python"' in block
    assert 'BEAMO_PYTHON="$BEAMO_SOURCE/.venv-darwin/bin/python"' in block
    assert '--proto-redir \'=https\'' in block
    assert not re.search(r"/dev/|\bsudo\b|\bdd\b|\bgunzip\b|\.iso\b", block)
    for filename in re.findall(r"^fetch_usb_file (.+)$", block, re.MULTILINE):
        assert "*" not in filename


def test_usb_links_are_portable_and_targets_exist_in_checkout():
    assert all(urlparse(target).scheme == "https" for target in re.findall(r"\]\(([^)]+)\)", usb_section()))
    fragments = [(DOC, usb_section()),
                 (ROOT / "README.md", (ROOT / "README.md").read_text(encoding="utf-8").split("## Flash a USB for testing", 1)[1].split("## Unit tests", 1)[0]),
                 (ROOT / "docs/runbook.md", (ROOT / "docs/runbook.md").read_text(encoding="utf-8").split("| Authenticated release inventory", 1)[1].split("\n", 1)[0])]
    for source, text in fragments:
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if urlparse(target).scheme:
                assert target.startswith("https://github.com/BeamoTech/beamo-wipe/")
                # URL shape/portability only; the dated validation receipt
                # separately checks HTTP status and the pinned page's anchors.
                for base in ("https://github.com/BeamoTech/beamo-wipe/blob/main/docs/",
                             "https://github.com/BeamoTech/beamo-wipe/releases/tag/v0.2.12"):
                    assert urljoin(base, target) == target
                parsed = urlparse(target)
                prefix = "/BeamoTech/beamo-wipe/blob/"
                if not parsed.path.startswith(prefix):
                    continue
                revision, path = parsed.path[len(prefix):].split("/", 1)
                assert re.fullmatch(r"[0-9a-f]{40}", revision)
                destination, anchor = ROOT / path, parsed.fragment
            else:
                path, _, anchor = target.partition("#")
                destination = source.parent / path
            assert destination.is_file(), (source, target)
            if anchor:
                headings = re.findall(r"^#{1,6} (.+)$", destination.read_text(encoding="utf-8"), re.MULTILINE)
                slugs = [re.sub(r"[^\w\- ]", "", h.lower()).replace(" ", "-") for h in headings]
                assert anchor in slugs, (source, target)
