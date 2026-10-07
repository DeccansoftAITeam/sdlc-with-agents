<!--
TEMPLATE: Handover Pack  (standard_version 2.0.0)
Location: docs/handover/README.md
Required when the client (or another party) will operate production (10-OPERATIONS-STANDARD.md).
Delivered before go-live; followed by a mandatory 30-day hypercare period operated by Deccansoft.
Everything listed must live in the repository or be exported into it — no knowledge in private chats.
-->

# Handover Pack — <Project Name>

| Field | Value |
|---|---|
| Delivered to | <client team / contact> |
| Delivered by | <Tech Lead> |
| Delivery date | <YYYY-MM-DD> |
| Hypercare | <start> → <end> (30 days), contact: <on-call channel> |
| Release at handover | <vX.Y.Z> |

## 1. System overview

- Constitution: docs/constitution.md
- Architecture (C4 + arc42-lite): docs/architecture/
- ADR index: docs/adr/
- Threat model: docs/security/threat-model.md

## 2. Environments & access

| Environment | Purpose | Access method | Owner after handover |
|---|---|---|---|
| Staging | Release testing / UAT | <identity group> | |
| Production | Live | JIT, time-boxed | |

- Infrastructure as code: infra/ (OpenTofu). State location: <backend name>. Who can apply: <role>.
- Secrets: vault <name>; secret names listed in docs/handover/secrets-inventory.md (names only, never values).
- Credentials to rotate at handover: <list>

## 3. Build, release & deploy

- How to cut a release: release PR → merge → tag (09-ENVIRONMENTS-AND-RELEASE.md)
- Release gate checks and where reports appear: <...>
- Deploy & rollback procedure: docs/runbooks/deploy-and-rollback.md
- Mobile: store accounts, EAS project, OTA channel policy: <...>

## 4. Operations

| Item | Location |
|---|---|
| Dashboards | <names in telemetry backend> |
| SLO definitions | docs/constitution.md §8 + alert rules in repo |
| Alerts → runbooks | docs/runbooks/ |
| Error tracking | <project name> |
| LLM tracing / prompt management | <Langfuse project> |
| Backup & restore procedure (with last restore-test result) | docs/runbooks/restore.md |
| DR procedure | docs/runbooks/disaster-recovery.md |
| Incident process & postmortem template | docs/postmortems/README.md |
| Cost budgets & alerts | <...> |

## 5. Security

- Open waivers and their expiry: docs/waivers/
- Vulnerability SLAs and dependency policy in force: <summary>
- Last pen test / DAST results: <...>
- Security contact (security.txt): <...>

## 6. AI features (if any)

- Feature inventory with models, providers, fallbacks (AI-BOM): <...>
- Prompt files: prompts/; golden sets: evals/
- Eval thresholds and how to run evals: <commands>
- Guardrails configuration and kill-switch flags: <...>
- Gateway budgets / rate limits: <...>

## 7. Known issues & backlog

| Item | Severity | Issue |
|---|---|---|
| | | |

## 8. Acceptance

| Check | Done |
|---|---|
| Client walked through deploy, rollback, restore | ☐ |
| Client on-call has access to dashboards, alerts, runbooks | ☐ |
| Credentials rotated; Deccansoft standing access removed after hypercare | ☐ |

| Role | Name | Date |
|---|---|---|
| Deccansoft Tech Lead | | |
| Client operations owner | | |
