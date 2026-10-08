# SDLC in the Agents Life Cycle

Build **TicketDesk**, a support-ticket app with AI triage, from an empty folder. Coding agents (Claude Code and GitHub Copilot) write most of the code. You plan, approve, review and ship, following the Deccansoft SDLC v2 standard.

| | |
|---|---|
| Stack | FastAPI · PostgreSQL + pgvector · Next.js |
| AI | Azure OpenAI (Foundry) behind the Azure APIM AI gateway |
| Deploy | Azure Container Apps |
| Agents | Claude Code and GitHub Copilot, sharing one `AGENTS.md` |

## How the course works

Each module is one SDLC phase. Every module folder in `course/` has:

- `notes.md`: the concepts, kept short. Read it in 15 minutes.
- `lab.md`: what you do, including the exact agent prompts.
- a git tag `mNN-done`: the finished state. If you fall behind, run `git checkout mNN-done`.

**Shell:** labs use bash. On Windows use **Git Bash** (comes with Git).

Start at [`course/m00-setup`](course/m00-setup/notes.md). The full module plan is in [`course/COURSE-OUTLINE.md`](course/COURSE-OUTLINE.md).
