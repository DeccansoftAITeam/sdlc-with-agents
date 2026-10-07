#!/usr/bin/env python3
"""Install or upgrade the pinned org agent bundle (DeccansoftAITeam/agent-bundle).

  1. skills       -> npx skills (Claude: .claude/skills, Copilot: .agents/skills) + skills-lock.json
  2. org rules, Copilot agents + hooks -> the bundle's install.py (+ .agents/bundle.lock)
  3. Claude subagents + hooks -> plugin, enabled via .claude/settings.json (prompted on first run)

Usage: python scripts/install_agent_bundle.py <ref>      e.g. v2.1.0
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "DeccansoftAITeam/agent-bundle"


def run(cmd: list[str], **kw: object) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True, **kw)  # noqa: S603


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    ref = sys.argv[1]
    env = {**os.environ, "DISABLE_TELEMETRY": "1"}
    npx = shutil.which("npx") or "npx"
    run([npx, "-y", "skills", "add", f"{REPO}#{ref}", "--skill", "*",
         "-a", "claude-code", "-a", "github-copilot", "--copy", "-y"], env=env)
    with tempfile.TemporaryDirectory() as tmp:
        run(["git", "clone", "-q", "--depth", "1", "--branch", ref, f"https://github.com/{REPO}", tmp])
        run([sys.executable, str(Path(tmp) / "scripts" / "install.py"), "."])
    print(f"agent bundle {ref} installed. Open the repo in Claude Code and accept the "
          "'deccansoft-org' plugin prompt to get Claude subagents and hooks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
