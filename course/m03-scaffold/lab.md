# M3 Lab — Generate TicketDesk from the Scaffold

**Time:** about 2 h · **Starts at:** `m02-done` · **Ends at tag:** `m03-done`
**Skills:** `scaffold` (M1 Pair) · **Needs:** Docker running, access to `DeccansoftAITeam/project-scaffold` and `agent-bundle`


> **Seeing the reference files.** Your `../course-ref` is checked out at the M0 tag, so later files aren't in it. Read any file at any module's finished state with:
> ```sh
> git -C ../course-ref fetch --tags
> git -C ../course-ref show m03-done:<path>        # e.g. m03-done:docs/constitution.md
> ```
> or browse it on GitHub: `https://github.com/DeccansoftAITeam/sdlc-with-agents/blob/m03-done/<path>`.

## Step 1 — Let the agent derive the answers (15 min)

```
/scaffold
Generate this project from DeccansoftAITeam/project-scaffold at v1.0.2.
Derive the Copier answers from docs/constitution.md and show them to me first.
```

Expected answers (check them yourself):

| Answer | Value | From the constitution |
|---|---|---|
| project_name / slug | TicketDesk / ticketdesk | §1 |
| asvs_level | L2 | §9 |
| multi_tenant | true | Principle 1, ADR-0003 |
| has_ai | true | §12 (AI triage, suggested reply) |
| cloud / region | azure / eastus2 | §4, §5 |
| agent_bundle_ref | v2.1.2 | Pinned org bundle |

> 🎩 **Tech Lead:** confirm. The agent must not proceed without your go-ahead (skill rule).

## Step 2 — Generate (20 min)

The skill runs, in your existing repo:

```sh
uvx copier copy --trust --overwrite --vcs-ref v1.0.2 gh:DeccansoftAITeam/project-scaffold . --data ...
```

Post-generation tasks: `uv lock`, `pnpm install`, git hooks installed, agent bundle installed. Then:

```sh
git status        # constitution, specs and course files untouched; new: backend/, apps/, ...
```

## Step 3 — Complete AGENTS.md (15 min)

The skill fills the `TODO(scaffold skill)` sections from the constitution: product, the principles you'll trip over in code, non-goals, ADR table, work in flight. **Read it as a new agent would.** Does it tell you where tenant data access goes? What not to build?

## Step 4 — Prove it works (30 min)

```sh
docker compose up -d db
cd backend && uv run pytest -q          # 16 tests, RLS isolation included, coverage ≥ 80%
cd .. && pnpm typecheck && pnpm test
git add -A && git commit -m "chore(p2): scaffold TicketDesk from project-scaffold v1.0.2"
uvx pre-commit run --hook-stage pre-push --all-files     # all Passed, < 90 s warm
```

Open `backend/tests/test_rls.py` and read the five tests. **Break one on purpose:** in `app/core/db.py` change `set_config(..., true)` to `false` (session-wide instead of transaction-local) and rerun `uv run pytest tests/test_rls.py --no-cov`. **Two** tests fail. The scary one is `test_no_tenant_set_sees_nothing`: a request with *no* tenant now sees another tenant's row, because the pooled connection kept the previous request's setting. One keyword is all that separates SaaS isolation from a data breach. Revert.

## Step 5 — Feel a gate catch something (15 min)

Create a throwaway migration that adds an index the dangerous way:

```sh
cd backend && uv run alembic revision -m "demo bad index"
# in upgrade(): op.execute("CREATE INDEX ix_demo ON alembic_version (version_num)")
git add -A && git commit -m "chore: demo" && uvx pre-commit run --hook-stage pre-push --all-files
```

squawk fails: `require-concurrent-index-creation`. That's the gate the `migration-writer` skill is written to satisfy. Delete the revision and reset the commit (`git reset --hard HEAD~1`).

## Step 6 — Practise an update (15 min)

```sh
git switch -c chore/scaffold-update
uvx copier update --trust --defaults --skip-tasks --vcs-ref v1.0.2
```

Nothing changes, because you're already on v1.0.2. Read `.copier-answers.yml`: that's how the Platform Owner can see which projects are behind.

## Step 7 — Protect `main` (15 min)

> 🎩 **Platform Owner.** Add a second person (or your second account) as a collaborator and code owner (`copier update -d "code_owners=@you @reviewer"`), then create the ruleset:

```sh
gh api -X POST repos/<owner>/<repo>/rulesets --input ruleset.json
```

Use the JSON from the reference repo (`Settings → Rules`): PR required, 1 code-owner approval, **last-push approval**, dismiss stale reviews, resolved threads, required checks `hygiene`/`backend`/`web`, squash only. Then prove it: `git commit --allow-empty -m test && git push`. Expect `GH013: Changes must be made through a pull request`.

## Step 7 — Tag

```sh
git switch main && git tag m03-done && git push origin m03-done   # tags aren't covered by the branch ruleset
```

## Done when

- [ ] `.copier-answers.yml` shows `_commit: v1.0.2`, `agent_bundle_ref: v2.1.2`
- [ ] Backend tests (16) and web tests pass; pre-push gate fully green
- [ ] `AGENTS.md` has no `TODO` left
- [ ] You broke and repaired tenant isolation, and saw squawk block a locking index
