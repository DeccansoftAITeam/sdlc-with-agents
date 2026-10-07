#!/usr/bin/env python3
"""Fail if any tracked source file exceeds --max lines (AD-09)."""
import argparse
import subprocess
import sys

EXT = (".py", ".ts", ".tsx", ".js", ".jsx")
ap = argparse.ArgumentParser()
ap.add_argument("--max", type=int, default=1000)
args = ap.parse_args()
files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
bad = [(f, n) for f in files if f.endswith(EXT)
       for n in [sum(1 for _ in open(f, encoding="utf-8", errors="ignore"))] if n > args.max]
for f, n in bad:
    print(f"{f}: {n} lines (max {args.max})")
sys.exit(1 if bad else 0)
