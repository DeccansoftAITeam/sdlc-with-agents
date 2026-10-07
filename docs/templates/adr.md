<!--
TEMPLATE: Architecture Decision Record (MADR style)  (standard_version 2.0.0)
Location: docs/adr/NNNN-<kebab-title>.md   (NNNN = next zero-padded number)
Write one when: a decision is hard to reverse, adds a dependency to a core layer, picks a datastore/queue/
auth approach/model or provider, or deviates from a default in 04-ARCHITECTURE-DECISIONS.md.
Approver: Tech Lead. Deviation from an org default (AD-xx): Platform/Standards Owner as well.
Once Accepted, an ADR is immutable. To change it, write a new ADR that supersedes it.
-->

# ADR-NNNN: <Short title of the decision>

| Field | Value |
|---|---|
| Status | Proposed / Accepted / Rejected / Deprecated / Superseded by ADR-XXXX |
| Date | <YYYY-MM-DD> |
| Deciders | <names / roles> |
| Consulted | <names / roles> |
| Deviates from org default? | <No / Yes: AD-xx> |
| Related spec(s) | <SPEC-nnn> |

## Context and problem statement

<!-- 2–5 sentences. What forces us to decide, and what question are we answering? -->

## Decision drivers

- <driver, e.g. "p95 < 300 ms under 200 rps">
- <driver, e.g. "must stay cloud-neutral">

## Considered options

1. <Option A>
2. <Option B>
3. <Option C>

## Decision outcome

Chosen option: **<Option X>**, because <justification tied to the drivers>.

### Consequences

- Good: <...>
- Bad / accepted trade-off: <...>
- Follow-up actions: <issue links>

### Confirmation

<!-- How we will verify the decision is implemented and still holds: an architecture test, a CI check, a metric, a review item. -->
- <e.g. "ArchUnit rule features_must_not_import_other_features">

## Pros and cons of the options

### <Option A>
- Good: <...>
- Bad: <...>

### <Option B>
- Good: <...>
- Bad: <...>

## More information

<!-- Links to specs, benchmarks done in-repo, related ADRs. No external dependencies required to understand the decision. -->
