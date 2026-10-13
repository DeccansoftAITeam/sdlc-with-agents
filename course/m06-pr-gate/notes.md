# M6 — The PR gate and review (P5–P7)

**Goal:** make CI the place where nothing can be skipped, add the checks that are too slow for a laptop, and see what they find in code that already "passed".

> 🎩 **Developer**, **Platform Owner** and **Reviewer**. You change the gate through a scaffold release, fix what it finds, and ship the first web page behind an E2E test.

## 1. The gate, v2

The workflow is a Platform-owned file: agents can't edit it, and projects receive it through `copier update` from a tagged scaffold release.

| Job | Checks | New in v1.1/v1.2 |
|---|---|---|
| `hygiene` | pre-commit (all files), file length | public-env check, **PR title** (it becomes the squash commit), **agent attribution** trailers on `agent/*` branches |
| `backend` | ruff, mypy strict, tests + coverage + architecture | **squawk**, **contract fuzzing** (Schemathesis), **breaking-change check** (oasdiff, base vs head) |
| `security` | — | **semgrep** (Python + OWASP Top 10), **pip-audit**, **pnpm audit** (high+) |
| `e2e` | — | **Playwright smoke + axe** against the real API, Postgres and a production web build |
| `web` | typecheck, unit tests | — |

All three local-only checks from M5 now have a CI backstop. Budget: the whole gate stays **under 10 minutes**. Ours runs in about 2.

## 2. What contract fuzzing found in code that already passed

Schemathesis reads `openapi.json`, generates thousands of requests, and checks that every response is not a 5xx and matches the documented schema. TicketDesk had 218 green tests at 97% coverage. Fuzzing found:

| # | Finding | Fix |
|---|---|---|
| 1 | An odd timezone string → `ZoneInfo` raised `OSError` → **500** | Check against an IANA-name pattern first, then catch `OSError` |
| 2 | A NUL (`\u0000`) in any text field → Postgres rejected it → **500** (company name at signup, ticket body…) | One boundary middleware, `RejectNul`, returns 422 for every endpoint |
| 3 | Error responses missing from OpenAPI, and the 422 schema didn't match the RFC 7807 body | Problem documented as the `default` response |
| 4 | `GET /tickets/` silently redirected to the ticket list | `redirect_slashes=False`: it's a 404 |
| 5 | SLA schedule times declared as OpenAPI `time` (with offset); the server sends local times | `HH:MM[:SS]` string with a pattern |
| 6 | A ticket number beyond BIGINT → asyncpg overflow → **500** | Path parameter bounded to `1..2^63-1` |

Every fix shipped with a regression test that fails without it (org rules §4).

**Finding 6 only appeared on GitHub.** The fuzzer is random. Two local runs passed; the first CI run tried `339480193592603374782513152`. Lesson: a passing fuzz run says "nothing found this time", not "nothing there". That's why it runs on every PR, not once.

## 3. Breaking changes are a decision, not an accident

oasdiff compares the base branch's OpenAPI with the PR's. Fixes 5 and 6 made the API **stricter**, and oasdiff flagged 12 breaking changes. That's correct: a client sending `09:00+02:00` would now get a 422.

The way through is reviewed, not silent:
1. Add the `api-breaking-approved` label. The step becomes report-only and prints a warning.
2. Explain the break in the PR description (here: no client uses the API yet, and the old format never matched what the server sent).
3. A code owner approves. A label alone changes nothing; the ruleset still requires that approval.

## 4. The gate tested itself, and failed twice

Scaffold v1.1.0 was verified on a freshly generated project (tests and contract test) before release. Its first real run still failed:

- A template test was 113 characters wide, so every new project failed its **own** lint on the first commit. The check had run tests, not hooks.
- `setup-node@v5` auto-caches the package manager named in `package.json`. The backend job has no pnpm, so it died during setup.

Both were fixed in v1.1.1, verified this time with the full pre-commit suite and `actionlint`. A gate is code. It needs the same review and the same "does it actually run?" check as anything else.

## 5. The first web page, acceptance-first

T-007-04 (TD-007/AC-3, AC-9): a login page and a queue that shows a breach badge.

- **AC-9 says "a text label, not colour alone".** `breachLabel()` returns "First response breached 2h ago", a pure function with a unit test.
- **The Playwright test came first** and was run red: the breach-active ticket is first and carries the badge, and the calm one has none. The unit test covers hiding the badge once a breach is no longer active (AC-12, AC-14). Removing the badge from the page makes the E2E test fail: a test you've never seen fail proves nothing.
- **axe** runs inside the same test. The gate blocks on serious or critical WCAG 2 A/AA issues.
- The E2E test runs against `next build && next start`, not `next dev`. The Next 16 dev server blocks its hydration resources on `127.0.0.1`, so the page rendered but never became interactive. A production build is also what users get.
- **Seed data** comes from `scripts/e2e_seed.py`: a fresh tenant and a random password per run. Nothing is shared between runs.

**Generated files are data.** `next build` wrote `apps/web/AGENTS.md`, a file of instructions for coding agents. Instructions for agents come only from the project-owned `AGENTS.md` (org rules §7). It's gitignored and flagged to the Tech Lead.

## 6. Review: gates first, then agents, then a human (P6–P7)

1. **Gates.** Nobody reads a PR whose checks are red.
2. **Agent review passes.** The `code-reviewer` subagent (read-only, isolated context) and, for auth, input handling or anything tenant-related, `security-reviewer`. Their findings are suggestions; the author answers each with a fix or a reason.
3. **A human code owner** approves and merges. The prompting human can't be the sole approver, and agents never approve (org rules §1, §9).

GitHub only counts a review that is **submitted**: choosing "Approve" in the dialog does nothing until you press "Submit review". And a reviewer needs write access to the repo, or their approval is just a comment.

## 7. Deferred

- **Preview environments** (one Container Apps environment per PR): they cost money, so they wait for the Azure go-ahead.
- **Mutation testing, DAST, AI evals**: too slow for every PR. Nightly, in M8.

**Next:** [lab.md](lab.md)
