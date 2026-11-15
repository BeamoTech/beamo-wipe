# SPDX-License-Identifier: GPL-3.0-or-later
"""Shebang for Python fake tools that must never fall back to the real tool.

A test puts a fake (``losetup``, ``sudo``, ``docker``, ``curl``, ``xorriso``
...) first on PATH and lets the code under test find it. If the kernel cannot
start the fake, the exec search silently moves on to the next PATH entry, so
the real tool runs instead. That happened in bug audit pass 16
(docs/evidence/bug-audit-20261017-pass16/incident-review-loop-probes-20261115.md):
a space in the venv path made ``#!{sys.executable}`` invalid, and the real
``losetup`` attached loop devices as root.

Refuse to write such a fake rather than risk a real tool running.
"""
import sys

import pytest

# Linux splits a shebang at the first blank, and kernels before 5.1 read only
# the first 127 bytes of it (BINPRM_BUF_SIZE 128). Stay inside both limits.
SHEBANG_MAX_BYTES = 127


def python_shebang(executable: str | None = None) -> str:
    """Return ``#!<python>\\n`` for a fake tool, or fail the test.

    Fails (never skips) so an unusable interpreter path shows up as a red
    test instead of a run that silently reached a real tool.
    """
    interpreter = sys.executable if executable is None else executable
    line = f"#!{interpreter}"
    if (not interpreter.startswith("/")
            or any(char.isspace() for char in interpreter)
            or len(line.encode()) > SHEBANG_MAX_BYTES):
        pytest.fail(
            f"refusing to write a fake tool: interpreter {interpreter!r} is not a "
            "valid Linux shebang target (relative, contains a blank, or longer "
            f"than {SHEBANG_MAX_BYTES} bytes); the fake could not start and the "
            "PATH search would reach the real tool",
            pytrace=False,
        )
    return line + "\n"
