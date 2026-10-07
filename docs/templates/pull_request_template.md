<!--
PR TEMPLATE  (standard_version 2.0.0)
Install as: .github/pull_request_template.md (or your repo host's equivalent).
Rules (P5 PR gate / P6 Review):
- Request human review only after automated gates are green.
- Resolve every agent-review finding (fix, or reply with a reason) before merge.
- PRs > ~400 changed lines (excluding generated code) may be returned unreviewed.
-->

## Summary

<!-- What changed and why, in 2–4 sentences. -->

## Links

- Spec / issue: <SPEC-nnn or issue #>
- Task: <T-nnn-nn or n/a>
- Acceptance criteria covered: <SPEC-nnn/AC-1, AC-2>
- ADR(s): <ADR-NNNN or none>

## Change-risk tier

- [ ] Low — docs / tests only
- [ ] Medium — application code
- [ ] **High** — auth, payments, PII, migrations, infrastructure, permissions, LLM/agent actions that write or send
  <!-- High ⇒ 2 approvals incl. Tech Lead + security checklist below -->

## Authorship & agent attribution

- [ ] Human-authored
- [ ] Agent-assisted (M1 Pair)
- [ ] Agent-delegated (M2) — branch `agent/*`
- [ ] Agent-unattended (M3) — 2 approvals (or Tech Lead) required

Harness & model: <e.g. Claude Code / OpenCode + model id>
Prompting human (accountable, cannot be sole approver): @<handle>
- [ ] Commits carry `Agent-Model` / `Agent-Mode` / `Agent-Session` / `Agent-Operator` trailers (no agent `Co-Authored-By`)
- [ ] Agent stayed within the task's "Files in scope"; no permission, CI, `.agents/` or `.standards.yml` changes (or Platform Owner is requested)

## Author checklist

- [ ] Tests written first; test names contain the AC IDs
- [ ] Bug fix includes a regression test that fails without the fix
- [ ] Local gate passed
- [ ] No new direct dependency — OR dependency justified: license `<license>`, Scorecard `<score>`, age ≥ 30 days
- [ ] OpenAPI changed? Generated client regenerated and committed; breaking changes labelled with version bump
- [ ] Docs updated (AGENTS.md / runbooks / architecture diagrams) where behaviour changed

## Database migration (if any)

- [ ] Not applicable
- [ ] Follows expand → migrate → contract; this PR is the <expand / migrate / contract> step
- [ ] Migration lint passes; no long table locks; indexes created concurrently
- [ ] Downgrade path tested (up → down → up)

## Feature flag (if any)

- [ ] Not applicable
- [ ] Flag `<key>` defaults OFF; owner `<name>`; removal date `<YYYY-MM-DD>`

## AI changes (prompts, models, retrieval, tools)

- [ ] Not applicable
- [ ] Prompt files changed under `prompts/` (no inline prompts)
- [ ] PR eval set passed (attach summary); thresholds unchanged or tightened (loosening needs ADR)
- [ ] New tools for in-product agents are allow-listed, typed, and HITL-gated if irreversible

## Security checklist (REQUIRED for High tier)

- [ ] Threat-model delta updated: <link to section>
- [ ] AuthN/AuthZ enforced server-side; ownership checks for object access
- [ ] Input validated at the boundary; output encoded; no raw SQL with user input
- [ ] No secrets in code, config, prompts, or logs; new secrets in vault only
- [ ] PII handling: minimised, masked in logs and prompts, retention honoured
- [ ] New external calls go through approved clients with timeouts and retries
- [ ] Security reviewer: @<handle>

## Reviewer checklist (contributor model)

- [ ] Solves the spec / issue — nothing more, nothing less
- [ ] Scope appropriate and explained; no unrequested changes
- [ ] Tests are meaningful (assert behaviour, not just status codes)
- [ ] Consistent with AGENTS.md, AD-xx decisions, and ADRs
- [ ] For agent PRs: no scope or permission expansion; plan was followed
