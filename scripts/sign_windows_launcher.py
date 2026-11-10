#!/usr/bin/env python3
"""Sign the Windows launcher with Microsoft Artifact Signing, then verify it.

Not used by any workflow yet. It runs only after the owner has bought the
service and handed back the settings named in docs/code-signing.md.

The script signs only the exact paths it is given. Each path must be a
regular, unsigned file named "Start Beamo Wipe.exe". It never prints the
access token: jsign reads it from the environment by name. Use --dry-run to
check the settings and paths without signing anything. If any step fails,
the exit code is 2 and the caller must throw the launchers away and rebuild.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys

LAUNCHER_NAME = "Start Beamo Wipe.exe"
MAX_LAUNCHER_BYTES = 64 * 1024 * 1024
JSIGN_VERSION = "7.6"
# GitHub release asset digest for jsign-7.6.jar (ebourg/jsign, 2026-10-12).
JSIGN_SHA256 = "6cf58aa080e7ff82656f320cff8d4a3bff30408df8766806dcba3740dd839fa5"
TIMESTAMP_URL = "http://timestamp.acs.microsoft.com"
TOKEN_ENV = "BEAMO_SIGN_ACCESS_TOKEN"
SETTINGS = (
    "BEAMO_SIGN_ENDPOINT",
    "BEAMO_SIGN_ACCOUNT",
    "BEAMO_SIGN_PROFILE",
    "BEAMO_SIGN_PUBLISHER",
    "BEAMO_SIGN_JSIGN_JAR",
    "BEAMO_SIGN_CA_FILE",
)
_ENDPOINT = re.compile(r"https://[a-z0-9]{2,8}\.codesigning\.azure\.net/?")
_ACCOUNT = re.compile(r"[A-Za-z](?!.*--)[A-Za-z0-9-]{1,22}[A-Za-z0-9]")
_PROFILE = re.compile(r"[A-Za-z](?!.*--)[A-Za-z0-9-]{3,98}[A-Za-z0-9]")
_PUBLISHER = re.compile(r"[^\x00-\x1f\x7f]{2,200}")

Runner = Callable[..., subprocess.CompletedProcess]


class SigningRefused(Exception):
    """A setting, tool or launcher is not safe to sign with."""


@dataclass(frozen=True)
class Settings:
    endpoint: str
    account: str
    profile: str
    publisher: str
    jsign_jar: Path
    ca_file: Path
    token_set: bool


def load_settings(env: Mapping[str, str], *, need_token: bool) -> Settings:
    """Read the non-secret settings. Never read or return the token value."""
    missing = [name for name in SETTINGS if not env.get(name, "").strip()]
    if need_token and not env.get(TOKEN_ENV, ""):
        missing.append(TOKEN_ENV)
    if missing:
        raise SigningRefused("missing required environment: " + ", ".join(missing))
    endpoint = env["BEAMO_SIGN_ENDPOINT"].strip()
    if not _ENDPOINT.fullmatch(endpoint):
        raise SigningRefused(
            "BEAMO_SIGN_ENDPOINT must be an https://<region>.codesigning.azure.net endpoint"
        )
    account = env["BEAMO_SIGN_ACCOUNT"].strip()
    if not _ACCOUNT.fullmatch(account):
        raise SigningRefused(
            "BEAMO_SIGN_ACCOUNT is not a valid Artifact Signing account name"
        )
    profile = env["BEAMO_SIGN_PROFILE"].strip()
    if not _PROFILE.fullmatch(profile):
        raise SigningRefused(
            "BEAMO_SIGN_PROFILE is not a valid certificate profile name"
        )
    publisher = env["BEAMO_SIGN_PUBLISHER"].strip()
    if not _PUBLISHER.fullmatch(publisher):
        raise SigningRefused("BEAMO_SIGN_PUBLISHER must be the plain certificate name")
    return Settings(
        endpoint=endpoint.rstrip("/"),
        account=account,
        profile=profile,
        publisher=publisher,
        jsign_jar=Path(env["BEAMO_SIGN_JSIGN_JAR"]),
        ca_file=Path(env["BEAMO_SIGN_CA_FILE"]),
        token_set=bool(env.get(TOKEN_ENV, "")),
    )


def certificate_table(data: bytes) -> tuple[int, int]:
    """Return the PE certificate table (offset, size); (0, 0) means unsigned."""
    if len(data) < 0x40 or data[:2] != b"MZ":
        raise SigningRefused("launcher is not a Windows program (no MZ header)")
    (pe_offset,) = struct.unpack_from("<I", data, 0x3C)
    if pe_offset + 24 > len(data) or data[pe_offset : pe_offset + 4] != b"PE\0\0":
        raise SigningRefused("launcher has no PE header")
    optional = pe_offset + 24
    if optional + 2 > len(data):
        raise SigningRefused("launcher PE header is truncated")
    (magic,) = struct.unpack_from("<H", data, optional)
    if magic == 0x10B:
        count_at, directories = optional + 92, optional + 96
    elif magic == 0x20B:
        count_at, directories = optional + 108, optional + 112
    else:
        raise SigningRefused("launcher has an unknown PE optional header")
    if count_at + 4 > len(data):
        raise SigningRefused("launcher PE header is truncated")
    (count,) = struct.unpack_from("<I", data, count_at)
    if count < 5:
        return (0, 0)
    entry = directories + 4 * 8
    if entry + 8 > len(data):
        raise SigningRefused("launcher PE header is truncated")
    return struct.unpack_from("<II", data, entry)


def read_launcher(path: Path) -> bytes:
    """Read one launcher, refusing links, other names and odd files."""
    if path.name != LAUNCHER_NAME:
        raise SigningRefused(f"refusing {path}: only {LAUNCHER_NAME!r} is signed")
    try:
        info = os.lstat(path)
    except OSError as exc:
        raise SigningRefused(
            f"refusing {path}: cannot read it ({exc.strerror})"
        ) from exc
    if not stat.S_ISREG(info.st_mode):
        raise SigningRefused(f"refusing {path}: not a regular file")
    if info.st_size > MAX_LAUNCHER_BYTES:
        raise SigningRefused(f"refusing {path}: larger than {MAX_LAUNCHER_BYTES} bytes")
    data = path.read_bytes()
    if len(data) != info.st_size:
        raise SigningRefused(f"refusing {path}: it changed while being read")
    return data


def check_tools(settings: Settings) -> None:
    try:
        jar = settings.jsign_jar.read_bytes()
    except OSError as exc:
        raise SigningRefused(
            f"cannot read BEAMO_SIGN_JSIGN_JAR ({exc.strerror})"
        ) from exc
    if hashlib.sha256(jar).hexdigest() != JSIGN_SHA256:
        raise SigningRefused(
            f"BEAMO_SIGN_JSIGN_JAR is not the pinned jsign {JSIGN_VERSION} jar"
        )
    if not settings.ca_file.is_file():
        raise SigningRefused("BEAMO_SIGN_CA_FILE is not a readable file")


def sign_command(settings: Settings, path: Path) -> list[str]:
    """jsign reads the token from the environment, so argv holds no secret."""
    return [
        "java",
        "-jar",
        str(settings.jsign_jar),
        "--storetype",
        "TRUSTEDSIGNING",
        "--keystore",
        settings.endpoint.removeprefix("https://"),
        "--storepass",
        f"env:{TOKEN_ENV}",
        "--alias",
        f"{settings.account}/{settings.profile}",
        "--alg",
        "SHA-256",
        "--tsaurl",
        TIMESTAMP_URL,
        "--tsmode",
        "RFC3161",
        str(path),
    ]


def verify_command(settings: Settings, path: Path) -> list[str]:
    return [
        "osslsigncode",
        "verify",
        "-CAfile",
        str(settings.ca_file),
        "-TSA-CAfile",
        str(settings.ca_file),
        "-in",
        str(path),
    ]


def _scrub(text: str, env: Mapping[str, str]) -> str:
    token = env.get(TOKEN_ENV, "")
    return text.replace(token, "[hidden]") if token else text


def _run(run: Runner, label: str, command: list[str], env: Mapping[str, str]) -> str:
    result = run(
        command,
        env=dict(env),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=600,
        check=False,
    )
    output = _scrub(result.stdout or "", env)
    if result.returncode != 0:
        raise SigningRefused(
            f"{label} failed with exit {result.returncode}:\n{output.strip()}"
        )
    return output


def main(
    argv: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
    run: Runner = subprocess.run,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "launchers", nargs="+", type=Path, help=f"paths named {LAUNCHER_NAME!r}"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="check settings, tools and launchers; print the commands; sign nothing",
    )
    args = parser.parse_args(argv)
    env = os.environ if env is None else env
    try:
        settings = load_settings(env, need_token=not args.dry_run)
        resolved = [path.absolute() for path in args.launchers]
        if len({os.path.normcase(str(path)) for path in resolved}) != len(resolved):
            raise SigningRefused("the same launcher path was given twice")
        before = {}
        for path in resolved:
            data = read_launcher(path)
            if certificate_table(data) != (0, 0):
                raise SigningRefused(f"refusing {path}: it is already signed")
            before[path] = hashlib.sha256(data).hexdigest()
        check_tools(settings)
        if args.dry_run:
            print("DRY RUN: nothing was signed.")
            print(
                f"access token ({TOKEN_ENV}): {'set' if settings.token_set else 'not set'}"
            )
            for path in resolved:
                print(f"would sign {path} (sha256 {before[path]})")
                print("  " + subprocess.list2cmdline(sign_command(settings, path)))
                print("  " + subprocess.list2cmdline(verify_command(settings, path)))
            return 0
        receipts = []
        for path in resolved:
            _run(run, "jsign sign", sign_command(settings, path), env)
            data = read_launcher(path)
            if certificate_table(data) == (0, 0):
                raise SigningRefused(f"{path}: jsign exited 0 but wrote no signature")
            output = _run(
                run, "osslsigncode verify", verify_command(settings, path), env
            )
            if settings.publisher not in output:
                raise SigningRefused(
                    f"{path}: signer is not {settings.publisher!r}:\n{output.strip()}"
                )
            if "timestamp" not in output.lower():
                raise SigningRefused(f"{path}: no timestamp found:\n{output.strip()}")
            receipts.append(
                {
                    "launcher": str(path),
                    "sha256_unsigned": before[path],
                    "sha256_signed": hashlib.sha256(data).hexdigest(),
                    "publisher": settings.publisher,
                    "timestamp_url": TIMESTAMP_URL,
                    "jsign": JSIGN_VERSION,
                }
            )
        print(json.dumps({"signed": receipts}, indent=2, sort_keys=True))
        return 0
    except SigningRefused as exc:
        print(f"sign_windows_launcher: {_scrub(str(exc), env)}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
