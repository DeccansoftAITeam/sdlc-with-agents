<!--
TEMPLATE: Waiver  (standard_version 2.0.0)
A waiver is a time-boxed exception to a required gate, threshold, SLA, or rule.
Permanent exemptions do not exist. The conformance checker FAILS on an expired waiver.
Two places must agree:
  1. This document: docs/waivers/WVR-<nnn>-<slug>.md (the justification)
  2. The machine entry in .standards.yml under `waivers:` (gate, reason, expires, ref)
Approval:
  - Gate / threshold waivers: Tech Lead + Platform/Standards Owner.
  - Vulnerability SLA waivers (Critical/High CVE): Tech Lead + Platform/Standards Owner, max 30 days, renewable once.
  - In-flight project adoption waivers (rollout): expire within 1 quarter.
  - Loosening an AI eval threshold is NOT a waiver: it requires an ADR.
-->

# WVR-<nnn>: <Short title>

| Field | Value |
|---|---|
| Project | <name> |
| Waived item | <gate id from .standards.yml / threshold / SLA / rule> |
| Type | Gate / Threshold / Vulnerability SLA / Rollout adoption / Other |
| Requested by | <name> |
| Date | <YYYY-MM-DD> |
| Expires | <YYYY-MM-DD> (hard end date) |
| Status | Requested / Approved / Rejected / Expired / Closed early |

## 1. What is being waived

<!-- Exact gate or rule and the scope (whole repo / one path / one CVE id / one release). -->

## 2. Why it cannot be met now

<!-- Evidence. "Not enough time" alone is not a reason. -->

## 3. Risk while waived

| Risk | Likelihood | Impact | Compensating control |
|---|---|---|---|
| | | | |

## 4. Plan to close

| Step | Owner | Due | Issue |
|---|---|---|---|
| | | | |

## 5. Machine entry

```yaml
# add to .standards.yml
waivers:
  - gate: <gate-id>
    reason: "<one line>"
    expires: "<YYYY-MM-DD>"
    ref: "docs/waivers/WVR-<nnn>-<slug>.md"
```

## 6. Approval

| Role | Name | Date |
|---|---|---|
| Tech Lead | | |
| Platform/Standards Owner | | |
