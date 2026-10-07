<!--
TEMPLATE: Runbook  (standard_version 2.0.0)
Location: docs/runbooks/<alert-or-procedure-name>.md
Rule: every alert links to exactly one runbook; no alert without a runbook (checked by conformance).
Write for someone woken at 3 a.m. who has never seen this service: numbered steps, copy-pasteable commands,
clear decision points. Never put secrets in a runbook; reference the vault entry name.
-->

# Runbook: <Alert name / Procedure>

| Field | Value |
|---|---|
| Service | <service> |
| Alert(s) linked | <alert rule name(s)> |
| Severity guidance | <Sev2 if …; Sev1 if …> |
| Owner | <team / role> |
| Last tested | <YYYY-MM-DD> |

## 1. What this alert means

<!-- One paragraph: the SLI, the threshold, and the user impact. -->

## 2. Dashboards & links

- Service dashboard: <name in telemetry backend>
- Traces query: <saved query name>
- Error tracker project: <name>
- LLM traces (if AI feature): <Langfuse project name>

## 3. Triage (first 10 minutes)

1. Acknowledge the alert and open an incident channel if Sev1/Sev2.
2. Check whether a deploy happened in the last 2 hours: `<command to list recent releases>`
3. Check dependencies: database health, LLM gateway health, third-party status.
4. Decide: is this caused by the latest release?
   - **Yes →** go to §4 Rollback.
   - **No / unsure →** go to §5 Diagnosis.

## 4. Mitigation / rollback

| Situation | Action | Command / steps |
|---|---|---|
| Bad release (web/API) | Swap back to previous slot / revision | `<command>` |
| Faulty feature | Turn feature flag OFF | `<flag key>` in flag service |
| AI feature misbehaving | Kill-switch flag OFF; confirm gateway budget | `<flag key>` |
| Mobile OTA update bad | Republish previous EAS Update to channel | `<command>` |
| DB overload | <scale / kill long query> | `<command>` |

Do NOT roll back a database migration without the Tech Lead; prefer roll-forward (expand/contract makes the previous app version compatible).

## 5. Diagnosis

1. <step>
2. <step>

Common causes:

| Symptom | Likely cause | Fix |
|---|---|---|
| | | |

## 6. Verification

- [ ] SLI back within objective for 15 minutes
- [ ] No new errors in error tracker
- [ ] Synthetic / smoke checks green

## 7. Escalation

| After | Escalate to | How |
|---|---|---|
| 30 min unresolved | Tech Lead | <channel / phone> |
| Data exposure suspected | Tech Lead + client contact; follow security incident steps (07-SECURITY-STANDARD.md) | |

## 8. Follow-up

- Sev1/Sev2: postmortem within 5 working days (templates/postmortem.md).
- Update this runbook with anything that was missing.
