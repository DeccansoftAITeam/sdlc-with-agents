<!--
TEMPLATE: Production Readiness Review (PRR)  (standard_version 2.0.0)
Location: docs/release/prr.md
Required once, before the FIRST production launch of a project (in addition to the normal release gate).
Also repeat after a major architectural change (new container, new datastore, new AI capability).
Participants: Tech Lead, Release Manager, QA, rotating security reviewer, operator (Deccansoft or client).
Every "No" needs either a fix before launch or a waiver (templates/waiver.md) with an expiry date.
-->

# Production Readiness Review — <Project Name>

| Field | Value |
|---|---|
| Date | <YYYY-MM-DD> |
| Release | <vX.Y.Z> |
| Participants | <names / roles> |
| Decision | Go / Go with waivers / No-go |

## 1. Architecture & design

| Check | Yes/No | Evidence |
|---|---|---|
| Constitution complete and approved (NFRs, SLOs, budgets, RPO/RTO) | | docs/constitution.md |
| C4 Context + Container diagrams current | | docs/architecture/ |
| ADRs recorded for all hard-to-reverse decisions | | docs/adr/ |
| Threat model current, no open High-impact threats | | docs/security/threat-model.md |

## 2. Reliability & operations

| Check | Yes/No | Evidence |
|---|---|---|
| SLOs defined and burn-rate alerts deployed | | |
| Every alert links to a runbook | | docs/runbooks/ |
| Dashboards for service, DB, LLM gateway | | |
| Error tracking live; source maps / debug symbols uploaded | | |
| On-call rota defined (business hours default / 24×7 per contract) | | |
| Incident process and escalation contacts known | | |
| Load test met performance budgets | | k6 report |

## 3. Data & recovery

| Check | Yes/No | Evidence |
|---|---|---|
| PITR enabled; retention matches constitution | | |
| Automated restore test executed successfully at least once | | restore job run id |
| RPO / RTO achievable per restore test timing | | |
| Data residency configuration matches constitution | | IaC module |
| Retention / deletion jobs (incl. embeddings, LLM traces) in place | | |

## 4. Security

| Check | Yes/No | Evidence |
|---|---|---|
| ASVS level verified (L1 / L2) | | checklist |
| Pen test done (required for L2) and High findings fixed | | report ref |
| DAST: no High findings | | |
| No unwaived Critical/High CVEs | | |
| Secrets in vault; CI uses OIDC; workload identity for app → DB/vault | | |
| JIT production access configured; standing access removed | | |
| security.txt / vulnerability contact published | | |

## 5. Release & rollback

| Check | Yes/No | Evidence |
|---|---|---|
| Artifact signed; SBOM + provenance attached | | |
| Slot / revision deploy with smoke tests; swap-back rehearsed | | |
| Migration rehearsal on masked snapshot done; timing acceptable | | |
| Feature flags for risky features, default OFF, kill switches tested | | |
| Mobile: store listing, staged rollout plan, OTA channel policy | | |

## 6. AI features (if any)

| Check | Yes/No | Evidence |
|---|---|---|
| AI intake complete for each feature | | spec §7 |
| Full eval suite meets thresholds; red team 0 critical | | eval report |
| Guardrails (input/output) active; kill switch tested | | |
| Gateway budgets and rate limits configured | | |
| User disclosure and content labelling present | | screenshots |
| Langfuse tracing + feedback capture live | | |

## 7. Handover (if client operates)

| Check | Yes/No | Evidence |
|---|---|---|
| Handover pack delivered (templates/handover-pack.md) | | |
| 30-day hypercare scheduled | | |

## 8. Waivers & sign-off

| Waiver | Expires | Approved by |
|---|---|---|
| | | |

| Role | Name | Decision | Date |
|---|---|---|---|
| Tech Lead | | | |
| Release Manager | | | |
| QA | | | |
| Security reviewer | | | |
