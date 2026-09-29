#!/usr/bin/env python3
"""Verify that a release tag exactly matches RAISE's package version."""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

DEFAULT_VERSION_FILE = Path(__file__).resolve().parents[1] / "src/raise_xai/__about__.py"


def read_package_version(version_file: Path) -> str:
    """Read a single literal ``__version__`` assignment without executing source code."""
    tree = ast.parse(version_file.read_text(encoding="utf-8"), filename=str(version_file))
    assignments: list[ast.expr] = []

    for node in tree.body:
        if isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "__version__"
                for target in node.targets
            ):
                assignments.append(node.value)
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "__version__"
            and node.value is not None
        ):
            assignments.append(node.value)

    if len(assignments) != 1:
        raise ValueError(
            f"expected exactly one top-level __version__ assignment in {version_file}, "
            f"found {len(assignments)}"
        )

    try:
        version = ast.literal_eval(assignments[0])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"__version__ in {version_file} must be a string literal") from exc

    if not isinstance(version, str) or not version:
        raise ValueError(f"__version__ in {version_file} must be a non-empty string literal")
    return version


def verify_release_version(tag: str, version_file: Path = DEFAULT_VERSION_FILE) -> str:
    """Return the package version when ``v<version>`` and ``__version__`` match exactly."""
    if not tag.startswith("v") or len(tag) == 1:
        raise ValueError(f"release tag {tag!r} must use the form 'v<package-version>'")

    tag_version = tag[1:]
    package_version = read_package_version(version_file)
    if tag_version != package_version:
        raise ValueError(
            f"release tag {tag!r} does not match package version {package_version!r} "
            f"from {version_file}"
        )
    return package_version


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail unless a GitHub release tag exactly matches RAISE's package version."
    )
    parser.add_argument("tag", help="Release tag, for example v0.1.2")
    parser.add_argument(
        "--version-file",
        type=Path,
        default=DEFAULT_VERSION_FILE,
        help="Version source file (defaults to src/raise_xai/__about__.py)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        version = verify_release_version(args.tag, args.version_file)
    except (OSError, SyntaxError, ValueError) as exc:
        print(f"release-version check failed: {exc}", file=sys.stderr)
        return 1

    print(f"release tag {args.tag} matches package version {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
