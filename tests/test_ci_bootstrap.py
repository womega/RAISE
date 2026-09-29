"""Exercise the public CI entry point without installing packages in the test runner."""

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("make") is None, reason="GNU make is not installed")
@pytest.mark.parametrize("install_fails", [False, True])
def test_ci_bootstraps_before_checks_even_in_parallel(tmp_path, install_fails):
    shutil.copyfile(Path(__file__).parents[1] / "Makefile", tmp_path / "Makefile")
    recorder = tmp_path / "record_python.py"
    recorder.write_text(
        "import json, os, sys\n"
        "with open('calls.jsonl', 'a') as stream:\n"
        "    stream.write(json.dumps(sys.argv[1:]) + '\\n')\n"
        "if os.environ['FAIL_INSTALL'] == '1' and '-e' in sys.argv:\n"
        "    sys.exit(1)\n"
    )
    result = subprocess.run(
        ["make", "-j4", "ci", f"PYTHON={shlex.join([sys.executable, str(recorder)])}"],
        cwd=tmp_path,
        env={**os.environ, "FAIL_INSTALL": str(int(install_fails))},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    calls = [json.loads(line) for line in (tmp_path / "calls.jsonl").read_text().splitlines()]
    assert calls[:2] == [
        ["-m", "pip", "install", "--upgrade", "pip"],
        ["-m", "pip", "install", "-e", ".[dev]"],
    ]
    if install_fails:
        assert result.returncode != 0
        assert len(calls) == 2
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert sorted(calls[2:-1]) == sorted(
            [
                ["-m", "ruff", "check", "."],
                ["-m", "ruff", "format", "--check", "."],
                ["-m", "pytest"],
            ]
        )
        assert calls[-1] == ["-m", "build"]
