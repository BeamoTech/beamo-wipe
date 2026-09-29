#!/usr/bin/env python3
"""Develop Beamo Wipe with fake devices; see docs/development.md."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def venv_python(host=None):
    host = host or sys.platform
    directory = ROOT / (".venv-" + host)
    return directory / ("Scripts/python.exe" if host == "win32" else "bin/python")


def python():
    candidate = venv_python()
    return str(candidate if candidate.is_file() else Path(sys.executable))


def fake_environment(*, preview=False):
    env = os.environ.copy()
    for key in (
        "BEAMO_WIPE_LIVE",
        "BEAMO_WIPE_BOOT_DEVICE",
        "BEAMO_DESKTOP_NATIVE_INVENTORY_TEST",
        "BEAMO_WIPE_DEMO",
    ):
        env.pop(key, None)
    env.update(BEAMO_WIPE_DRY_RUN="1", PYTHONPATH=str(ROOT / "src"))
    if preview:
        env["BEAMO_WIPE_DEMO"] = "1"
    return env


def live_environment():
    # Do not clear live markers to make a development command work on the kiosk.
    if os.environ.get("BEAMO_WIPE_LIVE") == "1":
        return True
    if sys.platform != "linux":
        return False
    try:
        return (
            "boot=live" in Path("/proc/cmdline").read_text().split()
            or Path("/run/live/medium").is_mount()
        )
    except OSError:
        return True  # Unknown Linux runtime: refuse to start a preview/test.


def run(argv, **kwargs):
    try:
        return subprocess.run(argv, cwd=kwargs.pop("cwd", ROOT), **kwargs).returncode
    except OSError as exc:
        print(f"Could not run {argv[0]}: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        return 130


def wsl(argv):
    executable = shutil.which("wsl.exe")
    if not executable:
        print(
            "The Python wizard needs Linux on Windows. Install WSL2 with Ubuntu, then see docs/development.md.",
            file=sys.stderr,
        )
        return 2
    try:
        conversion = subprocess.run(
            [executable, "--exec", "wslpath", "-a", "-u", str(ROOT)],
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        print(f"WSL2 could not start: {exc}", file=sys.stderr)
        return 2
    if conversion.returncode or not conversion.stdout.strip().startswith("/"):
        print(
            "WSL2 path conversion failed. Start your Ubuntu distribution and install python3 and python3-venv.\n"
            + (conversion.stderr or ""),
            file=sys.stderr,
        )
        return conversion.returncode or 2
    path = conversion.stdout.strip().rstrip("/") + "/dev.py"
    return run([executable, "--exec", "python3", path, *argv])


DOCTOR_OPERATIONS = (
    "local",
    "test",
    "test-native",
    "preview",
    "preview-web",
    "desktop",
    "qualification",
)


def doctor_probe(argv, *, env=None):
    """Read a local version/module result; never print subprocess diagnostics."""
    try:
        result = subprocess.run(
            argv, cwd=ROOT, capture_output=True, text=True, timeout=5, env=env
        )
    except subprocess.TimeoutExpired:
        return None, "probe exceeded 5 seconds"
    except (OSError, UnicodeError):
        return None, "executable could not start"
    if result.returncode:
        return None, "probe failed; repair the selected local tool"
    return result.stdout, None


def doctor(operation="local"):
    checks = {
        "operation": operation,
        "python": sys.version.split()[0],
        "host": sys.platform,
        "machine": platform.machine(),
        "checkout": str(ROOT),
        "environment_python": python(),
        "git": shutil.which("git"),
        "live_environment": live_environment(),
    }
    problems = []
    notes = [
        "Local preflight only; no disks, authentication, network checks, builds or CI dispatch.",
        "Each local probe is bounded to 5 seconds; at most two probes run.",
        "Current qualification: Blacksmith via .github/workflows/ci.yml (CI gate).",
        "Publication is separately authorized release.yml; see docs/ci.md.",
    ]
    if sys.version_info < (3, 10):
        problems.append("Install Python 3.10 or newer.")
    if not checks["git"]:
        problems.append("Install Git for this checkout.")
    if checks["live_environment"]:
        problems.append(
            "Use a separate development machine, not the live erasure system."
        )
    elif operation == "qualification":
        checks["gh"] = shutil.which("gh")
        notes.append(
            "gh is optional for the CLI route; GitHub's web UI can open PRs and inspect CI. Authentication and repository access are not probed."
        )
        notes.append(
            "PRs to main and pushes to main trigger full CI. Manual dispatch also needs authorization. This doctor never triggers them."
        )
    elif sys.platform == "win32" and operation in ("test", "preview", "preview-web"):
        checks["wsl"] = shutil.which("wsl.exe")
        problems.append(
            "Run this doctor operation inside the WSL2 Ubuntu checkout; Linux dependencies are not checked here."
            if checks["wsl"]
            else "Install WSL2 Ubuntu for Python wizard work; see docs/development.md."
        )
        notes.append("For portable native tooling tests use doctor --for test-native.")
    else:
        modules = ["venv", "pip"] if operation == "local" else []
        if operation in ("test", "test-native"):
            modules = ["pytest"]
        if operation == "preview":
            modules = ["tkinter"]
        output, error = doctor_probe(
            [
                python(),
                "-c",
                "import importlib.util,json,sys; print(json.dumps({'version':list(sys.version_info[:3]),"
                "'modules':{n:importlib.util.find_spec(n) is not None for n in sys.argv[1:]}}))",
                *modules,
            ],
            env=fake_environment(),
        )
        try:
            data = json.loads(output) if output is not None else None
            if (
                not isinstance(data, dict)
                or not isinstance(data.get("version"), list)
                or len(data["version"]) != 3
                or any(type(v) is not int for v in data["version"])
                or not isinstance(data.get("modules"), dict)
                or any(type(data["modules"].get(n)) is not bool for n in modules)
            ):
                raise ValueError("invalid probe output")
        except (ValueError, TypeError):
            problems.append(
                "Selected Python "
                + (error or "returned invalid probe output")
                + ". Repair or recreate its environment."
            )
        else:
            checks["environment_version"] = ".".join(map(str, data["version"]))
            checks["modules"] = data["modules"]
            if tuple(data["version"]) < (3, 10):
                problems.append(
                    "The selected environment needs Python 3.10 or newer; recreate it."
                )
            missing = [n for n in modules if not data["modules"][n] and n != "tkinter"]
            if missing:
                problems.append(
                    "Missing "
                    + ", ".join(missing)
                    + "; follow setup in docs/development.md."
                )
            if operation == "preview":
                notes.append(
                    "Tk availability is not a display/version check; preview selects compatible Tk or falls back to console. Web preview needs no Tk."
                )
        if operation == "desktop":
            go = shutil.which(os.environ.get("BEAMO_GO_BIN", "go"))
            checks["go"] = go
            try:
                pin = re.search(
                    r"^go (\d+\.\d+\.\d+)$", (ROOT / "desktop/go.mod").read_text(), re.M
                )
            except (OSError, UnicodeError):
                pin = None
            if not pin:
                problems.append(
                    "Cannot read the desktop Go version pin; restore desktop/go.mod."
                )
            elif not go:
                problems.append(f"Install Go {pin[1]} or select it with BEAMO_GO_BIN.")
            else:
                env = fake_environment()
                env["GOTOOLCHAIN"] = "local"
                output, error = doctor_probe([go, "version"], env=env)
                version = re.match(r"go version (go\d+\.\d+\.\d+)\s", output or "")
                checks["go_version"] = version[1] if version else "unavailable"
                if error or not version or version[1] != "go" + pin[1]:
                    problems.append(
                        f"Select pinned Go {pin[1]}; "
                        + (error or "version does not match")
                        + "."
                    )
        if operation in ("test", "test-native"):
            notes.append(
                "Module presence is not a passing test suite. Full Linux GTK/Orca, display and image coverage belong to the hosted gate; report local skips/failures."
            )
    checks.update(
        status="blocked" if problems else "ok", problems=problems, notes=notes
    )
    print(json.dumps(checks, indent=2))
    return 2 if problems else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    child = sub.add_parser(
        "doctor", help="Local prerequisite checks; never authenticate or trigger CI"
    )
    child.add_argument(
        "--for",
        dest="operation",
        choices=DOCTOR_OPERATIONS,
        default="local",
        help="Check only this operation's local prerequisites (default: local)",
    )
    for name in ("setup", "test"):
        child = sub.add_parser(name)
        child.add_argument(
            "--native",
            action="store_true",
            help="Native developer tooling only; no Python wizard or Linux acceptance claims",
        )
    child = sub.add_parser(
        "preview", help="Fake wizard preview; Windows delegates to WSL2"
    )
    child.add_argument("args", nargs=argparse.REMAINDER)
    sub.add_parser(
        "desktop-build", help="Build Windows and Linux launchers with pinned Go"
    )
    sub.add_parser(
        "desktop-test", help="Native Go unit tests and vet; no host inventory opt-in"
    )
    argv = list(sys.argv[1:] if argv is None else argv)
    preview_args = argv[1:] if argv[:1] == ["preview"] else []
    args = parser.parse_args(["preview"] if argv[:1] == ["preview"] else argv)
    if args.command == "doctor":
        return doctor(args.operation)
    if live_environment():
        print(
            "Development commands are disabled on the live erasure system. Use a separate development machine.",
            file=sys.stderr,
        )
        return 2
    if sys.version_info < (3, 10):
        print("Python 3.10 or newer is required.", file=sys.stderr)
        return 2
    if args.command == "preview":
        if preview_args[:1] == ["--"]:
            preview_args = preview_args[1:]
        if sys.platform == "win32":
            return wsl(["preview", *preview_args])
        env = fake_environment(preview=True)
        # Preserve the canonical Mac Tk >=8.6.13 selection and console fallback.
        # Other hosts use the development venv when present.
        if sys.platform != "darwin":
            env["BEAMO_WIPE_PREVIEW_PYTHON"] = python()
        return run(["sh", str(ROOT / "scripts/preview.sh"), *preview_args], env=env)
    if (
        args.command in ("setup", "test")
        and sys.platform == "win32"
        and not args.native
    ):
        return wsl([args.command])
    if args.command == "setup":
        destination = venv_python().parents[1]
        if not venv_python().is_file():
            code = run([sys.executable, "-m", "venv", str(destination)])
            if code:
                print(
                    "Environment creation failed. On Debian/Ubuntu install python3-venv; rerun setup to retry.",
                    file=sys.stderr,
                )
                return code
        code = run(
            [python(), "-m", "pip", "install", "--upgrade", "pip>=23", "setuptools>=68"]
        )
        if code:
            return code
        packages = (
            ["pytest==9.0.3"]
            if args.native
            else ["-e", ".[dev]", "pytest==9.0.3", "ruff==0.9.2", "mypy==2.1.0"]
        )
        return run([python(), "-m", "pip", "install", *packages])
    if args.command == "test":
        cmd = [python(), "-m", "pytest"] + (["developer_tests"] if args.native else [])
        env = fake_environment()
        # Isolated Xvfb avoids replacing the user's desktop or depending on its DPI.
        if (
            not args.native
            and sys.platform == "linux"
            and shutil.which("xvfb-run")
            and shutil.which("dbus-run-session")
        ):
            cmd = [
                "dbus-run-session",
                "--",
                "xvfb-run",
                "-a",
                "-s",
                "-screen 0 1600x1000x24 -dpi 72",
                *cmd,
            ]
        print(
            "Running developer tooling tests only."
            if args.native
            else "Running the full checkout suite; environment-dependent skips remain visible.",
            flush=True,
        )
        return run(cmd, env=env)
    if args.command == "desktop-build":
        return run([python(), str(ROOT / "scripts/build_desktop.py")])
    env = fake_environment()
    env["GOTOOLCHAIN"] = "local"
    env.pop("GOOS", None)
    env.pop("GOARCH", None)
    go = os.environ.get("BEAMO_GO_BIN", "go")
    for operation in (["test", "./..."], ["vet", "./..."]):
        code = run([go, *operation], cwd=ROOT / "desktop", env=env)
        if code:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
