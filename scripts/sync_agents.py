#!/usr/bin/env python3
"""Package the canonical org agent bundle (.agents/) for each harness.

One source, two packagings (03-AGENT-OPERATING-MODEL.md: "keep behaviour
identical; only the packaging differs"):

  .agents/skills/<name>/SKILL.md  -> .claude/skills/<name>/  and .github/skills/<name>/
  .agents/agents/<name>.md        -> .claude/agents/<name>.md and .github/agents/<name>.agent.md

Generated copies carry a header and must not be edited by hand. Conformance (M8)
fails when a copy drifts from its source. Run: python scripts/sync_agents.py [--check]
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".agents"
NOTICE = "<!-- GENERATED from .agents/ by scripts/sync_agents.py. Do not edit. -->\n"

# Claude tool names -> Copilot custom-agent tool sets (read-only reviewers)
COPILOT_TOOLS = {"Read": "read", "Grep": "search", "Glob": "search", "Bash": "execute"}


def with_notice(text: str) -> str:
    # keep YAML frontmatter first; notice goes right after it
    m = re.match(r"(---\n.*?\n---\n)(.*)", text, re.S)
    return m.group(1) + NOTICE + m.group(2) if m else NOTICE + text


def copilot_agent(text: str) -> str:
    def tools(m: re.Match) -> str:
        names = sorted({COPILOT_TOOLS.get(t.strip(), t.strip().lower()) for t in m.group(1).split(",")})
        return "tools: [" + ", ".join(f"'{n}'" for n in names) + "]"
    return with_notice(re.sub(r"^tools: (.+)$", tools, text, count=1, flags=re.M))


def outputs() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for skill in sorted((SRC / "skills").iterdir()):
        for f in skill.rglob("*"):
            if f.is_file():
                rel = f.relative_to(SRC / "skills")
                body = f.read_text(encoding="utf-8")
                body = with_notice(body) if f.name == "SKILL.md" else body
                out[ROOT / ".claude/skills" / rel] = body
                out[ROOT / ".github/skills" / rel] = body
    for agent in sorted((SRC / "agents").glob("*.md")):
        text = agent.read_text(encoding="utf-8")
        out[ROOT / ".claude/agents" / agent.name] = with_notice(text)
        out[ROOT / ".github/agents" / f"{agent.stem}.agent.md"] = copilot_agent(text)
    return out


def main() -> int:
    check = "--check" in sys.argv
    wanted = outputs()
    drift = [p for p, body in wanted.items()
             if not p.exists() or p.read_text(encoding="utf-8") != body]
    if check:
        for p in drift:
            print(f"drift: {p.relative_to(ROOT)}")
        return 1 if drift else 0
    for d in (".claude/skills", ".github/skills", ".claude/agents", ".github/agents"):
        shutil.rmtree(ROOT / d, ignore_errors=True)
    for p, body in wanted.items():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8", newline="\n")
    print(f"synced {len(wanted)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
