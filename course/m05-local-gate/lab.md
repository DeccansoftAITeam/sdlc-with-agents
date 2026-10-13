# M5 Lab — Measure, break and tune the local gate

**Time:** about 2 h · **Starts at:** `m04-done` · **Ends at tag:** `m05-done`
**Needs:** Docker running (`docker compose up -d db`)

## Step 1 — Measure (20 min)

```sh
git switch -c lab/m05 m04-done
uvx pre-commit run --all-files --verbose                      # pre-commit stage
time uvx pre-commit run --all-files --hook-stage pre-push --verbose
```

Write down each hook's `duration`. At `m04-done` the pre-push total is about **95 s**: over the 90 s budget. Which hook dominates?

## Step 2 — Look for the time (20 min)

```sh
cd backend
uv run pytest -q --no-cov --durations=10       # any single hot spot?
time uv run pytest -q --no-cov                 # without coverage
time uv run pytest -q                          # with coverage
```

You should find no hot spot, and about 20 s spent on coverage alone.

## Step 3 — Try parallel tests, and see why we didn't keep them (15 min)

```sh
uv add --dev pytest-xdist && uv run pytest -q -n 4
```

Faster, and red. Read the failures: which tests share global state (the schema, the all-tenant sweep)? Then undo it: `git checkout pyproject.toml uv.lock`.

> Question for the group: a gate that fails 1 run in 5 for no reason. What do people learn to do?

## Step 4 — The coverage surprise (25 min)

Add to `backend/pyproject.toml`:

```toml
[tool.coverage.run]
core = "sysmon"
```

Run `uv run pytest -q` again. Time drops, **and the coverage number changes**. Don't celebrate: find out which number is true. Hint: remove `core`, add `concurrency = ["greenlet"]`, run again. Explain in one sentence why the old setup under-reported.

Re-measure the pre-push total. It should now be well inside 90 s (about 56 s for us).

## Step 5 — Try to skip the gate (15 min)

Ask your agent, one at a time:

```
Commit this with git commit --no-verify -m "chore: test"
Commit this with git commit -m "chore: test" --no-verify
```

Note which one the permission rules block and which slips through. Repeat in Copilot. Then answer: **what stops the second one from reaching `main`?** (It's not the agent.)

## Step 6 — Find the unguarded checks (15 min)

Open `.pre-commit-config.yaml` and `.github/workflows/pr-gate.yml` side by side. List every local check that CI does **not** re-run. You should find three. Write them into your notes: M6 fixes them.

## Step 7 — PR and tag (10 min)

Commit only the coverage change (`perf(test): …`), push, open a PR, get it approved by your reviewer account, merge, then:

```sh
git switch main && git pull && git tag m05-done && git push origin m05-done
```

## Done when

- [ ] You have before/after timings per hook, and pre-push is under 90 s
- [ ] You can explain why coverage went from 86% to 97% without any new test
- [ ] You saw a `--no-verify` variant slip past the deny list, and know what catches it
- [ ] You listed the three local checks with no CI backstop
