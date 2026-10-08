#!/usr/bin/env python3
"""M0 lab step 4: install the project guardrails and the org agent bundle. Any shell.

Run from the root of YOUR repo, with the course repo cloned next to it:

    git clone --branch m00-done-v2 https://github.com/DeccansoftAITeam/sdlc-with-agents ../course-ref
    python ../course-ref/course/m00-setup/bootstrap.py

What it does:
  1. Copies the project scaffold files (guardrails that live in your repo, behind
     CODEOWNERS): scripts/, docs/, AGENTS.md, CLAUDE.md, CODEOWNERS, .gitignore,
     .gitattributes, .claude/settings.json, .github/copilot-instructions.md,
     .vscode/settings.json
  2. Installs the org agent bundle at a pinned version:
       skills       -> npx skills (Claude: .claude/skills, Copilot: .agents/skills)
       org rules, Copilot agents + hooks -> the bundle's install.py
  3. Claude Code subagents + hooks come from the plugin that .claude/settings.json
     enables: accept the prompt the first time you run `claude` in the repo.
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

COURSE_REF = Path(__file__).resolve().parents[2]
BUNDLE = "DeccansoftAITeam/agent-bundle"
DIRS = ["scripts", "docs"]
FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "CODEOWNERS",
    ".gitignore",
    ".gitattributes",
    ".claude/settings.json",
    ".github/copilot-instructions.md",
    ".vscode/settings.json",
]


def run(cmd: list[str], **kw: object) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)  # noqa: S603


def tool(name: str) -> str:
    exe = shutil.which(name)
    if exe is None:
        sys.exit(f"'{name}' not found on PATH. Run doctor.py and install it first.")
    return exe


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle-ref", default="v2.0.0", help="agent-bundle tag to install (default: v2.0.0)")
    args = ap.parse_args()

    target = Path.cwd()
    if not (target / ".git").exists():
        sys.exit("Run this from the root of your own git repo (the folder with .git).")
    if target.resolve() == COURSE_REF:
        sys.exit("You're inside the course repo. cd into YOUR repo first.")

    print(f"1/3  Copying scaffold files from {COURSE_REF}")
    for d in DIRS:
        shutil.copytree(COURSE_REF / d, target / d, dirs_exist_ok=True)
    for f in FILES:
        (target / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(COURSE_REF / f, target / f)

    print(f"\n2/3  Installing skills from {BUNDLE}@{args.bundle_ref}")
    env = {**os.environ, "DISABLE_TELEMETRY": "1"}
    run([tool("npx"), "-y", "skills", "add", f"{BUNDLE}#{args.bundle_ref}", "--skill", "*",
         "-a", "claude-code", "-a", "github-copilot", "--copy", "-y"], env=env)

    print("\n3/3  Installing org rules + Copilot agents and hooks")
    with tempfile.TemporaryDirectory() as tmp:
        run([tool("git"), "clone", "-q", "--depth", "1", "--branch", args.bundle_ref,
             f"https://github.com/{BUNDLE}", tmp])
        run([sys.executable, str(Path(tmp) / "scripts" / "install.py"), str(target)])

    print("\nDone. Next: run `claude` in this folder and accept the 'deccansoft-org' plugin prompt,")
    print("then continue with step 4's checks in the lab.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
