# M2 — Spec, Grill, Design, Plan (P1)

**Goal:** turn a one-line feature idea into a plan an agent can execute without guessing.

> 🎩 **Product Owner** for the spec, **Tech Lead** for design, ADRs and `tasks.md`.

## 1. The P1 pipeline

```
idea ─► /spec-draft ─► spec.md (Draft) ─► /grill ─► spec.md (Grilled)
     ─► design.md + ADRs ─► tasks.md ─► 🎩 TL approves ─► agents may start (M4)
```

**Gate:** spec and `tasks.md` approved. **Nothing executes before that.** An agent in M2 (Delegated) may only run a task whose approval block is signed, and may only touch that task's "Files in scope".

## 2. EARS: requirements a test can check

| Pattern | Template | TD-007 example |
|---|---|---|
| Event | **When** <trigger>, the system shall … | When a ticket's first-response deadline passes with no staff reply, the system shall set `first_response_breached_at` within 60 s. |
| State | **While** <state>, … | While a ticket is breach-active, the queue shall list it first. |
| Unwanted | **If** <bad thing>, **then** … | (AC-7 style) at most one notification per user, even with concurrent sweeps. |
| Ubiquitous | The system shall … | The system shall never notify a user of a different tenant. |

Rules: one behaviour per criterion, no vague words, and every criterion gets an ID (`TD-007/AC-3`) that **test names must contain**. That ID is how M6 proves traceability.

## 3. Why grill a spec that looks complete

The TD-007 draft had 9 criteria and 5 honest open questions. It looked done. Grilling found that **"SLA deadline" was never defined**. Business hours? Paused while waiting on the customer? What happens on reopen, or on a priority change? Answering those produced 5 more criteria and one design insight: every clock event calls **one pure function**, `compute_deadlines()`.

The draft's own open questions covered only 2 of the 6 things that mattered. The value of the grill is in finding the questions nobody wrote down.

## 4. Design and ADRs: what goes where

| Artifact | Contains | Lifetime |
|---|---|---|
| `design.md` | How *this feature* works: data, algorithm, API, test plan, rollout | The feature |
| ADR | A decision that **outlives the feature** or **deviates from an org default** | The project |

TD-007's "sweep vs scheduled messages" stays in the design (it's local). Multi-tenancy with RLS (ADR-0003), JWT auth (ADR-0002) and APIM instead of LiteLLM (ADR-0001, a deviation from the org default) are ADRs. ADRs use the MADR format: context → drivers → options → outcome → consequences → **confirmation** (how we'll know it held).

## 5. `tasks.md`: the contract with the agent

Each task has: a goal, the ACs it covers, a mode (M1/M2), a risk tier, a branch, a **budget** (steps, time, tokens), **files in scope**, explicit out-of-scope items, done criteria, and when to escalate.

Good task design for agents:

- **Small:** each task yields a PR of about 400 lines or fewer.
- **Isolated:** tasks that don't share files can run in parallel (T-007-02 with Claude, T-007-03 with Copilot).
- **High-risk work in its own task:** the migration (T-007-01) is split out, because it needs 2 approvals.
- **The skill is named:** `migration-writer`, `acceptance-tdd`.

## Check yourself

1. Rewrite "The queue should show urgent tickets prominently" as an EARS criterion a test can verify.
2. Why is "sweep vs scheduled messages" in `design.md`, but "RLS" in an ADR?
3. T-007-02's agent finds it needs to change `compute_deadlines`. What does it do, and why?
