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

## 4. Install the org agent bundle (20 min)

> 🎩 **Platform Owner hat.** The bundle lives in its own repo, [`DeccansoftAITeam/agent-bundle`](https://github.com/DeccansoftAITeam/agent-bundle): the org's central standards repo. Projects install a **pinned version** (`v2.0.0`) and commit the result.

First copy the **project scaffold files** from the course repo. These are guardrails that live in *your* repo and are protected by CODEOWNERS, not by an installer:

```sh
git clone --branch m00-done https://github.com/DeccansoftAITeam/sdlc-with-agents ../course-ref
cp -r ../course-ref/scripts ../course-ref/docs .
cp ../course-ref/{AGENTS.md,CLAUDE.md,CODEOWNERS,.gitignore,.gitattributes} .
mkdir -p .claude .github .vscode
cp ../course-ref/.claude/settings.json .claude/
cp ../course-ref/.github/copilot-instructions.md .github/
cp ../course-ref/.vscode/settings.json .vscode/
```

Then install the bundle in three steps, one per delivery channel:

```sh
# 1. Skills for both harnesses → .claude/skills/ and .agents/skills/ + skills-lock.json
DISABLE_TELEMETRY=1 npx skills add DeccansoftAITeam/agent-bundle#v2.0.0 \
  --skill '*' -a claude-code -a github-copilot --copy -y

# 2. Org rules, MCP allow-list, Copilot subagents + Copilot audit hook → .agents/bundle.lock
git clone --depth 1 --branch v2.0.0 https://github.com/DeccansoftAITeam/agent-bundle ../agent-bundle
python ../agent-bundle/scripts/install.py .

# 3. Claude Code subagents + audit hook: the deccansoft-org plugin.
#    Nothing to run. .claude/settings.json already registers the marketplace and enables
#    the plugin, so Claude Code prompts you to install it the first time you open the repo.
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
- **Drift check:** `python ../agent-bundle/scripts/install.py . --check` exits 0.

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
- [ ] `skills-lock.json` and `.agents/bundle.lock` are committed, both pinned to `v2.0.0`
- [ ] `install.py . --check` exits 0
- [ ] Tag `m00-done` is pushed
- [ ] You can answer the three "Check yourself" questions in `notes.md`
