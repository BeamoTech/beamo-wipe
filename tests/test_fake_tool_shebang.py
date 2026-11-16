# SPDX-License-Identifier: GPL-3.0-or-later
"""A fake tool's shebang must be one Linux can start, or the test fails."""
import pytest

from fake_tool_shebang import SHEBANG_MAX_BYTES, python_shebang


@pytest.mark.parametrize("interpreter", [
    "/usr/bin/python3",
    "/tmp/beamo-pass16-python/bin/python3",
    "/" + "p" * (SHEBANG_MAX_BYTES - 3),  # "#!" + path is exactly the limit
])
def test_valid_interpreter_gives_a_plain_shebang(interpreter):
    assert python_shebang(interpreter) == f"#!{interpreter}\n"


@pytest.mark.parametrize("interpreter", [
    "/root/dev/Beamo Wipe/.venv-linux/bin/python3",  # the pass 16 path
    "/opt/py\tthon/bin/python3",
    "/opt/python3\n",
    "python3",
    r"C:\Python313\python.exe",
    "/" + "p" * (SHEBANG_MAX_BYTES - 2),  # one byte over the limit
])
def test_unusable_interpreter_fails_instead_of_writing_a_fake(interpreter):
    with pytest.raises(pytest.fail.Exception, match="refusing to write a fake tool"):
        python_shebang(interpreter)
