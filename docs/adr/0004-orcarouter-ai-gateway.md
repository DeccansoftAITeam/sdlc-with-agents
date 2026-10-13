# ADR-0004: OrcaRouter as the AI gateway, with direct Anthropic as an alternative

| Field | Value |
|---|---|
| Status | Proposed |
| Date | 2026-10-13 |
| Deciders | Tech Lead, Product Owner |
| Supersedes | [ADR-0001](0001-azure-apim-ai-gateway.md) (Azure APIM AI gateway) |
| Deviates from org default? | **Yes**: the org default LLM gateway is LiteLLM |
| Related spec(s) | TD-008 (TD-009 is a course sidebar) |

## Context and problem statement

ADR-0001 put Azure OpenAI behind the Azure APIM AI gateway. The PO now wants **no Azure spend for the AI path** while learning, and to use **Claude** models. OrcaRouter is a hosted, OpenAI-compatible gateway that serves Anthropic models (and others, including embeddings) with one API key. The PO also wants **direct Anthropic** supported, so a tenant (or the course) isn't locked to one router.

What APIM gave us for free now has to come from somewhere: per-tenant quotas, a kill-switch, usage metrics, and a trusted caller identity.

## Decision drivers

- Claude models, no Azure resources for AI
- One provider interface, so OrcaRouter and direct Anthropic are interchangeable
- Per-tenant caps (constitution §12) that a bug or a client can't bypass
- The API key never reaches a browser, a log, or the repository (the repos are public)

## Considered options

1. Keep APIM + Azure OpenAI (ADR-0001)
2. **OrcaRouter (default) + direct Anthropic (alternative), caps and kill-switch in the app**
3. Self-hosted LiteLLM (org default)

## Decision outcome

**Option 2.**

- `app/adapters/llm/` holds the only code that talks to a model, behind one port: `complete(model, messages, schema) -> parsed output + usage`. Two adapters: `orcarouter` (OpenAI-compatible HTTP, `base_url=https://api.orcarouter.ai/v1`) and `anthropic` (Anthropic Messages API). `LLM_PROVIDER` picks one; the default is `orcarouter`.
- Models are settings: `AI_TRIAGE_MODEL`, `AI_REPLY_MODEL`, `AI_EMBEDDING_MODEL`. OrcaRouter defaults: `anthropic/claude-haiku-4.5` for triage (Haiku 5.5 has no capacity on OrcaRouter today; switch when it does), `anthropic/claude-sonnet-5.5` for replies, `openai/text-embedding-3-small`. Direct Anthropic defaults: `claude-haiku-5-5`, `claude-sonnet-5-5`.
- Keys come from the environment only: `ORCAROUTER_API_KEY` or `ANTHROPIC_API_KEY`. Locally they live in the gitignored `backend/.env`; in CI and Azure, in secrets. Neither is ever logged.
- **Per-tenant caps move into the app**, enforced in one place, the adapter's caller (`ai/budget.py`), before any call: a monthly token ledger per tenant (200k tokens) and a rate limit of 20 AI requests per minute. Usage is recorded from the provider's response, not estimated.
- **Kill-switch:** the global `ai-enabled` setting plus the per-tenant feature flag. Either one off → no call is made.

### Consequences

- Good: no Azure cost for AI; Claude models; the provider can be swapped by configuration.
- Good: caps are plain Python, so they're unit-testable (APIM's XML policies weren't).
- Bad: caps live in our code. A bug can overspend. Mitigation: one budget check guarding the only adapter, an architecture test that nothing else imports `app.adapters.llm`, and OrcaRouter's own account spending limit as a backstop.
- Bad: **data residency changes.** Ticket text (masked) is processed by OrcaRouter and Anthropic outside Azure East US 2. Constitution §5 is amended accordingly. Masking before every call becomes even more important.
- Bad: one more external service with its own availability. AI is optional by design (the ticket works without triage), so an outage degrades and doesn't break.

### Confirmation

M7 tests: a tenant over its monthly tokens gets no AI call and the UI says "AI paused for this month"; the 21st request in a minute is refused; with the flag or `ai-enabled` off no adapter is called; an architecture test fails if any module outside `ai/` imports `app.adapters.llm`; a log-capture test shows no key and no unmasked ticket text.

## Pros and cons of the options

### APIM + Azure OpenAI
- Good: quotas and metrics without app code; managed identity, no keys.
- Bad: Azure cost; no Claude models.

### LiteLLM
- Good: org default, provider-neutral, budgets built in.
- Bad: another service to run, plus its own Postgres; idle cost.
