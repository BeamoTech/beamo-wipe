"""Rollback never replaces a concurrent output or consumes an un-restored backup."""

import os
from pathlib import Path
import shlex
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _identity(path):
    info = path.lstat()
    return info.st_dev, info.st_ino


def _rollback(tmp_path, collision, prior_exit, fault="", prior_kind="file"):
    root = tmp_path / "owned rollback fixture"
    root.mkdir()
    out, backup, stage, binaries = [
        root / name for name in ("out", "backup", "stage", "bin")
    ]
    for directory in (out, backup, stage, binaries):
        directory.mkdir()
    name = "owned-fixture.iso"
    prior = backup / name
    if prior_kind == "directory":
        prior.mkdir()
        (prior / "keep").write_bytes(b"prior ISO\n")
    else:
        prior.write_bytes(b"prior ISO\n")
    prior_identity = _identity(prior)
    outside = root / "outside"
    outside.write_bytes(b"outside\n")
    info = root / "docker-info"
    info.write_bytes(b"fixture\n")
    ledger = root / "injection"
    python = shutil.which("python3")
    assert python
    injection = (
        "#!/bin/sh\nset -eu\nfor destination do :; done\n"
        'case "$COLLISION" in\n'
        'file) printf "peer\\n" > "$destination";;\n'
        'directory) mkdir -- "$destination"; printf "peer\\n" > "$destination/sentinel";;\n'
        'symlink) ln -s "$OUTSIDE" "$destination";;\n'
        "none) :;;\nesac\n"
        'if [ "$COLLISION" != none ]; then stat -c "%d %i" -- "$destination" > "$LEDGER"; fi\n'
    )
    for tool in ("mv", "python3"):
        executable = python if tool == "python3" else shutil.which("mv")
        assert executable
        if fault and tool == "python3":
            # Patch only the chosen operation inside the production heredoc.
            code = (
                "import errno,os,sys; "
                "defect=lambda *a,**k:(_ for _ in ()).throw(OSError(errno.EACCES,'injected refusal')); "
                f"os.{fault}=defect; exec(compile(sys.stdin.read(),'<restore>','exec'))"
            )
            command = (
                f'shift\nexec {shlex.quote(executable)} -c {shlex.quote(code)} "$@"\n'
            )
        else:
            command = f'exec {shlex.quote(executable)} "$@"\n'
        shim = binaries / tool
        shim.write_text(injection + command)
        shim.chmod(0o700)

    source = (ROOT / "scripts/build-iso.sh").read_text()
    cleanup = (
        "cleanup() {"
        + source.split("cleanup() {", 1)[1].split("\ntrap cleanup EXIT", 1)[0]
    )
    helper = ""
    if "restore_prior_file() {" in source:
        helper = (
            "restore_prior_file() {"
            + source.split("restore_prior_file() {", 1)[1].split("\ncleanup()", 1)[0]
        )
    variables = dict(
        OUT_DIR=out,
        BACKUP_DIR=backup,
        BUILD_OUT=stage,
        ISO_NAME=name,
        BUNDLE_FILES=name,
        DOCKER_INFO=info,
        bundle_in_progress=1,
    )
    script = (
        "set -eu\n"
        + "\n".join(
            key + "=" + shlex.quote(str(value)) for key, value in variables.items()
        )
        + "\n"
        + helper
        + "\n"
        + cleanup
        + f"\ntrap cleanup EXIT\nexit {prior_exit}\n"
    )
    environment = dict(
        os.environ,
        PATH=str(binaries) + os.pathsep + os.defpath,
        COLLISION=collision,
        OUTSIDE=str(outside),
        LEDGER=str(ledger),
    )
    result = subprocess.run(
        ["sh", "-c", script],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == prior_exit, result.stdout + result.stderr
    assert outside.read_bytes() == b"outside\n"
    return result, out / name, prior, prior_identity, ledger


@pytest.mark.parametrize("prior_exit", [0, 7])
@pytest.mark.parametrize("collision", ["file", "directory", "symlink"])
def test_rollback_preserves_output_created_after_absence_check(
    tmp_path, collision, prior_exit
):
    result, destination, prior, original, ledger = _rollback(
        tmp_path, collision, prior_exit
    )
    assert ledger.is_file(), "collision injection did not execute"
    assert _identity(destination) == tuple(map(int, ledger.read_text().split()))
    if collision == "file":
        assert destination.read_bytes() == b"peer\n"
    elif collision == "directory":
        assert (destination / "sentinel").read_bytes() == b"peer\n"
        assert not (destination / destination.name).exists()
    else:
        assert destination.is_symlink()
        assert destination.read_bytes() == b"outside\n"
    assert _identity(prior) == original
    assert prior.read_bytes() == b"prior ISO\n"
    assert "backup retained" in result.stderr


@pytest.mark.parametrize("prior_exit", [0, 7])
def test_rollback_restores_prior_file_when_destination_stays_absent(
    tmp_path, prior_exit
):
    _, destination, prior, original, _ = _rollback(tmp_path, "none", prior_exit)
    assert _identity(destination) == original
    assert destination.read_bytes() == b"prior ISO\n"
    assert not prior.exists()
    assert not prior.parent.exists()


@pytest.mark.parametrize("fault", ["link", "unlink"])
@pytest.mark.parametrize("prior_exit", [0, 7])
def test_rollback_retains_backup_when_restore_operation_fails(
    tmp_path, fault, prior_exit
):
    result, destination, prior, original, _ = _rollback(
        tmp_path, "none", prior_exit, fault
    )
    assert _identity(prior) == original
    assert prior.read_bytes() == b"prior ISO\n"
    assert "backup retained" in result.stderr
    if fault == "link":
        assert not destination.exists()
    else:
        assert _identity(destination) == original
        assert destination.read_bytes() == b"prior ISO\n"


@pytest.mark.parametrize("prior_exit", [0, 7])
@pytest.mark.parametrize("collision", ["file", "directory", "symlink", "none"])
def test_rollback_restores_or_retains_directory_substituted_during_backup(
    tmp_path, collision, prior_exit
):
    result, destination, prior, original, ledger = _rollback(
        tmp_path, collision, prior_exit, prior_kind="directory"
    )
    if collision == "none":
        assert _identity(destination) == original
        assert (destination / "keep").read_bytes() == b"prior ISO\n"
        assert not prior.exists()
    else:
        assert _identity(destination) == tuple(map(int, ledger.read_text().split()))
        assert _identity(prior) == original
        assert (prior / "keep").read_bytes() == b"prior ISO\n"
        assert "backup retained" in result.stderr
        if collision == "directory":
            assert (destination / "sentinel").read_bytes() == b"peer\n"
            assert not (destination / destination.name).exists()
        elif collision == "file":
            assert destination.read_bytes() == b"peer\n"
        else:
            assert destination.is_symlink()
            assert destination.read_bytes() == b"outside\n"
