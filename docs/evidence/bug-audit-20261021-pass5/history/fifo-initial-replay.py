"""Replay the exact regression module with only the archived safety source."""
from pathlib import Path
import importlib.util
import sys

import beamo_wipe
import pytest

folder = Path(__file__).resolve().parent
name = "beamo_wipe.safety"
spec = importlib.util.spec_from_file_location(name, folder / "safety-original.py")
module = importlib.util.module_from_spec(spec)
sys.modules[name] = module
spec.loader.exec_module(module)
beamo_wipe.safety = module
raise SystemExit(pytest.main([
    "-o", "addopts=", "-q", "tests/test_log_fifo_open_pass5_20261021.py",
    "--junitxml=" + str(folder / "expanded-before.xml"),
]))
