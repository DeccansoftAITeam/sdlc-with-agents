# TicketDesk — C4 Level 1: System Context

```mermaid
flowchart TB
  cust["👤 End customer<br/>(of a tenant)<br/>Raises and follows tickets"]
  staff["👤 Support staff<br/>(tenant employee)<br/>Works the queue, replies"]
  admin["👤 Tenant admin<br/>Manages users, SLAs, KB"]

  td["🟦 TicketDesk<br/>Multi-tenant ticketing SaaS<br/>FastAPI · Postgres · Next.js on Azure Container Apps"]

  gw["⬜ Azure APIM AI gateway<br/>Token limits, metrics, kill-switch"]
  aoai["⬜ Azure OpenAI (Foundry)<br/>gpt-4.1-mini · text-embedding-3-small"]
  mail["⬜ Email provider<br/>Notifications only (outbound)"]

  cust -->|HTTPS, JWT| td
  staff -->|HTTPS, JWT| td
  admin -->|HTTPS, JWT| td
  td -->|Masked prompts| gw --> aoai
  td -->|Notifications| mail
```

| Element | Responsibility | Trust |
|---|---|---|
| End customer | Creates tickets, reads replies, sees only their own tickets | Untrusted |
| Support staff | Sees all tickets of their tenant | Authenticated, tenant-scoped |
| Tenant admin | Configures their tenant | Authenticated, tenant-scoped, elevated |
| TicketDesk | All business logic; owns all data | Our system |
| APIM AI gateway | The only path to LLMs: quotas, logging, kill-switch | Ours (config) |
| Azure OpenAI | Model inference; no data retention for training | Third party (Microsoft) |
| Email provider | Sends notification emails | Third party |

The container view (C4 level 2) comes in M2 `design.md`.
