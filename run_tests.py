#!/usr/bin/env python3
"""Runs every test: happy-path programs must compile, error programs must be rejected."""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COMPILER = os.path.join(HERE, "compiler.py")


def run(path):
    result = subprocess.run(
        [sys.executable, COMPILER, path, os.devnull],
        capture_output=True, text=True
    )
    return result.returncode == 0


def main():
    passed = failed = 0

    for path in sorted(glob.glob(os.path.join(HERE, "tests", "happy", "*.txt"))):
        name = os.path.basename(path)
        if run(path):
            print(f"[pass] happy/{name}")
            passed += 1
        else:
            print(f"[FAIL] happy/{name} — should have compiled")
            failed += 1

    for path in sorted(glob.glob(os.path.join(HERE, "tests", "errors", "*.txt"))):
        name = os.path.basename(path)
        if not run(path):
            print(f"[pass] errors/{name}")
            passed += 1
        else:
            print(f"[FAIL] errors/{name} — should have been rejected")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
