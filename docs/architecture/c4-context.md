# TicketDesk — C4 Level 1: System Context

```mermaid
flowchart TB
  cust["👤 End customer<br/>(of a tenant)<br/>Self-registers per tenant, raises tickets"]
  staff["👤 Support staff<br/>(tenant employee)<br/>Works the queue, replies"]
  admin["👤 Tenant admin<br/>Self-serve signup; manages users, SLAs, KB, AI opt-in"]

  td["🟦 TicketDesk<br/>Multi-tenant ticketing SaaS<br/>FastAPI · Postgres · Next.js on Azure Container Apps"]

  gw["⬜ Azure APIM AI gateway<br/>Token limits, metrics, kill-switch"]
  aoai["⬜ Azure OpenAI (Foundry)<br/>gpt-4.1-mini · text-embedding-3-small"]
  mail["⬜ Azure Communication Services Email<br/>Auth messages only: verify, reset"]

  cust -->|HTTPS, JWT| td
  staff -->|HTTPS, JWT| td
  admin -->|HTTPS, JWT| td
  td -->|Masked prompts| gw --> aoai
  td -->|Verify / reset links| mail
```

| Element | Responsibility | Trust |
|---|---|---|
| End customer | Creates tickets, reads replies, sees only their own tickets | Untrusted |
| Support staff | Sees all tickets of their tenant | Authenticated, tenant-scoped |
| Tenant admin | Configures their tenant | Authenticated, tenant-scoped, elevated |
| TicketDesk | All business logic; owns all data | Our system |
| APIM AI gateway | The only path to LLMs: quotas, logging, kill-switch | Ours (config) |
| Azure OpenAI | Model inference; no data retention for training | Third party (Microsoft) |
| ACS Email | Sends account verification and password-reset emails only | Third party (Microsoft) |

The container view (C4 level 2) comes in M2 `design.md`.
