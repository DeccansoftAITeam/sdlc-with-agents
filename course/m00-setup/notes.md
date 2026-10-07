# M0 — Setup and the Big Picture

**Goal:** know the whole journey before taking the first step, and have a working toolbox.

## 1. What changes when agents write the code

Typing code is no longer the slow part. What is left to manage:

- **Intent.** An agent builds exactly what it is told, so vague requirements turn into wrong code quickly.
- **Verification.** Agents produce more code than people can read line by line, so machines have to check most of it.
- **Accountability.** Something has to stop an agent that is wrong but sure of itself.

The SDLC in this course is designed around those three problems.

## 2. Three rules you will meet in every module

1. **Instructions guide; gates enforce.** A rule written in `AGENTS.md` is a suggestion. A rule in CI, a branch protection or a hook is a law. Anything that must *always* hold becomes a check.
2. **Everything is in the template.** Each project starts with all the practices already in place. Nothing gets "added later".
3. **Humans stay accountable.** Agents plan, write, test and review. Humans approve plans, merges and releases. **If you merge it, you own it,** whoever wrote it.

## 3. The map

```
PLAN    M1  P0  Intake       → constitution, SLOs, threat model
        M2  P1  Specify      → spec (EARS) → grill → design → tasks.md   ◄ human approves
BUILD   M3  P2  Scaffold     → repo skeleton + agent config + skills
        M4  P3  Implement    → acceptance tests FIRST, then agents code
        M5  P4  Local gate   → hooks, < 90 s
        M6  P5-7 PR → Review → Merge   → CI < 10 min, agent review + human approval
        M7  P3  AI feature   → gateway, prompts as files, evals, kill-switch
        M8  P8  Scheduled    → nightly deep tests, weekly agent reviews
SHIP    M9  P9  Release gate → 10 checks + sign-offs on staging
        M10 P10 Deploy       → same image → new revision → smoke → swap
RUN     M11 P11 Operate      → SLOs, alerts, runbooks, incidents, learning
        M12 Capstone         → one feature, end to end, on your own
```

Checks happen at four **gate layers**. Each layer is a different speed of feedback:

| Layer | When | What it blocks |
|---|---|---|
| LOCAL | On commit or push | Your push |
| PR | Every PR update | The merge |
| NIGHTLY | Scheduled | Nothing. It reports and opens issues |
| RELEASE | Before production | The release |

## 4. Three ways to work with an agent

| Mode | You... | Typical use in this course |
|---|---|---|
| **M1 Pair** | Drive it interactively | Exploring, small fixes, Copilot in the IDE |
| **M2 Delegated** | Hand it one approved `tasks.md` item; it opens a draft PR | Most feature work |
| **M3 Unattended** | Don't take part; CI runs it on a schedule | Nightly or weekly jobs (M8) |

In every mode, an agent **never** merges, deploys, reads production data, edits gate configs or skips a test. These limits are enforced by permissions and branch rules, not by asking the agent nicely.

## 5. The org agent bundle: installed before the first prompt

Agents need the rules *before* they touch the repo, so every project starts with the **org bundle**:

| Layer | What | Who changes it |
|---|---|---|
| L1 Org rules | Forbidden actions, modes, attribution, injection hygiene | Platform Owner only |
| L2 Project `AGENTS.md` | Project facts and commands (a stub now, full in M3) | Tech Lead |
| L3 Adapters | `CLAUDE.md`, `copilot-instructions.md`, permissions, hooks | Platform Owner |
| L4 Skills + subagents | `grill`, `spec-draft`, `acceptance-tdd`, `migration-writer`, `test-generator`, `code-reviewer`, `security-reviewer` | Platform Owner |
| L5 Tool allow-list | `.agents/mcp-allowlist.yml` | Platform Owner |

**One source, three delivery channels.** The bundle lives in its own repo (`DeccansoftAITeam/agent-bundle`) and is released as tags. Projects install a pinned version: **skills** through `npx skills` (one command, both harnesses), **Claude subagents and hooks** through a Claude Code plugin, and **Copilot subagents and hooks, plus the org rules**, through the bundle's installer. Each channel writes a lock file, so conformance can tell whether a repo drifted from its pinned version.

**Where each skill shows up in the course:**

| Module | Skill / agent / tool |
|---|---|
| M1 | `grill` (constitution, threat model) |
| M2 | `spec-draft` → `grill` → design → tasks |
| M4 | `acceptance-tdd`, `migration-writer`, `treehouse` |
| M5 | git hooks, optional `no-mistakes` |
| M6 | `code-reviewer`, `security-reviewer` |
| M8 | `test-generator`, `gnhf` |
| M11 | `backpass` |

## 6. The hats you will wear

The course has one learner, but the standard has six roles. When a module switches roles, you'll see a callout:

> 🎩 **Tech Lead hat:** you are now approving, not writing.

| Role | What you do as that role |
|---|---|
| Product Owner | Write and accept requirements |
| Tech Lead | Design, approve plans, review high-risk changes |
| Developer | Direct agents; own every merged line |
| QA | Write acceptance tests; sign off releases |
| Release Manager | Approve production; roll back |
| Platform Owner | Own gates and agent config |

Rule to remember: **the person who prompted an agent can't be the only approver of its PR.** In labs where you are alone, the course shows how a second approver (or a CODEOWNERS rule) fills that gap.

## 7. The product: TicketDesk

- Customers raise support tickets. Support staff work through a queue: they assign tickets, reply and close them.
- Each priority has an SLA timer. A breach escalates the ticket.
- **AI triage** suggests a category and priority. A human can override it.
- **AI suggested reply** drafts an answer from help articles (RAG). A human edits it before sending.

One feature, **TD-007 Escalate ticket on SLA breach**, runs through every module, so you'll see a single change go from idea to production.

## Check yourself

1. An `AGENTS.md` line says "never commit secrets". Why is that not enough, and what makes it a rule that actually holds?
2. You delegated task T3 to Claude Code, which opened a PR. Can you approve it alone?
3. Which gate layer would you use for a 40-minute mutation-testing run, and why not the PR layer?
