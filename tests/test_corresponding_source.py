# SPDX-License-Identifier: GPL-3.0-or-later
"""GPL corresponding source: written offer on the USB and the archive tool.

Network access is replaced by an in-memory opener; no real download runs.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

from beamo_wipe.verification_evidence import build_package_inventory

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
COMMIT = "a" * 40
NWIPE_COMMIT = "6082bde060091e66365d852a1877f2ee80c67105"


def _load(name, filename):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


cs = _load("beamo_corresponding_source", "corresponding_source.py")


def _manifest(packages, **source):
    inventory = build_package_inventory(
        packages=packages,
        collected_from="squashfs var/lib/dpkg/status",
        apt_sources=["https://deb.debian.org/debian/"],
        source_commit=COMMIT,
        generated_at="2026-10-26T00:00:00Z",
    )
    return {
        "beamo_wipe_version": "0.2.15",
        "source": {"commit": COMMIT, "dirty": False, **source},
        "nwipe": {"version": "0.42", "commit": NWIPE_COMMIT},
        "installed_packages": inventory,
    }


PACKAGES = [
    {"name": "libc6", "version": "2.36-9+deb12u10", "arch": "amd64", "source": "glibc"},
    {"name": "libc-bin", "version": "2.36-9+deb12u10", "arch": "amd64", "source": "glibc"},
    {"name": "grub-efi-amd64-signed", "version": "1+2.06+13+deb12u1", "arch": "amd64",
     "source": "grub-efi-amd64-signed (1+2.06+13+deb12u1)"},
    {"name": "libpython3.11", "version": "3.11.2-6+deb12u6+b1", "arch": "amd64",
     "source": "python3.11 (3.11.2-6+deb12u6)"},
    {"name": "bash", "version": "5.2.15-2+b8", "arch": "amd64", "source": "bash (5.2.15-2)"},
    {"name": "tzdata", "version": "2025b-0+deb12u2", "arch": "all", "source": ""},
    {"name": "libpam0g", "version": "1.5.2-6+deb12u1", "arch": "amd64", "source": "pam"},
    {"name": "dpkg", "version": "1.21.22", "arch": "amd64", "source": ""},
    {"name": "libgcrypt20", "version": "1.10.1-3", "arch": "amd64", "source": ""},
    {"name": "e2fsprogs", "version": "1.47.0-2", "arch": "amd64", "source": ""},
    {"name": "libdb5.3", "version": "5.3.28+dfsg2-1", "arch": "amd64", "source": "db5.3"},
    {"name": "perl-base", "version": "5.36.0-7+deb12u2", "arch": "amd64", "source": "perl"},
    {"name": "libsystemd0", "version": "252.38-1~deb12u1", "arch": "amd64", "source": "systemd"},
    {"name": "libcap2", "version": "1:2.66-4", "arch": "amd64", "source": ""},
]


# ---------- the written offer shipped on the USB ----------

def test_usb_source_txt_is_a_written_offer_with_contact_and_repository():
    assets = _load("beamo_stage_live_assets_offer", "stage_live_assets.py")
    from beamo_wipe.support_contact import SUPPORT_URL

    text = assets.source_offer(SUPPORT_URL).decode("utf-8")
    assert "Written offer" in text
    assert "at least three years" in text
    assert "corresponding source code" in text
    assert "GNU General Public License" in text
    assert "no more than our cost of physically performing" in text
    assert SUPPORT_URL in text
    assert "https://github.com/BeamoTech/beamo-wipe" in text
    assert "START-HERE.html" in text
    assert "BeamoINT" not in text
    for forbidden in ("certified", "DoD", "plug and play", "guarantee"):
        assert forbidden.lower() not in text.lower()
    source = (SCRIPTS / "stage_live_assets.py").read_text(encoding="utf-8")
    assert "source = source_offer(SUPPORT_URL)" in source
    assert 'put_bytes(binary / "SOURCE.txt", source)' in source
    assert 'put_bytes(docs / "SOURCE.txt", source)' in source
    assert "BeamoINT" not in source


# ---------- plan ----------

def test_plan_maps_every_binary_to_its_exact_source_version():
    result = cs.plan(_manifest(PACKAGES))
    sources = {(s["name"], s["version"]): s["binaries"] for s in result["debian_sources"]}
    assert sources[("glibc", "2.36-9+deb12u10")] == ["libc-bin:amd64", "libc6:amd64"]
    # binNMU binaries carry the unrebuilt source version in their Source field.
    assert ("python3.11", "3.11.2-6+deb12u6") in sources
    assert ("bash", "5.2.15-2") in sources
    # No Source field: the binary name and version are the source identity.
    assert ("tzdata", "2025b-0+deb12u2") in sources
    assert ("libcap2", "1:2.66-4") in sources
    assert result["binary_package_count"] == len(PACKAGES)
    assert result["debian_source_count"] == len(sources)
    assert result["nwipe"] == {
        "version": "0.42", "commit": NWIPE_COMMIT,
        "upstream": "https://github.com/martijnvanbrummelen/nwipe",
    }
    assert result["beamo_wipe"]["commit"] == COMMIT
    assert [s["name"] for s in result["debian_sources"]] == sorted(
        s["name"] for s in result["debian_sources"]
    )
    # Deterministic: the same manifest gives byte-identical plans.
    assert cs._canonical(result) == cs._canonical(cs.plan(_manifest(PACKAGES)))


@pytest.mark.parametrize("mutate,match", [
    (lambda m: m["installed_packages"].update(measured=False), "measured"),
    (lambda m: m.pop("installed_packages"), "measured"),
    (lambda m: m["source"].update(dirty=True), "dirty"),
    (lambda m: m["source"].update(commit="abc"), "commit"),
    (lambda m: m["nwipe"].update(commit=""), "nwipe"),
    (lambda m: m["installed_packages"]["packages"][0].update(version="9.9"), "digest|sha256|inventory"),
])
def test_plan_refuses_unmeasured_dirty_or_tampered_manifests(mutate, match):
    manifest = _manifest(PACKAGES)
    mutate(manifest)
    with pytest.raises(Exception, match=match):
        cs.plan(manifest)


def test_plan_refuses_inventory_from_another_commit():
    manifest = _manifest(PACKAGES)
    manifest["source"]["commit"] = "b" * 40
    with pytest.raises(cs.SourceError, match="another source commit"):
        cs.plan(manifest)


@pytest.mark.parametrize("field", ["Glibc", "glibc (2.36", "glibc (2.36) extra", "../x", "glibc (a b)"])
def test_plan_refuses_unparseable_source_fields(field):
    packages = [{"name": "libc6", "version": "2.36-9", "arch": "amd64", "source": field}]
    # Either the inventory builder (host-path guard) or the plan refuses it.
    with pytest.raises(RuntimeError):
        cs.plan(_manifest(packages))


# ---------- fetch ----------

class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _source_files(name, version, *, tamper=None, extra=None, bad_name=None):
    upstream = version.split(":")[-1].rsplit("-", 1)[0]
    orig = f"{name}_{upstream}.orig.tar.xz"
    debian = f"{name}_{version.split(':')[-1]}.debian.tar.xz"
    blobs = {orig: f"orig {name}".encode(), debian: f"debian {name}".encode()}
    lines = "".join(
        f" {hashlib.sha256(data).hexdigest()} {len(data)} {file_name}\n"
        for file_name, data in blobs.items()
    )
    dsc_name = f"{name}_{version.split(':')[-1]}.dsc"
    blobs[dsc_name] = (
        f"-----BEGIN PGP SIGNED MESSAGE-----\n\nSource: {name}\nVersion: {version}\n"
        f"Checksums-Sha256:\n{lines}\n-----BEGIN PGP SIGNATURE-----\n"
    ).encode()
    if tamper:
        blobs[tamper] = blobs[tamper] + b"!"
    if extra:
        blobs[extra] = b"unlisted"
    if bad_name:
        blobs[bad_name] = blobs.pop(orig)
    return blobs


def _tarball(commit, name="nwipe"):
    """A tar.gz like GitHub's: git archive's pax header names the commit."""
    import io
    import tarfile

    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz", format=tarfile.PAX_FORMAT,
                      pax_headers={"comment": commit}) as archive:
        data = f"{name} source\n".encode()
        info = tarfile.TarInfo(f"{name}-{commit}/README")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def _opener(plan, *, tamper_hash=None, **variant):
    routes = {}
    for package in plan["debian_sources"]:
        name, version = package["name"], package["version"]
        blobs = _source_files(name, version, **variant.get(name, {}))
        result, fileinfo = [], {}
        for file_name, data in blobs.items():
            digest = hashlib.sha1(data).hexdigest()  # noqa: S324 - fixture content id
            result.append({"hash": digest})
            fileinfo[digest] = [{"name": file_name, "archive_name": "debian"},
                                {"name": file_name, "archive_name": "debian-security"}]
            served = data + b"x" if tamper_hash == file_name else data
            routes[f"{cs.SNAPSHOT}/file/{digest}"] = served
        meta = {"result": result, "fileinfo": fileinfo}
        from urllib.parse import quote
        routes[f"{cs.SNAPSHOT}/mr/package/{quote(name, safe='')}/{quote(version, safe='')}"
               "/srcfiles?fileinfo=1"] = json.dumps(meta).encode()
    routes[cs.NWIPE_TARBALL.format(commit=NWIPE_COMMIT)] = _tarball(NWIPE_COMMIT)
    seen = []

    def open_url(url):
        seen.append(url)
        if url not in routes:
            raise AssertionError(f"unexpected URL {url}")
        return FakeResponse(routes[url])

    return open_url, seen


SMALL = [
    {"name": "libc6", "version": "2.36-9+deb12u10", "arch": "amd64", "source": "glibc"},
    {"name": "libcap2", "version": "1:2.66-4", "arch": "amd64", "source": ""},
]


def test_fetch_downloads_verifies_and_records_every_file(tmp_path):
    plan = cs.plan(_manifest(SMALL))
    open_url, seen = _opener(plan)
    dest = tmp_path / "source-0.2.15"
    receipt = cs.fetch(plan, dest, open_url=open_url, git_archive=lambda c: b"beamo " + c.encode())
    paths = {item["path"] for item in receipt["files"]}
    assert "debian/glibc_2.36-9+deb12u10/glibc_2.36-9+deb12u10.dsc" in paths
    assert "debian/libcap2_1%3A2.66-4/libcap2_2.66-4.dsc" in paths
    assert f"upstream/nwipe-0.42-{NWIPE_COMMIT}.tar.gz" in paths
    assert f"upstream/beamo-wipe-{COMMIT}.tar.gz" in paths
    assert "SOURCES.json" in paths
    for item in receipt["files"]:
        data = (dest / item["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["sha256"]
    sums = (dest / "SHA256SUMS").read_text().splitlines()
    assert len(sums) == len(receipt["files"])
    assert json.loads((dest / "ARCHIVE.json").read_text()) == receipt
    assert all(url.startswith("https://") for url in seen)


def test_fetch_uses_github_tarball_when_commit_is_not_local(tmp_path):
    plan = cs.plan(_manifest(SMALL))
    open_url, seen = _opener(plan)
    url = cs.BEAMO_TARBALL.format(commit=COMMIT)

    def opener(target):
        if target == url:
            seen.append(target)
            return FakeResponse(_tarball(COMMIT, "beamo-wipe"))
        return open_url(target)

    receipt = cs.fetch(plan, tmp_path / "out", open_url=opener, git_archive=lambda _c: None)
    (beamo,) = [item for item in receipt["files"] if item["path"].startswith("upstream/beamo")]
    assert beamo["origin"] == url
    assert url in seen


@pytest.mark.parametrize("variant,match", [
    ({"tamper_hash": "glibc_2.36.orig.tar.xz"}, "content hash mismatch"),
    ({"glibc": {"tamper": "glibc_2.36.orig.tar.xz"}}, "checksum mismatch|content hash"),
    ({"glibc": {"extra": "glibc_2.36.extra.tar.xz"}}, "does not match"),
    ({"glibc": {"bad_name": "../escape.tar.xz"}}, "unsafe file name"),
])
def test_fetch_refuses_any_unverified_byte(tmp_path, variant, match):
    plan = cs.plan(_manifest(SMALL))
    open_url, _ = _opener(plan, **variant)
    with pytest.raises(cs.SourceError, match=match):
        cs.fetch(plan, tmp_path / "out", open_url=open_url, git_archive=lambda c: b"x")
    assert not (tmp_path / "escape.tar.xz").exists()


def test_fetch_refuses_an_existing_destination(tmp_path):
    plan = cs.plan(_manifest(SMALL))
    open_url, _ = _opener(plan)
    (tmp_path / "out").mkdir()
    with pytest.raises(FileExistsError):
        cs.fetch(plan, tmp_path / "out", open_url=open_url, git_archive=lambda c: b"x")


def test_fetch_refuses_a_foreign_plan(tmp_path):
    with pytest.raises(cs.SourceError, match="not a corresponding-source plan"):
        cs.fetch({"schema": "other"}, tmp_path / "out")


def test_default_opener_refuses_plain_http():
    with pytest.raises(cs.SourceError, match="non-HTTPS"):
        cs._default_open("http://snapshot.debian.org/mr/package/x/1/srcfiles")


def test_cli_plan_writes_new_file_and_refuses_overwrite(tmp_path, capsys):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(_manifest(PACKAGES)))
    out = tmp_path / "SOURCES.json"
    assert cs.main(["plan", str(manifest), "--out", str(out)]) == 0
    assert json.loads(out.read_text())["schema"] == cs.SCHEMA
    assert "Debian source packages" in capsys.readouterr().out
    assert cs.main(["plan", str(manifest), "--out", str(out)]) == 2


@pytest.mark.parametrize("binary,source,expected", [
    ("linux-image-6.12.95+deb12-amd64", "linux-signed-amd64 (6.12.95+1~bpo12+1)", ("linux", "6.12.95-1~bpo12+1")),
    ("linux-image-6.1.0-54-amd64", "linux-signed-amd64 (6.1.190+1)", ("linux", "6.1.190-1")),
    ("grub-efi-amd64-signed", "grub-efi-amd64-signed (1+2.06+13+deb12u2)", ("grub2", "2.06-13+deb12u2")),
    ("shim-helpers-amd64-signed", "shim-helpers-amd64-signed (1+16.1+2~deb12u1)",
     ("shim", "16.1-2~deb12u1")),
])
def test_signed_boot_wrappers_also_pull_their_real_gpl_source(binary, source, expected):
    packages = [{"name": binary, "version": "0-1", "arch": "amd64", "source": source}]
    result = cs.plan(_manifest(packages))
    sources = {(s["name"], s["version"]): s["binaries"] for s in result["debian_sources"]}
    wrapper = source.split(" ", 1)[0]
    assert any(name == wrapper for name, _ in sources)
    assert sources[expected] == [f"{binary}:amd64 (signed from)"]
    assert result["debian_source_count"] == 2


def test_debian_12_shim_signed_records_pull_shim_source():
    # Exact Debian 12 records: the Source field names shim-signed's own
    # version; the shim version is only in the binary version suffix.
    packages = [
        {"name": name, "version": "1.51~1+deb12u1+16.1-2~deb12u1", "arch": arch,
         "source": "shim-signed (1.51~1+deb12u1)"}
        for name, arch in (("shim-signed", "amd64"), ("shim-signed-common", "all"))
    ]
    packages.append({"name": "shim-helpers-amd64-signed", "version": "1+16.1+2~deb12u1",
                     "arch": "amd64", "source": ""})
    result = cs.plan(_manifest(packages))
    sources = {(s["name"], s["version"]): s["binaries"] for s in result["debian_sources"]}
    assert set(sources) == {
        ("shim-signed", "1.51~1+deb12u1"),
        ("shim-helpers-amd64-signed", "1+16.1+2~deb12u1"),
        ("shim", "16.1-2~deb12u1"),
    }
    assert sources[("shim", "16.1-2~deb12u1")] == [
        "shim-helpers-amd64-signed:amd64 (signed from)",
        "shim-signed-common:all (signed from)",
        "shim-signed:amd64 (signed from)",
    ]


def test_ordinary_sources_get_no_unsigned_companion():
    assert cs._unsigned_source("glibc", "2.36-9") is None
    assert cs._unsigned_source("shim-signed", "1.51") is None
    assert cs._unsigned_source("shim-signed", "1.51", "1.51") is None
    assert cs._unsigned_source("shim-signed", "1.51", "1.52+16.1-2") is None


@pytest.mark.parametrize("field,value", [
    ("version", "0.42/../../escaped"),
    ("version", "../0.42"),
    ("commit", "../" + "a" * 37),
    ("commit", "A" * 40),
])
def test_fetch_refuses_unsafe_nwipe_identity_before_writing(tmp_path, field, value):
    plan = cs.plan(_manifest(SMALL))
    plan["nwipe"][field] = value
    open_url, seen = _opener(plan)
    with pytest.raises(cs.SourceError, match="invalid nwipe version or commit"):
        cs.fetch(plan, tmp_path / "dest" / "out", open_url=open_url, git_archive=lambda c: b"x")
    assert not (tmp_path / "dest").exists() and seen == []
    assert not list(tmp_path.rglob("*escaped*"))


def test_fetch_refuses_an_unsafe_beamo_commit(tmp_path):
    plan = cs.plan(_manifest(SMALL))
    plan["beamo_wipe"]["commit"] = "../" + "b" * 37
    open_url, _ = _opener(plan)
    with pytest.raises(cs.SourceError, match="invalid nwipe version or commit"):
        cs.fetch(plan, tmp_path / "out", open_url=open_url, git_archive=lambda c: b"x")
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("served", ["other-commit", "not-a-tarball"])
def test_fetch_refuses_an_nwipe_tarball_for_another_commit(tmp_path, served):
    plan = cs.plan(_manifest(SMALL))
    open_url, _ = _opener(plan)
    url = cs.NWIPE_TARBALL.format(commit=NWIPE_COMMIT)
    body = _tarball("f" * 40) if served == "other-commit" else b"nwipe tarball"

    def opener(target):
        return FakeResponse(body) if target == url else open_url(target)

    with pytest.raises(cs.SourceError, match="nwipe tarball"):
        cs.fetch(plan, tmp_path / "out", open_url=opener, git_archive=lambda c: b"x")
    assert not (tmp_path / "out" / "upstream").exists()
