---
name: test-generator
description: Generates QA-level test scenarios (API scenario tests and Playwright E2E) from specs and the running app, mapped to acceptance criteria, for human QA review. Use in P3/P8 when QA wants more coverage, or when the user says "generate tests for <ID>".
---
<!-- GENERATED from .agents/ by scripts/sync_agents.py. Do not edit. -->

# test-generator (org skill · standard 2.0.0 · QA support)

You **propose** tests; QA owns them. Generated tests never count as acceptance proof until a human has reviewed them.

## Steps

1. Read `docs/specs/<ID>/spec.md` and the traceability report (`docs/traceability.md`, if it exists). List every acceptance criterion that has no test, or only a happy-path test.
2. For each gap, propose scenarios: happy path, boundaries, invalid input, **authorization** (wrong role), **tenant isolation** (wrong tenant), concurrency where it matters (e.g. two staff members assigning the same ticket).
3. Write the tests in `tests/qa/` (API, pytest + httpx) or `apps/web/e2e/` (Playwright). Name each one `test_<id>_ac<n>_<scenario>`. Use synthetic data from factories only, never real PII.
4. Run them. A failing test means either a real bug (report it) or a wrong test (fix it). Label each failure as one or the other.
5. Output a table of criterion → new tests → result, for QA to review.

## Rules

- Never change application code. Never change existing approved tests.
- Use stable selectors only (`getByRole`, `data-testid`). No sleeps; use web-first assertions.
