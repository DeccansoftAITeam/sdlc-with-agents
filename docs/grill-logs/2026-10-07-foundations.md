# Grill log — Foundation specs TD-001 … TD-006 (brief)

| Field | Value |
|---|---|
| Skill | `grill` (agent-bundle v2.0.0), **brief mode**: the agent proposes, the PO/TL reviews the decision list |
| Interviewer | Claude Code (Opus 5.5) |
| Decider | PO/TL delegated the decisions on 2026-10-07 ("you briefly grill"); review below |
| Why brief | These features follow already-decided ADRs and constitution rules; TD-007 got the full grill |

| # | Spec | Question | Decision (agent recommendation, accepted) | Why |
|---|---|---|---|---|
| 1 | TD-001 | Can an unverified admin use the app? | Yes, but can't invite staff or enable AI (AC-11) | Lets signup "just work" while blocking the abuse paths in TM-013 |
| 2 | TD-001 | Password policy? | ≥ 12 chars + breached-list check; no composition rules | ASVS L2 V2.1; composition rules reduce real security |
| 3 | TD-001 | Reserved slugs? | `api, admin, t, login, signup, static, health` + regex | Grill Q3 of the constitution |
| 4 | TD-002 | Must customers verify before creating tickets? | Yes (AC-4) | Self-registration plus no verification = spam relay |
| 5 | TD-002 | Can the last admin be demoted? | No (AC-6) | Otherwise the tenant gets locked out with no recovery path in v1 |
| 6 | TD-002 | Revoke sessions on role change? | Yes (AC-7) | A demoted admin keeps admin rights for up to 15 min otherwise (access-token lifetime) |
| 7 | TD-003 | Can customers set priority? | No; default P3, staff or AI set it (AC-3) | Every customer picks P1; it also corrupts SLA data |
| 8 | TD-003 | Ticket identifier shown to users? | Per-tenant sequence `#1, #2` | Global IDs leak tenant volume; UUIDs are unfriendly |
| 9 | TD-004 | Reopen window after resolve? | A customer reply always reopens | Simplest; matches TD-007 AC-11 (resume clocks) |
| 10 | TD-004 | Is there a `closed` state? | No; `resolved` is terminal unless reopened | Fewer states and fewer SLA edge cases |
| 11 | TD-005 | Policy change applies to existing tickets? | No; targets snapshotted at creation (AC-2) | Otherwise a policy edit can make hundreds of old tickets breach at once |
| 12 | TD-005 | Default timezone? | `UTC` until the admin sets one | No safe way to guess a tenant's timezone; the UI prompts on first SLA visit |
| 13 | TD-006 | Real-time delivery? | 30 s polling, no websockets | Matches the 60 s SLO; websockets add infra for no product gain in v1 |
| 14 | TD-006 | Retention? | 90 days | Notifications are transient; keeps the table small |

**For PO/TL review:** decisions 7, 9 and 11 have visible product impact. Overrule any of them by editing the spec and appending a row here.
