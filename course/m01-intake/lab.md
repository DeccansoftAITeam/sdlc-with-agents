# M1 Lab — Intake, Constitution, Threat Model

**Time:** about 2.5 h · **Starts at:** `m00-done` · **Ends at tag:** `m01-done`

Skills used: **`grill`** (installed in M0). The audit hook logs every step.

Run each step in **one** builder (Claude Code or Copilot agent mode); the skills and prompts work in both. Use the **other** builder for the review in step 5, so two separate "pairs of eyes" see the work.

## Step 1 — Intake interview with `/grill` (25 min)

> 🎩 **Product Owner hat.**

The constitution doesn't exist yet, so give the grill a one-paragraph brief to work from:

```
/grill
Subject: intake for a new product, TicketDesk: a support-ticket web app with AI triage
and AI-suggested replies (FastAPI, PostgreSQL, Next.js, Azure). Goal: gather everything
needed to fill docs/templates/constitution.md. Start with who the customer is.
```

Answer one question at a time. The course's answers:

- Multi-tenant SaaS for other companies
- Own JWT login, no SSO
- SLA first response P1 1 h / P2 4 h / P3 1 business day / P4 3 business days; availability 99.5%
- Tickets may hold PII → ASVS L2

Watch for the **stress-test** line after each of your answers. That's where the skill earns its keep.

## Step 2 — Draft the P0 files (25 min)

```
Using the grill decisions, create:
1. docs/constitution.md from docs/templates/constitution.md: under 250 lines, every NFR
   with a number and "measured by", explicit non-goals, ADRs owed (0001 gateway,
   0002 auth, 0003 multi-tenancy).
2. docs/architecture/c4-context.md: C4 level-1 mermaid + element/responsibility/trust table.
3. docs/security/threat-model.md from its template: tenant-vs-tenant trust boundary,
   10+ STRIDE rows each with a "Verified by" test or gate, OWASP LLM table for both AI
   features, agentic table for our coding-agent setup. All rows "Planned".
```

Notice that `docs/constitution.md` is on the **ask** list in `.claude/settings.json`, and Copilot asks before editing too. The constitution is protected even though it's a markdown file.

## Step 3 — Grill the draft (40 min)

This is the step people skip, and it's the most valuable one.

```
/grill
Subject: docs/constitution.md and docs/security/threat-model.md as drafted.
Find decisions that are missing, vague, or contradict each other. Security and tenancy first.
```

The reference run asked **9 questions**. Compare yours with [`docs/grill-logs/2026-10-07-constitution.md`](../../docs/grill-logs/2026-10-07-constitution.md). Your questions will differ; the categories shouldn't:

- How tenants are created (self-serve?) and what that costs if it's abused
- Whether identity is global or per tenant
- How a request finds its tenant (and why the token must win)
- Scope cuts (attachments)
- Notification channel, and its **conflict** with email verification (Q6 → Q7)
- AI consent and per-tenant cost caps

When the grill prints its decision summary, reply **`apply`**.

## Step 4 — Check what changed (15 min)

> 🎩 **Tech Lead hat.**

```sh
git diff --stat
git diff docs/constitution.md
```

Check these by hand: the new principle 7 (tenant from token), the new non-goals, the per-tenant AI limits paragraph, threat model v2 rows TM-013/014/015, and TM-010 withdrawn.

## Step 5 — Independent review with the other builder (20 min)

```
Act as an adversarial security reviewer. Read docs/constitution.md and
docs/security/threat-model.md. List the 5 most important remaining gaps for a
self-serve multi-tenant SaaS with per-tenant JWT identity and opt-in RAG.
Do not edit any file.
```

Add the findings you agree with, using a second `/grill` pass if a finding needs a decision.

## Step 6 — Approve and tag

The gate is TL + PO approval. Sign §13 of the constitution, then commit using the org attribution trailers (org rules §8):

```sh
git add docs
git commit -m "docs(p0): constitution, C4 context, threat model v2 (grilled)" \
  -m "Agent-Model: <model>" -m "Agent-Mode: M1" -m "Agent-Session: <id>" -m "Agent-Operator: <you>"
git push && git tag m01-done && git push origin m01-done
```

## Done when

- [ ] No `<placeholder>` left in the constitution
- [ ] A grill log exists in `docs/grill-logs/`, and every decision is reflected in a document
- [ ] Every STRIDE row has a "Verified by"
- [ ] OWASP LLM table complete for both AI features
- [ ] `.agents/audit/audit.jsonl` shows the session (try: `grep -c '"tool"' .agents/audit/audit.jsonl`)
- [ ] Approval signed, tag pushed
