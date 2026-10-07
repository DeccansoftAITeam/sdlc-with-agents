#!/usr/bin/env python3
"""Agent audit hook. Installed into each repo as .agents/hooks/audit_log.py.

Wired as a PreToolUse and PostToolUse hook for Claude Code (.claude/settings.json)
and as preToolUse/postToolUse for GitHub Copilot (.github/hooks/audit.json).
Usage: audit_log.py <pre|post> [harness]. Both harnesses send JSON on stdin; the
field names differ slightly (snake_case vs camelCase), so both are read.
Reads the hook event JSON on stdin and appends one JSON line per event to the
audit log. It never blocks a tool call; blocking is the permission lists' job.

Log location: $AGENT_AUDIT_LOG, else .agents/audit/audit.jsonl (git-ignored).
In CI the file is uploaded as an artifact and shipped to the central log store;
retention is one year (03-AGENT-OPERATING-MODEL.md).

Recorded fields: timestamp, session, event, tool, a truncated summary of the
tool input, outcome, git branch, human operator, agent mode.
Secrets: values of keys that look sensitive are redacted before writing.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MAX_FIELD = 500
SENSITIVE = re.compile(r"(secret|token|password|passwd|api[_-]?key|authorization|cookie)", re.I)


def redact(value):
    if isinstance(value, dict):
        return {k: ("[REDACTED]" if SENSITIVE.search(k) else redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return value if len(value) <= MAX_FIELD else value[:MAX_FIELD] + "…[truncated]"
    return value


def git_branch() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        event = {}

    def pick(*keys):
        for k in keys:
            if event.get(k) is not None:
                return event[k]
        return None

    phase = sys.argv[1] if len(sys.argv) > 1 else None
    harness = sys.argv[2] if len(sys.argv) > 2 else "claude"
    is_post = phase == "post" or pick("hook_event_name", "hookEventName") == "PostToolUse"

    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "harness": harness,
        "session": pick("session_id", "sessionId"),
        "event": "post" if is_post else "pre",
        "tool": pick("tool_name", "toolName"),
        "input": redact(pick("tool_input", "toolArgs", "toolInput")),
        "outcome": redact(pick("tool_response", "toolResult")) if is_post else None,
        "branch": git_branch(),
        "operator": os.environ.get("AGENT_OPERATOR") or os.environ.get("USER") or os.environ.get("USERNAME"),
        "mode": os.environ.get("AGENT_MODE", "M1"),
        "cwd": pick("cwd"),
    }

    path = Path(os.environ.get("AGENT_AUDIT_LOG", ".agents/audit/audit.jsonl"))
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as exc:  # never break the agent because logging failed
        print(f"audit_log: could not write audit record: {exc}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
