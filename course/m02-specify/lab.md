# M2 Lab — TD-007 from Idea to Approved Plan

**Time:** about 3 h · **Starts at:** `m01-done` · **Ends at tag:** `m02-done`

Skills used: **`spec-draft`**, **`grill`**. Run each in either harness, then use the other one for the review in step 5.

## Step 1 — Backlog (10 min)

> 🎩 **Product Owner.** Create `docs/specs/BACKLOG.md` with features TD-001…TD-009 and TD-012, their risk tier, dependencies and build order. Compare with the reference.

## Step 2 — Draft the spec (20 min)

```
/spec-draft
Feature TD-007 "Escalate ticket on SLA breach". When a ticket misses its SLA
(first response or resolution), flag it, put it at the top of the queue and notify
the people who should act. Read docs/constitution.md first.
```

Check the draft: every criterion uses EARS and has an ID; tenant-isolation and "unwanted" criteria exist; doubts are listed as **Open questions**, not guessed.

## Step 3 — Grill the spec (40 min)

```
/grill
Subject: docs/specs/TD-007-sla-breach-escalation/spec.md
```

The reference run asked 6 questions ([grill log](../../docs/grill-logs/2026-10-07-td007.md)). Make sure yours reaches these topics, even if it asks in a different order:

- [ ] Calendar vs business time, and whose timezone
- [ ] Pausing while waiting on the customer
- [ ] How breaches are detected (sweep, scheduled job or lazy)
- [ ] Who is notified when nobody is assigned, and the duplicate-notification trap
- [ ] Whether a breach ever clears; what reopening does
- [ ] What a priority change does to deadlines

If your grill missed one, ask it: `Grill me on <topic>`. Then reply **`apply`**. The spec becomes `Grilled`.

> If a decision changes the constitution (here: SLA clock rules), the grill updates it and the amendment log. That needs TL + PO approval like any constitution change.

## Step 4 — Design + ADRs (50 min)

> 🎩 **Tech Lead.**

```
Write docs/specs/TD-007-sla-breach-escalation/design.md from docs/templates/design.md,
using the grilled spec. Include: C4 container delta, expand-only data changes,
the sweep algorithm (advisory lock, per-tenant loop under RLS, idempotent UPDATE…RETURNING),
queue ordering SQL, API changes, threat-model delta, AC→test table, flag plan, metrics.
```

```
Write ADRs in docs/adr/ using docs/templates/adr.md (MADR):
0001 Azure APIM AI gateway instead of LiteLLM (deviation from the org default),
0002 self-issued JWT with per-tenant identity, 0003 shared DB + RLS + path-slug routing.
Each ADR must have a "Confirmation" section naming the tests that prove it holds.
```

Read every ADR's **Consequences**. If an ADR lists no downsides, it hasn't been thought through.

## Step 5 — Independent design review (20 min)

With the **other** builder:

```
Review docs/specs/TD-007-sla-breach-escalation/design.md against spec.md and ADR-0003.
For every acceptance criterion, say which part of the design satisfies it, and list any
criterion with no design support or any design element with no criterion. Do not edit files.
```

The reference review added **TM-016** (one huge tenant slows the sweep for everyone) to the threat model.

## Step 6 — tasks.md (30 min)

```
Write docs/specs/TD-007-sla-breach-escalation/tasks.md from docs/templates/tasks.md.
One task per PR (≤ ~400 lines). Split the migration into its own High-risk task using
the migration-writer skill. Name the skill each task uses. Mark tasks that can run in
parallel. Give each a budget and an exact "Files in scope" list.
```

## Step 7 — The gate: approve

> 🎩 **Tech Lead + Product Owner.** Read `tasks.md` as a contract: *if an agent does exactly this, and only this, do we get TD-007?* Then sign the approval tables in `spec.md`, `design.md` and `tasks.md`.

```sh
git add docs
git commit -m "docs(p1): TD-007 spec (grilled), design, ADR-0001..0003, tasks (approved)" \
  -m "Agent-Model: <model>" -m "Agent-Mode: M1" -m "Agent-Session: <id>" -m "Agent-Operator: <you>"
git push && git tag m02-done && git push origin m02-done
```

## Done when

- [ ] Spec status is `Approved`, with no open questions left
- [ ] Every AC appears in the design's test plan
- [ ] Three ADRs, each with Consequences (good *and* bad) and Confirmation
- [ ] `tasks.md` signed; each task has scope, budget, skill and done criteria
