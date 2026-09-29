"""Tests for the release tag/package version consistency guard."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts/check_release_version.py"


def run_guard(tmp_path: Path, tag: str, source: str) -> subprocess.CompletedProcess[str]:
    version_file = tmp_path / "__about__.py"
    version_file.write_text(source, encoding="utf-8")
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            tag,
            "--version-file",
            str(version_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )


def test_matching_release_tag_passes(tmp_path):
    result = run_guard(tmp_path, "v0.1.2", '__version__ = "0.1.2"\n')

    assert result.returncode == 0
    assert "release tag v0.1.2 matches package version 0.1.2" in result.stdout


def test_mismatched_release_tag_fails(tmp_path):
    result = run_guard(tmp_path, "v0.1.2", '__version__ = "0.1.1"\n')

    assert result.returncode == 1
    assert "does not match package version '0.1.1'" in result.stderr


def test_release_tag_requires_v_prefix(tmp_path):
    result = run_guard(tmp_path, "0.1.2", '__version__ = "0.1.2"\n')

    assert result.returncode == 1
    assert "must use the form 'v<package-version>'" in result.stderr


def test_version_source_must_have_one_literal_assignment(tmp_path):
    result = run_guard(
        tmp_path,
        "v0.1.2",
        '__version__ = "0.1.2"\n__version__ = "0.1.3"\n',
    )

    assert result.returncode == 1
    assert "expected exactly one top-level __version__ assignment" in result.stderr
