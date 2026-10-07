<!--
TEMPLATE: Feature Spec  (standard_version 2.0.0)
Location: docs/specs/<SPEC-ID>-<slug>/spec.md
Produced in: P1 Specify & Design. Drafted by Product Owner (agent-assisted), grilled, then approved.
Small changes (bug fix, copy change, single layer and < ~3 files) skip this file: use an issue with EARS criteria instead.
IDs: spec = SPEC-<nnn>; criteria = SPEC-<nnn>/AC-<n>. Tests must reference AC IDs (06-TESTING-STRATEGY.md).
-->

# SPEC-<nnn>: <Feature title>

| Field | Value |
|---|---|
| Status | Draft / Grilled / Approved / Superseded |
| Product Owner | <name> |
| Tech Lead | <name> |
| Change-risk tier | Low / Medium / **High** (see below) |
| Feature flag | `<flag-key>` (owner: <name>, removal date: <YYYY-MM-DD>) |
| Related ADRs | <ADR-NNNN, ...> |
| Tracker link | <ticket id> |

<!--
Change-risk tier:
- Low: docs, tests only.
- Medium: application code.
- High: auth, payments, PII handling, migrations, infrastructure, permissions, any LLM/agent action that writes or sends.
High ⇒ threat-model delta required, 2 approvals incl. Tech Lead, security checklist in PR.
-->

## 1. Problem & outcome

<!-- What is wrong today, for whom, and what measurable outcome proves success. -->
<problem statement>

Success measure: <metric + target>

## 2. User stories

- **US-1** As a <role>, I want <capability>, so that <benefit>.
- **US-2** ...

## 3. Acceptance criteria (EARS)

<!--
EARS patterns:
- Ubiquitous:     The <system> shall <response>.
- Event-driven:   When <trigger>, the <system> shall <response>.
- State-driven:   While <state>, the <system> shall <response>.
- Unwanted:       If <unwanted condition>, then the <system> shall <response>.
- Optional:       Where <feature is included>, the <system> shall <response>.
One behaviour per criterion. Each must be testable. Each maps to ≥ 1 automated test.
-->

| ID | Story | Criterion (EARS) | Test layer (unit/integration/E2E/eval) |
|---|---|---|---|
| SPEC-<nnn>/AC-1 | US-1 | When <trigger>, the system shall <response>. | <layer> |
| SPEC-<nnn>/AC-2 | US-1 | If <unwanted condition>, then the system shall <response>. | <layer> |
| SPEC-<nnn>/AC-3 | US-2 | While <state>, the system shall <response>. | <layer> |

## 4. Out of scope

- <explicitly excluded behaviour>

## 5. Non-functional notes

<!-- Only deltas from the constitution: new budgets, new SLO, accessibility, localisation. -->
- <note>

## 6. Data & privacy

- New personal data collected? <Y/N — what, why, retention>
- New data shared with third parties (incl. LLM providers)? <Y/N — what>

## 7. AI use-case intake

<!-- REQUIRED if the feature calls an LLM or runs an agent. Otherwise write "Not applicable". -->

| Item | Answer |
|---|---|
| Purpose of the AI component | <what it does, for whom> |
| Why AI (vs deterministic logic)? | <justification> |
| Risk tier | Low / Medium / High |
| EU AI Act category | Minimal / Limited (transparency duties) / High-risk (Annex III) / Not in scope |
| Data sent to the model | <fields, classification, masking> |
| Retrieval sources (RAG) | <sources, owners, permission model> |
| Tools / actions the AI can take | <list; mark irreversible or external ones> |
| Human-in-the-loop points | <where a human approves before effect> |
| User disclosure | <how users are told AI is involved; content labelling> |
| Model(s) + fallback | <pinned model ids via gateway> |
| Eval criteria | <metrics + thresholds; default org thresholds unless tightened> |
| Golden set | <location, initial size ≥ 50, curator> |
| Cost budget | <per task / per month> |
| Kill switch | flag `<flag-key>` |

## 8. Open questions

| # | Question | Owner | Resolved answer |
|---|---|---|---|
| 1 | | | |

<!-- Spec is "Approved" only when every open question is resolved. -->

## 9. Approval

| Role | Name | Date |
|---|---|---|
| Product Owner | | |
| Tech Lead | | |
