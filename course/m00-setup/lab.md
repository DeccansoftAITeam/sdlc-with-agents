# M0 Lab — Toolbox and Empty Repo

**Time:** about 45 min · **Ends at tag:** `m00-done`

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

## 4. Your first agent prompt (M1 Pair mode)

Try both builders on the same small job. That shows they are interchangeable.

**Claude Code** (run `claude` in the repo):

```
Create a README.md for a project called TicketDesk: a support-ticket web app
(FastAPI, PostgreSQL, Next.js) with AI triage and AI-suggested replies.
Keep it under 15 lines. Do not create any other files.
```

**Copilot** (VS Code Chat → Agent mode). Give it the same prompt, but ask for `README.copilot.md`.

Compare the two outputs, keep the better one as `README.md`, and delete the other file.

> 🎩 **Developer hat:** you just merged agent-written text into your repo. You own it now. Did you read every line?

## 5. Commit and tag

```sh
git add -A
git commit -m "chore: initial README"
git push -u origin main
git tag m00-done && git push origin m00-done
```

## Done when

- [ ] `doctor` shows no `MISSING`
- [ ] Repo exists, with `README.md` on `main`
- [ ] Tag `m00-done` is pushed
- [ ] You can answer the three "Check yourself" questions in `notes.md`
