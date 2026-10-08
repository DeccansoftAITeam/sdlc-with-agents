#!/usr/bin/env python3
"""Check the course toolbox. Works in any shell (Git Bash, PowerShell, cmd, macOS, Linux).

Usage:  python ../course-ref/course/m00-setup/doctor.py
"""

import os
import shutil
import subprocess
import sys

TOOLS = ["git", "gh", "python", "uv", "node", "pnpm", "docker", "az", "claude", "code"]


def version(tool: str) -> str:
    exe = shutil.which(tool)
    if exe is None:
        return "MISSING"
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)  # noqa: S603
    except (OSError, subprocess.TimeoutExpired):
        return "found, but `--version` failed"
    lines = [ln for ln in (out.stdout or out.stderr).splitlines() if ln.strip() and "WARNING" not in ln]
    return lines[0].strip() if lines else "found"


def shell_hint() -> str | None:
    if os.name != "nt":
        return None
    if os.environ.get("MSYSTEM"):  # set by Git Bash
        return None
    return (
        "You're on Windows outside Git Bash. The labs use bash syntax; open 'Git Bash' "
        "(installed with Git) and run the lab commands there."
    )


def branch_hint() -> str | None:
    git = shutil.which("git")
    if git is None:
        return None
    out = subprocess.run([git, "config", "--global", "init.defaultBranch"], capture_output=True, text=True)  # noqa: S603
    if out.stdout.strip() == "main":
        return None
    return (
        "git's default branch is not 'main'. Run: git config --global init.defaultBranch main "
        "(or use `git branch -M main` before your first push)."
    )


def main() -> int:
    missing = 0
    for tool in TOOLS:
        v = version(tool)
        missing += v == "MISSING"
        print(f"{tool:<8} {v}")
    for hint in (shell_hint(), branch_hint()):
        if hint:
            print(f"\nNOTE: {hint}")
    print(f"\n{'All tools found.' if not missing else f'{missing} tool(s) MISSING: install them first.'}")
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
