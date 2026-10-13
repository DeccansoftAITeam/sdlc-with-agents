# M6 Lab — Fuzz it, fix it, gate it

**Time:** about 3 h · **Starts at:** `m05-done` · **Ends at tag:** `m06-done`
**Needs:** Docker running (`docker compose up -d db`), the migrated database, and a reviewer account with **write** access to your fork

## Step 1 — Fuzz code that passes every test (25 min)

```sh
git switch -c lab/m06 m05-done
cd backend && uv run pytest -q && cd ..        # green, 97%
bash scripts/contract_test.sh                  # copy scripts/ from m06-done if you don't have it yet
```

Read every failure. For each 5xx, answer: which input, which line, and why did 218 tests miss it?

> Run it three times. Do you get the same failures each time? What does that mean for a single green run?

## Step 2 — Fix with regression tests first (45 min)

Hand your agent one finding at a time:

```
Contract fuzzing found: <paste the failing curl>. Write a regression test that fails,
show me it failing, then fix it at the boundary. Don't touch other endpoints.
```

Check that each test is red before the fix and green after. For the NUL bug, ask: fix it in one ticket field, or once for every endpoint? Why?

## Step 3 — Meet the breaking-change check (20 min)

```sh
(cd backend && uv run python ../scripts/export_openapi.py /tmp/head.json)
git worktree add /tmp/base m05-done                                    # the API before your fixes
(cd /tmp/base/backend && uv run python "$OLDPWD/scripts/export_openapi.py" /tmp/base.json)
docker run --rm -v /tmp:/w tufin/oasdiff:v1.32.1 breaking /w/base.json /w/head.json
```

Your fixes are breaking changes. Write the paragraph you'd put in the PR to justify the `api-breaking-approved` label. Who has to agree?

## Step 4 — Pull the new gate in (20 min)

```sh
uvx copier update --trust --skip-tasks --vcs-ref v1.2.0
```

Resolve conflicts (keep your project's code where it's a superset). Open `.github/workflows/pr-gate.yml` and find the three checks that were local-only in M5.

## Step 5 — The breach badge, acceptance-first (50 min)

Task card: T-007-04 in `docs/specs/TD-007-sla-breach-escalation/tasks.md`. Branch: `agent/T-007-04-breach-badge`.

1. Ask your agent for the Playwright test **only**: AC-3 order, AC-9 text badge, and axe with no serious or critical issues. Review it yourself: does it check text, not colour?
2. Run it: `pnpm --filter web e2e`. It must fail.
3. Now let the agent build `breachLabel()` (with a unit test), the login page and the queue page.
4. Green? Delete the badge line from `QueueTable.tsx` and run again. If the test still passes, it's not testing the badge.

## Step 6 — Review (15 min)

Run the `code-reviewer` subagent on your branch, and `security-reviewer` on the login page. Answer every finding with a fix or a reason in the PR.

## Step 7 — PR, approve, merge, tag (15 min)

Open the PR (title is a Conventional Commit; commits carry the `Agent-*` trailers). Watch all five jobs. Then, as the reviewer account: **Files changed → Review changes → Approve → Submit review**, then **Squash and merge**.

```sh
git switch main && git pull && git tag m06-done && git push origin m06-done
```

## Done when

- [ ] You found at least three 5xx bugs with fuzzing and fixed each with a red-then-green regression test
- [ ] You can explain why one green fuzz run isn't proof
- [ ] You justified a breaking API change in writing, and know why the label alone isn't enough
- [ ] Your E2E test fails without the badge and passes with it, and axe is clean
- [ ] All five PR-gate jobs are green on your PR
