# M0 Lab — Toolbox and Empty Repo

**Time:** about 1 h · **Ends at tag:** `m00-done`

## 1. Install the toolbox

| Tool | Version | Why |
|---|---|---|
| git | 2.40+ | — |
| GitHub CLI `gh` | 2.50+ | PRs, repo settings |
| Python | 3.12+ | Backend |
| uv | 0.6+ | Python deps and venvs |
| Node.js | 22+ | Frontend |
| pnpm | 9+ | Frontend deps |
| Docker | 24+ | Postgres locally, images |
| Azure CLI `az` | 2.60+ | Deploy (from M3) |
| Claude Code | latest | Builder agent |
| VS Code + GitHub Copilot (Chat, agent mode) | latest | Builder agent |

Then check everything at once:

```sh
# macOS / Linux / Git Bash
./scripts/doctor.sh
# Windows PowerShell
./scripts/doctor.ps1
```

Fix every `MISSING` line before you continue.

## 2. Sign in

```sh
gh auth login
az login
claude          # follow the login prompt, then /exit
```

In VS Code, sign in to GitHub Copilot and check that **Agent** mode appears in the Chat view.

## 3. Create your repo

```sh
gh repo create <you>/sdlc-with-agents --private --clone
cd sdlc-with-agents
```

## 4. Install the org agent bundle (15 min)

> 🎩 **Platform Owner hat.** In a real company this bundle is synced from a central standards repo. Here you copy it from the course repo at tag `m00-done`.

```sh
git clone --branch m00-done https://github.com/DeccansoftAITeam/sdlc-with-agents ../course-ref
cp -r ../course-ref/.agents ../course-ref/scripts ../course-ref/docs .
cp ../course-ref/{AGENTS.md,CLAUDE.md,CODEOWNERS,.gitignore,.gitattributes} .
mkdir -p .claude .github/hooks .vscode
cp ../course-ref/.claude/settings.json .claude/
cp ../course-ref/.github/hooks/audit.json .github/hooks/
cp ../course-ref/.github/copilot-instructions.md .github/
cp ../course-ref/.vscode/settings.json .vscode/
python scripts/sync_agents.py          # packages skills + agents for both harnesses
python scripts/sync_agents.py --check  # must print nothing and exit 0
```

What you just installed:

| Layer | File(s) | Claude Code | Copilot |
|---|---|---|---|
| L1 org rules | `.agents/org/org-rules.md` | imported by `CLAUDE.md` | via `AGENTS.md` + `copilot-instructions.md` |
| L4 skills | `.agents/skills/*` | `.claude/skills/` | `.github/skills/` |
| L4 subagents | `.agents/agents/*` | `.claude/agents/` | `.github/agents/*.agent.md` |
| Audit hook | `.agents/hooks/audit_log.py` | `.claude/settings.json` hooks | `.github/hooks/audit.json` |
| Permissions | — | `.claude/settings.json` allow/ask/deny | `.vscode/settings.json` terminal auto-approve rules |
| Protection | `CODEOWNERS` | changes to any of the above need the PSO | same |
| Templates | `docs/templates/` | used by skills | same |

Check that each harness sees the bundle:

- **Claude Code:** run `claude`, type `/` and confirm `grill`, `spec-draft`, `acceptance-tdd`, `migration-writer` and `test-generator` appear. Run `/agents` and confirm `code-reviewer` and `security-reviewer`.
- **Copilot:** in Agent mode, type `/` and confirm the same skills appear. In the agent picker, confirm `code-reviewer` and `security-reviewer`.

## 5. Your first agent prompt (M1 Pair mode)

Try both builders on the same small job. That shows they are interchangeable.

**Claude Code** (run `claude` in the repo):

```
Create a README.md for a project called TicketDesk: a support-ticket web app
(FastAPI, PostgreSQL, Next.js) with AI triage and AI-suggested replies.
Keep it under 15 lines. Do not create any other files.
```

**Copilot** (VS Code Chat → Agent mode). Give it the same prompt, but ask for `README.copilot.md`.

Compare the two outputs, keep the better one as `README.md`, and delete the other file.

Now open `.agents/audit/audit.jsonl`. You'll see one line per tool call from **both** harnesses (`"harness": "claude"` and `"harness": "copilot"`), with secrets redacted.

Finally, test a guardrail. Ask either agent to `run az account show`. Claude Code refuses (deny rule); Copilot asks for confirmation instead of auto-running. Decline it.

> 🎩 **Developer hat:** you just merged agent-written text into your repo. You own it now. Did you read every line?

## 6. Commit and tag

```sh
git add -A
git commit -m "chore: initial README"
git push -u origin main
git tag m00-done && git push origin m00-done
```

## Done when

- [ ] `doctor` shows no `MISSING`
- [ ] Repo exists, with `README.md` on `main`
- [ ] Both harnesses list the 5 skills and 2 reviewer agents
- [ ] `audit.jsonl` has lines from both harnesses
- [ ] `python scripts/sync_agents.py --check` exits 0
- [ ] Tag `m00-done` is pushed
- [ ] You can answer the three "Check yourself" questions in `notes.md`
