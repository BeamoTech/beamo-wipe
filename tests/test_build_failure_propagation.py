"""Build staging failures must stop before a fake gate or ISO export."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _tool(tools, name, body):
    path = tools / name
    path.write_text(f"#!{sys.executable}\n" + body, encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.parametrize(
    "producer_code,extractor_code,gate_code", [(0, 0, 0), (23, 0, 0), (0, 7, 0), (0, 0, 9)]
)
def test_private_source_copy_requires_both_tar_processes(
    tmp_path, producer_code, extractor_code, gate_code
):
    tools = tmp_path / "tools"
    tools.mkdir()
    mounted = tmp_path / "mounted"
    (mounted / "scripts").mkdir(parents=True)
    (mounted / "scripts/ci-hosted.sh").write_text(
        'printf gate > "$GATE_SENTINEL"\nexit "$GATE_CODE"\n'
    )
    archive = tmp_path / "source.tar"
    with tarfile.open(archive, "w") as output:
        output.add(mounted / "scripts", arcname="scripts")
    private = tmp_path / "private"
    private.mkdir()
    marker = tmp_path / "gate-ran"
    _tool(tools, "mktemp", "import os\nprint(os.environ['PRIVATE_SOURCE'])\n")
    _tool(
        tools,
        "tar",
        "import os, pathlib, sys\n"
        "if '-cf' in sys.argv:\n"
        " sys.stdout.buffer.write(pathlib.Path(os.environ['SOURCE_ARCHIVE']).read_bytes())\n"
        " raise SystemExit(int(os.environ['PRODUCER_CODE']))\n"
        "if int(os.environ['EXTRACTOR_CODE']):\n"
        " sys.stdin.buffer.read()\n"
        " raise SystemExit(int(os.environ['EXTRACTOR_CODE']))\n"
        "os.execv('/usr/bin/tar', ['tar', *sys.argv[1:]])\n",
    )
    source = (ROOT / "scripts/ci-blacksmith.sh").read_text()
    inner = source.split('"$IMAGE" bash -ceu \'\n', 1)[1].split("\n    ' --", 1)[0]
    result = subprocess.run(
        ["bash", "-ceu", inner, "--", str(mounted), "1", "lint"],
        env=dict(
            os.environ,
            PATH=str(tools) + os.pathsep + os.environ["PATH"],
            PRIVATE_SOURCE=str(private),
            SOURCE_ARCHIVE=str(archive),
            GATE_SENTINEL=str(marker),
            PRODUCER_CODE=str(producer_code),
            EXTRACTOR_CODE=str(extractor_code),
            GATE_CODE=str(gate_code),
        ),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == (extractor_code or producer_code or gate_code), result.stderr
    assert marker.exists() is not bool(producer_code or extractor_code)


@pytest.mark.parametrize(
    "names,find_code,expected",
    [
        (("one.iso",), 0, 0),
        (("one.iso",), 7, 7),
        ((), 7, 7),
        ((), 0, 1),
        (("one.iso", "two.iso"), 0, 1),
        (("one with spaces\nand newline.iso",), 0, 0),
    ],
)
def test_iso_export_requires_complete_successful_enumeration(
    tmp_path, names, find_code, expected
):
    tools = tmp_path / "tools"
    tools.mkdir()
    paths = []
    for name in names:
        path = tmp_path / name
        path.write_bytes(b"owned ISO fixture bytes")
        paths.append(str(path))
    output = tmp_path / "output"
    output.mkdir()
    _tool(
        tools,
        "find",
        "import json, os, sys\n"
        "assert sys.argv[1] == '/build/packaging/live'\n"
        "separator = b'\\0' if '-print0' in sys.argv else b'\\n'\n"
        "for path in json.loads(os.environ['ISO_PATHS']):\n"
        " sys.stdout.buffer.write(os.fsencode(path) + separator)\n"
        "raise SystemExit(int(os.environ['FIND_CODE']))\n",
    )
    source = (ROOT / "packaging/live/inside-docker.sh").read_text()
    tail = source.split("\nlb build\n", 1)[1]
    assert tail.count('"/out/${ISO_NAME}"') == 2
    tail = tail.replace('"/out/${ISO_NAME}"', '"${FIXTURE_OUTPUT}/${ISO_NAME}"')
    result = subprocess.run(
        ["bash", "-euo", "pipefail", "-c", tail],
        env=dict(
            os.environ,
            PATH=str(tools) + os.pathsep + os.environ["PATH"],
            TMPDIR=str(tmp_path),
            ISO_NAME="beamo-wipe-0.2.14-amd64.iso",
            FIXTURE_OUTPUT=str(output),
            ISO_PATHS=json.dumps(paths),
            FIND_CODE=str(find_code),
        ),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == expected, result.stderr
    exported = output / "beamo-wipe-0.2.14-amd64.iso"
    if expected == 0:
        assert exported.read_bytes() == b"owned ISO fixture bytes"
    else:
        assert not exported.exists()
