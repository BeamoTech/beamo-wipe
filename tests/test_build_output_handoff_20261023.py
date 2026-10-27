"""Owned-file regressions for receipt handoff and ISO bundle finalization.

Only the extracted production shell is executed: no outer CI entry point, Docker,
live build, guest, network operation, or device is used by these fixtures. Root
must review and run this module; it was authored without executing any tests.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tarfile

import pytest


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = b"owned fake gate receipt\n"


def _tool(tools: Path, name: str, body: str) -> None:
    path = tools / name
    path.write_text(f"#!{sys.executable}\n" + body, encoding="utf-8")
    path.chmod(0o755)


def _private_gate(tmp_path: Path, gate: str) -> tuple[Path, Path, dict[str, str]]:
    tools = tmp_path / "tools"
    tools.mkdir()
    mounted = tmp_path / "mounted"
    scripts = mounted / "scripts"
    scripts.mkdir(parents=True)
    for name in ("handoff_ci_outputs.py", "build_desktop.py"):
        source = ROOT / "scripts" / name
        if source.is_file():
            (scripts / name).write_bytes(source.read_bytes())
    (scripts / "ci-hosted.sh").write_text(
        "set -eu\n"
        'printf gate > "$GATE_SENTINEL"\n'
        "mkdir -p dist/evidence\n"
        'printf "owned fake gate receipt\\n" > "dist/evidence/$1.junit.xml"\n'
        'if [ "$1" = desktop-launchers ]; then\n'
        "  mkdir -p dist/desktop\n"
        '  printf windows-fixture > "dist/desktop/Start Beamo Wipe.exe"\n'
        '  printf linux-fixture > "dist/desktop/Start Beamo Wipe Linux"\n'
        '  printf "{}\\n" > dist/desktop/desktop-build.json\n'
        "fi\n",
        encoding="utf-8",
    )
    archive = tmp_path / "source.tar"
    with tarfile.open(archive, "w") as output:
        output.add(scripts, arcname="scripts")
    private = tmp_path / "private"
    private.mkdir()
    _tool(tools, "mktemp", "import os\nprint(os.environ['PRIVATE_SOURCE'])\n")
    _tool(
        tools,
        "tar",
        "import os, pathlib, sys\n"
        "if '-cf' in sys.argv:\n"
        " archive = pathlib.Path(os.environ['SOURCE_ARCHIVE'])\n"
        " sys.stdout.buffer.write(archive.read_bytes())\n"
        " raise SystemExit(0)\n"
        "os.execv('/usr/bin/tar', ['tar', *sys.argv[1:]])\n",
    )
    env = dict(
        os.environ,
        PATH=str(tools) + os.pathsep + os.environ["PATH"],
        TMPDIR=str(tmp_path),
        PRIVATE_SOURCE=str(private),
        SOURCE_ARCHIVE=str(archive),
        GATE_SENTINEL=str(tmp_path / "gate-ran"),
        FIXTURE_GATE=gate,
    )
    return mounted, private, env


def _run_private_gate(
    tmp_path: Path, mounted: Path, env: dict[str, str]
) -> subprocess.CompletedProcess[str]:
    source = (ROOT / "scripts/ci-blacksmith.sh").read_text(encoding="utf-8")
    inner = source.split('"$IMAGE" bash -ceu \'\n', 1)[1].split("\n    ' --", 1)[0]
    return subprocess.run(
        ["bash", "-ceu", inner, "--", str(mounted), "1", env["FIXTURE_GATE"]],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )


@pytest.mark.parametrize("collision", ["symlink", "regular"])
def test_receipt_handoff_refuses_existing_destination_unchanged(
    tmp_path: Path, collision: str
) -> None:
    mounted, private, env = _private_gate(tmp_path, "lint")
    evidence = mounted / "dist/evidence"
    evidence.mkdir(parents=True)
    destination = evidence / "lint.junit.xml"
    outside = tmp_path / "unrelated-receipt"
    outside.write_bytes(b"unrelated receipt must survive\n")
    if collision == "symlink":
        destination.symlink_to(outside)
    else:
        destination.write_bytes(b"previous receipt must survive\n")
    original_bytes = destination.read_bytes()
    original_inode = destination.lstat().st_ino
    original_link = os.readlink(destination) if collision == "symlink" else None

    result = _run_private_gate(tmp_path, mounted, env)

    assert (tmp_path / "gate-ran").read_bytes() == b"gate"
    assert (private / "dist/evidence/lint.junit.xml").read_bytes() == RECEIPT
    assert result.returncode != 0, result.stdout + result.stderr
    assert destination.lstat().st_ino == original_inode
    assert destination.read_bytes() == original_bytes
    assert destination.is_symlink() == (collision == "symlink")
    if original_link is not None:
        assert os.readlink(destination) == original_link
    assert outside.read_bytes() == b"unrelated receipt must survive\n"


def test_desktop_handoff_refuses_unidentified_directory_unchanged(
    tmp_path: Path,
) -> None:
    mounted, private, env = _private_gate(tmp_path, "desktop-launchers")
    destination = mounted / "dist/desktop"
    (destination / "nested").mkdir(parents=True)
    sentinel = destination / "nested/unrelated-sentinel"
    sentinel.write_bytes(b"unidentified user directory\n")
    previous = destination / "Start Beamo Wipe.exe"
    previous.write_bytes(b"unidentified previous file\n")
    original_inode = destination.stat().st_ino
    originals = {
        path.relative_to(destination): (path.stat().st_ino, path.read_bytes())
        for path in (sentinel, previous)
    }

    result = _run_private_gate(tmp_path, mounted, env)

    assert (tmp_path / "gate-ran").read_bytes() == b"gate"
    assert (
        private / "dist/desktop/Start Beamo Wipe.exe"
    ).read_bytes() == b"windows-fixture"
    assert result.returncode != 0, result.stdout + result.stderr
    assert destination.is_dir() and not destination.is_symlink()
    assert destination.stat().st_ino == original_inode
    assert {path.relative_to(destination) for path in destination.rglob("*")} == {
        Path("nested"),
        Path("nested/unrelated-sentinel"),
        Path("Start Beamo Wipe.exe"),
    }
    for name, (inode, content) in originals.items():
        assert (destination / name).stat().st_ino == inode
        assert (destination / name).read_bytes() == content


@pytest.mark.parametrize("gate", ["lint", "desktop-launchers"])
def test_clean_private_gate_handoff_control(tmp_path: Path, gate: str) -> None:
    mounted, private, env = _private_gate(tmp_path, gate)

    result = _run_private_gate(tmp_path, mounted, env)

    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "gate-ran").read_bytes() == b"gate"
    receipt = mounted / f"dist/evidence/{gate}.junit.xml"
    assert receipt.is_file() and not receipt.is_symlink()
    assert receipt.read_bytes() == RECEIPT
    assert (private / f"dist/evidence/{gate}.junit.xml").read_bytes() == RECEIPT
    if gate == "desktop-launchers":
        desktop = mounted / "dist/desktop"
        expected = {
            "Start Beamo Wipe.exe": b"windows-fixture",
            "Start Beamo Wipe Linux": b"linux-fixture",
            "desktop-build.json": b"{}\n",
        }
        assert desktop.is_dir() and not desktop.is_symlink()
        assert {path.name for path in desktop.iterdir()} == set(expected)
        for name, content in expected.items():
            assert (desktop / name).is_file() and not (desktop / name).is_symlink()
            assert (desktop / name).read_bytes() == content


def _write_bundle(directory: Path, version: str, iso_bytes: bytes) -> tuple[str, ...]:
    """Write every schema-2 field required by the canonical bundle verifier."""
    iso = f"beamo-wipe-{version}-amd64.iso"
    manifest = f"beamo-wipe-{version}-amd64.manifest.json"
    iso_sha = hashlib.sha256(iso_bytes).hexdigest()
    data = {
        "schema_version": 2,
        "beamo_wipe_version": version,
        "artifact": {
            "iso_name": iso,
            "iso_path": iso,
            "iso_sha256_sidecar": iso + ".sha256",
            "iso_sha256": iso_sha,
            "iso_size_bytes": len(iso_bytes),
        },
    }
    canonical = json.dumps(
        data, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    )
    data["_manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    raw = (json.dumps(data, sort_keys=True, indent=2) + "\n").encode("utf-8")
    manifest_sha = hashlib.sha256(raw).hexdigest()
    iso_line = f"{iso_sha}  {iso}\n".encode("ascii")
    manifest_line = f"{manifest_sha}  {manifest}\n".encode("ascii")
    files = {
        iso: iso_bytes,
        manifest: raw,
        manifest + ".sha256": manifest_line,
        iso + ".sha256": iso_line,
        "SHA256SUMS": iso_line + manifest_line,
    }
    for name, content in files.items():
        (directory / name).write_bytes(content)
    return tuple(files)


def _finalizer_source() -> tuple[str, str]:
    source = (ROOT / "scripts/build-iso.sh").read_text(encoding="utf-8")
    inode = source[
        source.index("same_regular_inode() {") : source.index(
            "\nrequire_prior_bundle_paths() {"
        )
    ]
    verifier = source[
        source.index("verify_prior_bundle() {") : source.index("\ncleanup() {")
    ]
    finalizer = 'for _f in "dist/' + source.rsplit('for _f in "dist/', 1)[1]
    finalizer = finalizer.split('\nls -lh "dist/', 1)[0]
    return inode + "\n" + verifier + "\n", finalizer


def _run_shell(project: Path, script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["sh", "-eu", "-c", script],
        cwd=project,
        env=dict(os.environ, TMPDIR=str(project)),
        capture_output=True,
        text=True,
        timeout=15,
    )


@pytest.mark.parametrize(
    "mutation,sidecar",
    [
        pytest.param("clean", None, id="clean"),
        pytest.param("inplaceiso", None, id="inplaceiso"),
        pytest.param("missingbundle", None, id="missingbundle"),
        pytest.param("wrongsidecar", "manifest", id="wrongsidecar-manifest"),
        pytest.param("wrongsidecar", "iso", id="wrongsidecar-iso"),
        pytest.param("wrongsidecar", "sums", id="wrongsidecar-sums"),
    ],
)
def test_finalization_verifies_bytes_before_discarding_backup(
    tmp_path: Path, mutation: str, sidecar: str | None
) -> None:
    project = tmp_path / "project"
    dist = project / "dist"
    dist.mkdir(parents=True)
    stage = dist / ".build-output.owned"
    stage.mkdir()
    backup = dist / ".bundle-backup.owned"
    backup.mkdir()
    version = "0.2.14"
    names = _write_bundle(dist, version, b"new ISO fixture bytes\n")
    _write_bundle(backup, version, b"old ISO fixture bytes\n")
    iso, manifest = names[:2]
    os.link(dist / iso, stage / iso)
    before_backup = {
        name: ((backup / name).stat().st_ino, (backup / name).read_bytes())
        for name in names
    }
    functions, finalizer = _finalizer_source()
    variables = {
        "ROOT": str(project),
        "OUT_DIR": str(dist),
        "BUILD_OUT": str(stage),
        "BACKUP_DIR": str(backup),
        "VERSION": version,
        "ISO_NAME": iso,
        "BUNDLE_FILES": " ".join(names),
        "bundle_in_progress": "2",
    }
    prefix = "".join(
        f"{key}={shlex.quote(value)}\n" for key, value in variables.items()
    )
    prefix += functions
    # Each adversarial case first proves both complete bundles are valid using
    # the actual extracted canonical verifier, rather than a test-side model.
    validated = _run_shell(
        project,
        prefix + 'verify_prior_bundle "$OUT_DIR"\nverify_prior_bundle "$BACKUP_DIR"\n',
    )
    assert validated.returncode == 0, validated.stdout + validated.stderr

    if mutation == "inplaceiso":
        before = (dist / iso).stat()
        (dist / iso).write_bytes(b"bad ISO fixture bytes\n")
        after = (dist / iso).stat()
        assert (before.st_dev, before.st_ino, before.st_size) == (
            after.st_dev,
            after.st_ino,
            after.st_size,
        )
        assert os.path.samefile(dist / iso, stage / iso)
    elif mutation == "wrongsidecar":
        sidecars = {
            "manifest": manifest + ".sha256",
            "iso": iso + ".sha256",
            "sums": "SHA256SUMS",
        }
        assert sidecar is not None
        changed = dist / sidecars[sidecar]
        original = changed.read_bytes()
        inode = changed.stat().st_ino
        replacement = (b"0" if original[:1] != b"0" else b"1") + original[1:]
        changed.write_bytes(replacement)
        assert changed.is_file() and not changed.is_symlink()
        assert changed.stat().st_ino == inode
        assert len(replacement) == len(original) and replacement != original

    final_bytes = {name: (dist / name).read_bytes() for name in names}
    if mutation == "missingbundle":
        # Remove the public bundle only after the final inode check succeeds.
        # The verifier's ordinary preflight allowance for no prior output must
        # never authorize retiring a backup during current-build finalization.
        prefix = prefix.replace(
            "same_regular_inode() {", "original_same_regular_inode() {"
        )
        prefix += (
            "same_regular_inode() {\n"
            '  original_same_regular_inode "$@" || return\n'
            '  for name in $BUNDLE_FILES; do rm -f -- "$OUT_DIR/$name"; done\n'
            "}\n"
        )
    result = _run_shell(project, prefix + finalizer)

    if mutation == "clean":
        assert result.returncode == 0, result.stdout + result.stderr
        assert all(not (backup / name).exists() for name in names)
    else:
        assert result.returncode != 0, result.stdout + result.stderr
        assert result.stderr.strip(), "mutation refusal must provide an error"
        assert backup.is_dir() and not backup.is_symlink()
        assert {path.name for path in backup.iterdir()} == set(names)
        for name, (inode, content) in before_backup.items():
            assert (backup / name).is_file() and not (backup / name).is_symlink()
            assert (backup / name).stat().st_ino == inode
            assert (backup / name).read_bytes() == content
    if mutation == "missingbundle":
        assert not any((dist / name).exists() for name in names)
        assert (stage / iso).read_bytes() == final_bytes[iso]
    else:
        assert {name: (dist / name).read_bytes() for name in names} == final_bytes
        assert os.path.samefile(dist / iso, stage / iso)
