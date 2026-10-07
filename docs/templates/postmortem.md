<!--
TEMPLATE: Blameless Postmortem  (standard_version 2.0.0)
Location: docs/postmortems/<YYYY-MM-DD>-<slug>.md
Required for every Sev1 and Sev2 incident, published within 5 working days of resolution (10-OPERATIONS-STANDARD.md).
Blameless: describe systems and decisions, not people's faults. Name roles, not individuals, in the analysis.
Every action item becomes a tracked issue with an owner and due date.
-->

# Postmortem: <Incident title>

| Field | Value |
|---|---|
| Incident ID | INC-<nnn> |
| Severity | Sev1 / Sev2 |
| Status | Draft / Reviewed / Closed |
| Date of incident | <YYYY-MM-DD> |
| Duration (detect → resolve) | <hh:mm> |
| Incident commander | <role/name> |
| Author | <name> |
| Reviewed in ops review | <YYYY-MM-DD> |
| Client notified | <Yes, at time / Not required> |

## 1. Summary

<!-- 3–5 sentences: what happened, who was affected, how it was resolved. -->

## 2. Impact

| Dimension | Impact |
|---|---|
| Users affected | <n / %> |
| Functionality affected | <features> |
| Data loss / exposure | <none / description> |
| SLO budget consumed | <% of 28-day budget> |
| Financial / contractual | <...> |

## 3. Timeline (UTC)

| Time | Event |
|---|---|
| <hh:mm> | Change deployed / trigger |
| <hh:mm> | First alert fired (<alert name>) |
| <hh:mm> | Acknowledged |
| <hh:mm> | Mitigation applied (e.g. slot swap-back, flag OFF) |
| <hh:mm> | Resolved |

## 4. Detection

- How was it detected? <alert / user report / client>
- Time to detect: <mm>. Could we have detected it sooner? <how>

## 5. Root cause and contributing factors

<!-- Use "5 whys" or a causal tree. Include process and tooling factors, e.g. which gate could have caught it. -->
- Root cause: <...>
- Contributing factors:
  - <...>
- Was AI-generated code or an AI feature involved? <No / Yes: describe, incl. agent mode and review path>

## 6. What went well

- <...>

## 7. What went poorly / where we got lucky

- <...>

## 8. Action items

| # | Action | Type (prevent / detect / mitigate / process) | Owner | Issue | Due |
|---|---|---|---|---|---|
| 1 | <e.g. add migration lint rule for X> | prevent | | | |

## 9. Standard feedback

<!-- Should a gate, threshold, template or org rule change? If yes, open an RFC (templates/rfc.md). -->
- <...>
