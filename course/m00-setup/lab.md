# M0 Lab — Toolbox and Empty Repo

**Time:** about 1 h · **Ends at tag:** `m00-done-v2`

> **Which shell?** All labs use **bash** syntax. On Windows, use **Git Bash** (installed with Git: Start → "Git Bash"). `cmd.exe` and PowerShell don't understand several commands in these labs. The two Python scripts below (`doctor.py`, `bootstrap.py`) work in any shell.

## 1. Install the toolbox

| Tool | Version | Why |
|---|---|---|
| git (includes Git Bash on Windows) | 2.40+ | — |
| GitHub CLI `gh` | 2.50+ | PRs, repo settings |
| Python | 3.12+ | Backend, lab scripts |
| uv | 0.6+ | Python deps and venvs |
| Node.js | 22+ | Frontend, `npx skills` |
| pnpm | 9+ | Frontend deps |
| Docker | 24+ | Postgres locally, images |
| Azure CLI `az` | 2.60+ | Deploy (from M6) |
| Claude Code | latest | Builder agent |
| VS Code + GitHub Copilot (Chat, agent mode) | latest | Builder agent |

## 2. Sign in

```sh
gh auth login
az login
claude          # follow the login prompt, then /exit
```

In VS Code, sign in to GitHub Copilot and check that **Agent** mode appears in the Chat view.

## 3. Create your repo and get the course files

```sh
gh repo create <you>/sdlc-with-agents --private --clone
cd sdlc-with-agents
git clone --branch m00-done-v2 https://github.com/DeccansoftAITeam/sdlc-with-agents ../course-ref
python ../course-ref/course/m00-setup/doctor.py
```

`doctor.py` lists every tool with its version. Fix every `MISSING` line before you continue. On Windows it also warns you if you're not in Git Bash.

## 4. Install the guardrails and the org agent bundle (20 min)

> 🎩 **Platform Owner hat.** The bundle lives in its own repo, [`DeccansoftAITeam/agent-bundle`](https://github.com/DeccansoftAITeam/agent-bundle): the org's central standards repo. Projects install a **pinned version** (`v2.0.0`) and commit the result.

From the root of **your** repo:

```sh
python ../course-ref/course/m00-setup/bootstrap.py
```

The script does three things (read it: it's short). Background on each route: [Start here → 3. How extensions get installed](../start-here/03-installing-extensions.md).

1. **Copies the project scaffold files**: `scripts/`, `docs/`, `AGENTS.md`, `CLAUDE.md`, `CODEOWNERS`, `.gitignore`, `.gitattributes`, `.claude/settings.json`, `.github/copilot-instructions.md`, `.vscode/settings.json`. These guardrails live in *your* repo, protected by CODEOWNERS, not by an installer.
2. **Installs the skills** for both harnesses: `npx skills add DeccansoftAITeam/agent-bundle#v2.0.0 …` → `.claude/skills/`, `.agents/skills/`, `skills-lock.json`.
3. **Installs org rules, Copilot subagents and hooks** with the bundle's `install.py` → `.agents/`, `.github/agents/`, `.github/hooks/`, `.agents/bundle.lock`.

The fourth delivery channel needs no command. **Claude Code subagents and hooks** come from the `deccansoft-org` plugin, which `.claude/settings.json` already enables:

```sh
claude      # accept the plugin install prompt, then /exit
```

What arrived, and from where:

| Piece | Claude Code | GitHub Copilot | Delivered by |
|---|---|---|---|
| L1 org rules | `.agents/org/org-rules.md` (imported by `CLAUDE.md`) | same file (via `AGENTS.md`) | `install.py` |
| L4 skills (5) | `.claude/skills/` | `.agents/skills/` | `npx skills` |
| L4 subagents (2) | plugin `deccansoft-org` | `.github/agents/*.agent.md` | plugin / `install.py` |
| Audit hook | plugin `hooks/hooks.json` | `.github/hooks/audit.json` → `.agents/hooks/audit_log.py` | plugin / `install.py` |
| Permissions | `.claude/settings.json` | `.vscode/settings.json` | **project scaffold** (not the bundle) |
| Version pins | `skills-lock.json`, `.agents/bundle.lock`, plugin `ref` in settings | same | all three |

**Why are permissions not in the bundle?** A gate a developer can uninstall isn't a gate. Deny-lists stay in the repo, behind CODEOWNERS, and conformance checks them (M8).

Check that each harness sees the bundle:

- **Claude Code:** `/plugin` shows `deccansoft-org` enabled. Typing `/` lists `grill`, `spec-draft`, `acceptance-tdd`, `migration-writer` and `test-generator`. `/agents` lists `code-reviewer` and `security-reviewer`.
- **Copilot (Agent mode):** typing `/` lists the same five skills, and the agent picker shows both reviewers.
- **Drift check:** clone the bundle once (`git clone --depth 1 --branch v2.0.0 https://github.com/DeccansoftAITeam/agent-bundle ../agent-bundle`), then `python ../agent-bundle/scripts/install.py . --check` exits 0.

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
git branch -M main      # some machines default to 'master'; this renames it
git push -u origin main
git tag m00-done && git push origin m00-done      # your own tag in your repo
```

## Done when

- [ ] `doctor` shows no `MISSING`
- [ ] Repo exists, with `README.md` on `main`
- [ ] Both harnesses list the 5 skills and 2 reviewer agents
- [ ] `audit.jsonl` has lines from both harnesses
- [ ] `skills-lock.json` and `.agents/bundle.lock` are committed, both pinned to `v2.0.0`
- [ ] `install.py . --check` exits 0
- [ ] Tag `m00-done` is pushed
- [ ] You can answer the three "Check yourself" questions in `notes.md`
