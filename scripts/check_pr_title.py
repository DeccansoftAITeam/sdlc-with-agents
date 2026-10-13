#!/usr/bin/env python3
"""Fail unless the PR title is a Conventional Commit header.

PRs are squash-merged, so the PR title BECOMES the commit on main that release-please
reads (M9). The local commit-msg hook can be skipped; this check can't.
Usage: check_pr_title.py "<title>"
"""
import re
import sys

TYPES = "build|chore|ci|docs|feat|fix|perf|refactor|revert|style|test"
PATTERN = re.compile(rf"^({TYPES})(\([a-z0-9,./-]+\))?!?: \S.{{0,99}}$")

title = sys.argv[1] if len(sys.argv) > 1 else ""
if PATTERN.match(title):
    sys.exit(0)
print(f"PR title is not a Conventional Commit header: {title!r}")
print("Expected e.g. 'feat(td007): escalate SLA breaches' (types: " + TYPES.replace("|", ", ") + ")")
sys.exit(1)
