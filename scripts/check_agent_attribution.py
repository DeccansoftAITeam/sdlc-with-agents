#!/usr/bin/env python3
"""Every commit on an agent/* branch must carry the agent attribution trailers (org rules §8).

Usage: check_agent_attribution.py <base-ref> <head-ref> <branch-name>
Branches not named agent/* pass: human-authored work needs no agent trailers.
"""
import subprocess
import sys

REQUIRED = ("Agent-Model", "Agent-Mode", "Agent-Session", "Agent-Operator")
MODES = {"M1", "M2", "M3"}

base, head, branch = sys.argv[1:4]
if not branch.startswith("agent/"):
    print(f"{branch}: not an agent branch, nothing to check")
    sys.exit(0)

log = subprocess.run(
    ["git", "log", "--no-merges", "--format=%H%x00%(trailers:only,unfold)%x01", f"{base}..{head}"],
    capture_output=True, text=True, check=True,
).stdout
failed = False
for entry in filter(str.strip, log.split("\x01")):
    sha, trailers = entry.strip().split("\x00", 1)
    found = dict(line.split(": ", 1) for line in trailers.splitlines() if ": " in line)
    missing = [t for t in REQUIRED if not found.get(t, "").strip()]
    if found.get("Agent-Mode") and found["Agent-Mode"].strip() not in MODES:
        missing.append("Agent-Mode (must be M1, M2 or M3)")
    if missing:
        failed = True
        print(f"{sha[:10]}: missing {', '.join(missing)}")
sys.exit(1 if failed else 0)
