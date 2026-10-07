---
name: acceptance-tdd
description: Implements one approved tasks.md item acceptance-test-first. Writes API/E2E acceptance tests from the EARS criteria, stops for human review, then implements in red-green vertical slices. Use in P3 for any task in an approved tasks.md, or when the user says "implement T<n>".
---
<!-- GENERATED from .agents/ by scripts/sync_agents.py. Do not edit. -->

# acceptance-tdd (org skill · standard 2.0.0 · P3)

## Inputs

- One task entry from `docs/specs/<ID>/tasks.md` (status `Approved`)
- The spec's acceptance criteria referenced by that task
- `AGENTS.md`, relevant ADRs

## Phase A: acceptance tests (then STOP)

1. For each referenced criterion, write an acceptance test through the **public interface** (an HTTP API test with httpx, or a Playwright E2E test). Name it `test_<id>_ac<n>_<behaviour>`, e.g. `test_td007_ac2_breach_notifies_assignee`.
2. Add a **cross-tenant test** for every new endpoint: a user from tenant B gets 404, never tenant A's data.
3. Run the tests and confirm they **fail for the right reason** (a missing feature, not a broken fixture).
4. Write the state to `.agents/progress/<task-id>.md`. **Stop and ask a human to review the tests.** Don't implement until they say so.

## Phase B: implement in vertical slices

5. Pick one failing acceptance test. Write the smallest code that makes it pass. Add unit tests only where the logic is complex. One test → one implementation → repeat. Never write all the tests first and then all the code.
6. After each green step: run `uv run pytest -q` for the affected area and update the progress file.
7. Refactor only while everything is green.
8. Finish by running the local gate (`pre-commit run --all-files`). Fix failures; never suppress them.

## Rules

- Change only the task's **Files in scope**. If you need another file, stop and ask.
- Never edit, skip or weaken an approved acceptance test to make it pass. If the test looks wrong, stop and ask.
- Bug fixes start with a regression test that fails without the fix.
- In M2: branch `agent/<task-id>-<slug>`, open a **draft** PR, and add Agent-* trailers on commits (org rules §8).
