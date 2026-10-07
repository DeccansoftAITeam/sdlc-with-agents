---
name: spec-draft
description: Drafts a feature spec with user stories and EARS acceptance criteria from a short feature request, using templates/spec.md. Use in P1 when a new feature (e.g. TD-007) needs a spec, or when the user says "draft a spec".
---
<!-- GENERATED from .agents/ by scripts/sync_agents.py. Do not edit. -->

# spec-draft (org skill · standard 2.0.0 · P1)

## Inputs

- Feature ID and a one-paragraph request from the Product Owner
- `docs/constitution.md` (principles, non-goals, NFRs, SLOs)
- `docs/templates/spec.md`

## Steps

1. Create `docs/specs/<ID>-<slug>/spec.md` from the template. Set Status to `Draft`.
2. Write user stories: `As a <role>, I want <capability>, so that <outcome>`.
3. Write acceptance criteria in **EARS**, one behaviour each, with IDs `<ID>/AC-n`:

| Pattern | Form |
|---|---|
| Ubiquitous | The system shall … |
| Event | **When** <trigger>, the system shall … |
| State | **While** <state>, the system shall … |
| Unwanted | **If** <condition>, **then** the system shall … |
| Optional | **Where** <feature>, the system shall … |

4. For every criterion ask: can a test prove it? If not, rewrite it. Avoid vague words ("fast", "user-friendly", "appropriate"); put numbers in instead.
5. Always add **tenant-isolation** and **authorization** criteria (constitution principle 1). Add unwanted-behaviour criteria for failures.
6. If the feature uses an LLM, fill the AI use-case intake section.
7. List everything you were unsure about under **Open questions**. Don't guess. Grilling resolves them.

## Rules

- Write no code and no tests. A spec describes *what*, not *how*.
- Anything that contradicts a non-goal goes under Open questions, not into the spec.
- Next step is always `/grill` on this spec.
