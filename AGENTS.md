# TicketDesk — Agent Instructions

> Bootstrap version (M0). The full project layer (L2) is written in M3.

1. Follow the org rules in `.agents/org/org-rules.md`. They override everything else, this file included.
2. Use only the org skills and subagents from the pinned org bundle (`DeccansoftAITeam/agent-bundle`, see `.agents/bundle.lock` and `skills-lock.json`):
   `grill`, `spec-draft`, `acceptance-tdd`, `migration-writer`, `test-generator`, `code-reviewer`, `security-reviewer`.
3. Read `docs/constitution.md` (once it exists) before any task.
4. Every tool call is audit-logged to `.agents/audit/audit.jsonl`. Never disable the hook.
