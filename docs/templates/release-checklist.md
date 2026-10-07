<!--
TEMPLATE: Release Go / No-Go Checklist  (standard_version 2.0.0)
Location: attach to the release PR (created by release-please) or docs/release/<version>.md
Used in: P9 Release gate → P10 Deploy.
The automated release gate produces most evidence; humans confirm and sign.
Any unchecked blocking item = No-go (or a dated waiver per templates/waiver.md).
-->

# Release <vX.Y.Z> — Go / No-Go

| Field | Value |
|---|---|
| Project | <name> |
| Release tag | <vX.Y.Z> |
| Artifact digest(s) | <image@sha256:…> |
| Previous production digest (rollback target) | <image@sha256:…> |
| Mobile | <store build n / OTA update group id / n/a> |
| Date | <YYYY-MM-DD> |

## 1. Automated release gate (Staging) — all blocking

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Full E2E (web + mobile) + Bruno API suite 100% pass (quarantined tests listed) | ☐ | report |
| 2 | Traceability: every AC in this release has a passing test | ☐ | traceability report |
| 3 | DAST: no High findings | ☐ | |
| 4 | Load test meets constitution budgets (p95, error rate) | ☐ | k6 summary |
| 5 | Accessibility: no serious/critical violations on key flows | ☐ | axe report |
| 6 | Full AI eval + red team meet thresholds, 0 critical | ☐ / n/a | eval report |
| 7 | SBOM generated; artifact signed; provenance verified | ☐ | |
| 8 | No unwaived Critical/High CVEs | ☐ | |
| 9 | Migration rehearsal on masked snapshot passed; duration: <mm:ss> | ☐ / n/a | |
| 10 | Rollback plan: previous digest recorded; migration down path or expand/contract confirmed | ☐ | |

## 2. Change summary

- Changelog: <link to release PR section>
- Breaking API changes: <none / list + version bump>
- New / changed feature flags and their rollout state: <...>
- Migrations in this release: <expand / migrate / contract steps>

## 3. Operational readiness

- [ ] On-call aware of release window
- [ ] Dashboards and alerts cover new features
- [ ] Runbooks updated for new alerts
- [ ] First production launch? → Production Readiness Review completed (templates/production-readiness-review.md)
- [ ] Client approval obtained (only if the contract requires it)

## 4. Deploy plan (P10)

1. Deploy signed digest to production slot / new revision
2. Run smoke tests against the slot
3. Swap / shift traffic
4. Watch SLO dashboards for <30> minutes
5. Mobile: EAS Submit; staged store rollout starting at 10%

Rollback trigger: <e.g. error rate > 2× baseline for 5 min, or any Sev1> → swap back, flag OFF.

## 5. Sign-off

| Role | Name | Decision (Go / No-go) | Date |
|---|---|---|---|
| QA Engineer | | | |
| Release Manager | | | |
