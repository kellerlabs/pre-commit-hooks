"""Pre-commit hook: flatten OpenSCAD files and validate they are committed."""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path


def _read_flatten_dirs():
    """Read flatten destination dirs from scadm.json.

    Returns:
        List of destination directory paths from the flatten config,
        or empty list if scadm.json is missing or has no flatten key.
    """
    scadm_json = Path("scadm.json")
    if not scadm_json.exists():
        print("WARNING: scadm.json not found, skipping flatten dir validation")
        return []

    with open(scadm_json, encoding="utf-8") as f:
        config = json.load(f)

    flatten_entries = config.get("flatten", [])
    if not flatten_entries:
        print("WARNING: No 'flatten' entries in scadm.json")
        return []

    return [entry["dest"] for entry in flatten_entries if "dest" in entry]


def _git_modified(paths):
    """Get modified tracked files (not staged) under the given paths.

    Args:
        paths: List of directory paths to check.

    Returns:
        List of modified file paths.

    Raises:
        SystemExit: If git diff fails.
    """
    if not paths:
        return []
    result = subprocess.run(
        ["git", "diff", "--name-only", "--"] + paths,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"ERROR: git diff failed: {result.stderr.strip()}")
        sys.exit(1)
    return [line for line in result.stdout.strip().split("\n") if line]


def _git_untracked(paths):
    """Get untracked files under the given paths.

    Args:
        paths: List of directory paths to check.

    Returns:
        List of untracked file paths.

    Raises:
        SystemExit: If git ls-files fails.
    """
    if not paths:
        return []
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard", "--"] + paths,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print(f"ERROR: git ls-files failed: {result.stderr.strip()}")
        sys.exit(1)
    return [line for line in result.stdout.strip().split("\n") if line]


def main():
    """Entry point for the flatten-validate pre-commit hook."""
    parser = argparse.ArgumentParser(description="Validate flattened OpenSCAD exports are committed.")
    parser.add_argument(
        "--flatten-dir",
        nargs="+",
        default=None,
        help="Override flatten destination dirs (default: read from scadm.json).",
    )
    args = parser.parse_args()

    flatten_dirs = args.flatten_dir if args.flatten_dir else _read_flatten_dirs()

    # Run scadm flatten
    result = subprocess.run(["scadm", "flatten", "--all"], check=False)
    if result.returncode != 0:
        print("ERROR: scadm flatten --all failed")
        return 1

    if not flatten_dirs:
        print("OK: No flatten directories to validate")
        return 0

    modified = _git_modified(flatten_dirs)
    untracked = _git_untracked(flatten_dirs)

    if modified or untracked:
        print("")
        print("ERROR: Flattened files have uncommitted/unstaged changes")
        print("")
        if modified:
            print("Modified files (not staged):")
            for f in modified:
                print(f"  {f}")
        if untracked:
            print("Untracked files:")
            for f in untracked:
                print(f"  {f}")
        dirs = " ".join(shlex.quote(d) for d in flatten_dirs)
        print("")
        print("Run the following to stage them:")
        print(f"  git add {dirs}")
        return 1

    print("OK: All flattened files are committed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
