# ADR-0001: Azure APIM AI gateway instead of LiteLLM

| Field | Value |
|---|---|
| Status | Accepted |
| Date | 2026-10-07 |
| Deciders | Tech Lead |
| Consulted | Platform/Standards Owner |
| Deviates from org default? | **Yes**: the org default LLM gateway is LiteLLM |
| Related spec(s) | TD-008, TD-009 |

## Context and problem statement

All LLM calls must go through a gateway (org rules §5) that gives us model pinning, per-caller quotas, usage metrics and a kill-switch. The org default is a self-hosted LiteLLM proxy. TicketDesk runs on Azure, uses Azure OpenAI in Foundry, and needs **per-tenant** token caps (constitution §12: 200k tokens per month and 20 requests per minute per tenant) that clients can't bypass.

## Decision drivers

- Per-tenant token quota keyed on a trusted, server-set identity
- No extra service to run, patch and scale ourselves
- Managed identity end to end, with no API keys in the app
- Cost: idle cost close to zero for a teaching project

## Considered options

1. LiteLLM proxy as a Container App (org default)
2. **Azure API Management AI gateway, Consumption tier**
3. Call Azure OpenAI directly, with quotas in application code

## Decision outcome

**Option 2: APIM AI gateway (Consumption).** The API calls APIM with its managed identity, and APIM calls Azure OpenAI with *its* managed identity. Policies: `llm-token-limit` keyed on the `x-tenant-id` header (set by the API, never by the client) with a monthly quota and per-minute rate, `llm-emit-token-metric` per tenant, and a named value `ai-enabled` as the global kill-switch. APIM accepts only the API's identity (`validate-azure-ad-token`).

### Consequences

- Good: quotas and metrics per tenant with no app code. Pay per call; no idle cost.
- Good: switching or adding a model is a gateway change, invisible to the app.
- Bad: APIM policies are XML and harder to unit-test. We add a gateway policy test in M7 (call over quota → 429).
- Bad: the Consumption tier has cold starts (first call after idle may take 1–3 s), which is acceptable within the 5–6 s AI budgets.
- Bad: we're tied to Azure for the gateway. The app talks plain OpenAI-compatible HTTP, so swapping to LiteLLM later only changes the base URL and auth.

### Confirmation

M7 tests: over-quota tenant gets 429 and the UI shows "AI paused for this month"; a request without the API's token gets 401; flipping `ai-enabled` stops all AI calls within 60 s.

## Pros and cons of the options

### LiteLLM proxy
- Good: org default, provider-neutral, rich budgets.
- Bad: another container to run and secure; its own Postgres for budgets; idle cost.

### Direct calls + app quotas
- Good: simplest.
- Bad: quotas in app code can be bypassed by bugs; no central kill-switch; violates "all LLM calls go through the gateway".
