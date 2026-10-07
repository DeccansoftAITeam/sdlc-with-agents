#!/usr/bin/env python3
"""Scope guard: block agent file edits outside the active task's "Files in scope".

PreToolUse hook for Claude Code (plugin hooks/hooks.json) and GitHub Copilot
(.github/hooks/scope-guard.json). Turns the tasks.md rule "modify only the
task's Files in scope" from an instruction into a gate (standard principle 1).

Active task:  .agents/progress/ACTIVE holds a task id (e.g. T-007-02).
Scope:        .agents/progress/<task-id>.md has a "## Files in scope" section;
              each list item holds one glob in backticks, e.g. - `backend/app/sla/**`.
              Globs support *, ** and {a,b}. .agents/progress/** is always allowed.
No ACTIVE file -> no task -> M1 pair work -> allow everything.

Usage: scope_guard.py [claude|copilot]
  claude:  exit 2 + reason on stderr blocks the call.
  copilot: prints {"permissionDecision":"deny",...} to block.
Never blocks non-edit tools. Fails open (allows) on internal errors, after
logging to stderr, so a broken guard can't brick a session; the CI scope
check is the backstop.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

EDIT_TOOLS = {"edit", "write", "multiedit", "notebookedit", "create", "str_replace_editor", "apply_patch"}
PATH_KEYS = ("file_path", "path", "filePath", "notebook_path")


def expand_braces(pattern: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", pattern)
    if not m:
        return [pattern]
    head, tail = pattern[: m.start()], pattern[m.end():]
    return [p for alt in m.group(1).split(",") for p in expand_braces(head + alt + tail)]


def glob_to_regex(glob: str) -> re.Pattern[str]:
    out, i = [], 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?"); i += 3
        elif glob.startswith("**", i):
            out.append(".*"); i += 2
        elif glob[i] == "*":
            out.append("[^/]*"); i += 1
        elif glob[i] == "?":
            out.append("[^/]"); i += 1
        else:
            out.append(re.escape(glob[i])); i += 1
    return re.compile("^" + "".join(out) + "$")


def scope_globs(progress: Path) -> list[str]:
    text = progress.read_text(encoding="utf-8")
    m = re.search(r"^##\s*Files in scope\s*$(.*?)(?=^##\s|\Z)", text, re.S | re.M | re.I)
    if not m:
        return []
    return [g for line in m.group(1).splitlines() for g in re.findall(r"`([^`]+)`", line)]


def in_scope(rel: str, globs: list[str]) -> bool:
    if rel.startswith(".agents/progress/"):
        return True
    return any(glob_to_regex(p).match(rel) for g in globs for p in expand_braces(g))


def target_path(event: dict) -> str | None:
    args = event.get("tool_input") or event.get("toolArgs") or event.get("toolInput") or {}
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            return None
    for k in PATH_KEYS:
        if isinstance(args, dict) and args.get(k):
            return str(args[k])
    return None


def decide(event: dict, root: Path) -> str | None:
    """Return a denial reason, or None to allow."""
    tool = str(event.get("tool_name") or event.get("toolName") or "").lower()
    if tool not in EDIT_TOOLS:
        return None
    active = root / ".agents/progress/ACTIVE"
    if not active.exists():
        return None
    task = active.read_text(encoding="utf-8").strip()
    progress = root / f".agents/progress/{task}.md"
    if not progress.exists():
        return f"Active task {task} has no .agents/progress/{task}.md; cannot verify scope."
    globs = scope_globs(progress)
    if not globs:
        return f".agents/progress/{task}.md has no '## Files in scope' section."
    path = target_path(event)
    if path is None:
        return None
    p = Path(path)
    p = p if p.is_absolute() else root / p
    try:
        rel = p.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return f"{path} is outside the repository."
    if in_scope(rel, globs):
        return None
    return (f"{rel} is outside the Files in scope of task {task}. "
            "Stop and ask the human to widen scope in tasks.md (org rules §4).")


def main() -> int:
    harness = sys.argv[1] if len(sys.argv) > 1 else "claude"
    try:
        event = json.load(sys.stdin)
        root = Path(event.get("cwd") or os.getcwd())
        reason = decide(event, root)
    except Exception as exc:  # fail open; CI scope check is the backstop
        print(f"scope_guard: internal error, allowing: {exc}", file=sys.stderr)
        return 0
    if reason is None:
        return 0
    if harness == "copilot":
        print(json.dumps({"permissionDecision": "deny", "permissionDecisionReason": reason}))
        return 0
    print(reason, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
