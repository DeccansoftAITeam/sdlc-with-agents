# M1 Lab — Intake, Constitution, Threat Model

**Time:** about 2 h · **Starts at:** `m00-done` · **Ends at tag:** `m01-done`

You'll do each step with **one** builder: Claude Code or Copilot agent mode. The prompts work in both. Use the other builder for the review step, so a second "pair of eyes" checks the first one's draft.

Copy the two templates into the repo first:

```sh
mkdir -p docs/architecture docs/security
cp <standard>/templates/constitution.md docs/constitution.md
cp <standard>/templates/threat-model.md docs/security/threat-model.md
```

## Step 1 — Get grilled (20 min)

The `grill` skill arrives in M3. For now, paste this prompt:

```
You are interviewing me, the Product Owner, for a new product called TicketDesk:
a support-ticket web app with AI triage and AI-suggested replies.
Ask me ONE question at a time. For each question give your recommended answer
and a one-line critique of that recommendation. Stop when you can fill every
section of docs/constitution.md. Do not write any files yet.
```

Answer it as the PO. Your answers should match these (they are the course's decisions):

- Multi-tenant SaaS for other companies
- Own JWT login, no Entra ID/SSO
- SLAs P1 1 h / P2 4 h / P3 1 bd / P4 3 bd first response; availability 99.5%
- Tickets may contain PII → ASVS L2

## Step 2 — Draft the constitution (20 min)

```
Using our interview, fill docs/constitution.md from its template.
Rules: keep it under 250 lines; every NFR has a number and a "measured by";
list non-goals explicitly (no email ingestion, no SSO, no mobile, no AI auto-actions);
mark the ADRs we still owe as ADR-0001 LLM gateway, ADR-0002 auth, ADR-0003 multi-tenancy.
Delete template comments. Do not create other files.
```

> 🎩 **Tech Lead hat:** read it line by line. Check each number against what you decided. Agents love to "helpfully" invent targets.

## Step 3 — C4 context (10 min)

```
Create docs/architecture/c4-context.md: a C4 level-1 mermaid diagram of TicketDesk
with three user types (end customer, support staff, tenant admin) and the external
systems (Azure APIM AI gateway → Azure OpenAI, outbound email provider).
Add a table: element, responsibility, trust level.
```

## Step 4 — Threat model (40 min)

```
Fill docs/security/threat-model.md from its template for TicketDesk v1, using
docs/constitution.md and docs/architecture/c4-context.md.
- Trust boundaries must include tenant-vs-tenant isolation.
- STRIDE rows: at least 10, each with a concrete "Verified by" test name or gate.
- Complete the OWASP LLM Top 10 table for AI triage and AI suggested reply.
- Complete the agentic table for OUR coding-agent setup.
- Mark everything "Planned" (no code exists yet).
```

**Review with the other builder:**

```
Review docs/security/threat-model.md as an adversarial security reviewer.
List the 5 most important missing threats or weak mitigations for a multi-tenant
SaaS with JWT auth and RAG. Do not edit the file.
```

Add the findings you agree with. The reference solution added attachment authorization (TM-010) and the noisy-neighbour threat (TM-011) during this review.

## Step 5 — Approve and tag

The gate is TL + PO approval. Fill in §13 Approval in the constitution, then:

```sh
git add docs && git commit -m "docs(p0): constitution, C4 context, threat model v1"
git push && git tag m01-done && git push origin m01-done
```

## Done when

- [ ] Constitution has no `<placeholder>` left (`grep -n "<" docs/constitution.md`)
- [ ] Every STRIDE row has a "Verified by"
- [ ] OWASP LLM table is complete for both AI features
- [ ] Approval table is signed
- [ ] Compare against the reference: `git diff m01-done -- docs/` in the course repo
