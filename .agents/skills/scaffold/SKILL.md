---
name: scaffold
description: Generates a new project repo from the org scaffold (Copier template DeccansoftAITeam/project-scaffold), fills project-specific values from docs/constitution.md, writes the project AGENTS.md, and verifies the result. Use in P2 for a new project, or for `copier update` when the scaffold releases a new version.
---

# scaffold (org skill · standard 2.1.0 · P2)

M1 Pair only: a human watches every step, because the scaffold writes gate configs.

## Inputs

- `docs/constitution.md` (approved; P0 gate passed)
- Scaffold version to use (pinned tag, e.g. `v1.0.0`)

## New project

1. Read the constitution and derive the Copier answers: `project_name`, `project_slug`, `python_package`, `asvs_level`, `has_ai`, `cloud`, `region`, `owner_team`. Show them to the human and **wait for confirmation**.
2. Run:
   `uvx copier copy --trust --vcs-ref <tag> gh:DeccansoftAITeam/project-scaffold . --data-file <answers.yml>`
   The scaffold's post-copy tasks install git hooks and the agent bundle. Report any task that fails; don't "fix" it by editing scaffold-owned files.
3. Write the **project `AGENTS.md`** (L2, under 300 lines) from `AGENTS.md` in the scaffold plus the constitution: purpose, principles, non-goals, stack, how to run, test and gate locally, folder map, the ADR list, and "where things go". Facts only; no rules that duplicate org rules.
4. Verify:
   - `docker compose up -d db` then `cd backend && uv run alembic upgrade head && uv run pytest -q`
   - `uvx pre-commit run --all-files`
   - `python scripts/check_conformance.py` (if present)
5. Report: what was generated, which checks pass, and anything the human must do outside the repo (branch protection, environments, secrets).

## Updating an existing project

1. On a branch `chore/scaffold-<new-tag>`: `uvx copier update --trust --defaults --skip-tasks --vcs-ref <new-tag>`.
   `--skip-tasks` is required: Copier re-renders the *old* version in a temp dir, where post-generation tasks fail.
2. Resolve conflicts (`*.rej` files or inline markers) by **keeping project changes to project-owned files** and **taking the scaffold's version of gate files**.
3. Run the post-update steps the tasks would have run: `cd backend && uv lock`, `pnpm install`, and `python scripts/install_agent_bundle.py <ref>` if `agent_bundle_ref` changed.
4. Run the full local gate (`uvx pre-commit run --hook-stage pre-push --all-files`).
5. Open a PR labelled `scaffold-update` that needs Platform/Standards Owner review.

## Rules

- Never edit `.copier-answers.yml` by hand.
- Never weaken a generated gate (hook, workflow, threshold) to get green. Stop and ask.
