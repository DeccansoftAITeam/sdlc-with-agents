# Tasks: TD-008 AI triage

| Field | Value |
|---|---|
| Spec | ./spec.md |
| Design | ./design.md |
| Status | Draft: approved together with the spec and design |

## Task index

| Task ID | Title | Depends on | Mode | Risk tier | Status |
|---|---|---|---|---|---|
| T-008-01 | LLM adapter port + OrcaRouter, Anthropic, fake | — | M2 | **High** | Todo |
| T-008-02 | Migration + masking + budget | — | M2 | **High** | In review |
| T-008-03 | Triage job, worker loop, suggestion API | 01, 02 | M2 | **High** | Todo |
| T-008-04 | Golden set + eval runner | 01 | M1 | Medium | Todo |
| T-008-05 | Web: suggestion panel (AC-9) | 03 | M2 | Medium | Todo |

T-008-01 and T-008-02 can run in parallel (Claude Code on one, Copilot on the other).

## T-008-01: LLM adapter

**Files in scope:** `backend/app/adapters/llm/**`, `backend/app/core/config.py`, `backend/tests/adapters/**`, `backend/tests/architecture/test_rules.py`
**Done:** the two adapters pass the same contract tests against recorded responses (no network in tests); 10 s timeout; the key never appears in `repr` or logs; architecture test "only `app.features.ai` imports `app.adapters.llm`".

## T-008-02: Migration, masking, budget

**Files in scope:** `backend/migrations/versions/td008a_*.py`, `backend/app/features/ai/{models,masking,budget}.py`, `backend/tests/features/ai/test_{masking,budget}.py`
**Done:** AC-4 (masking property test), AC-6 (cap + rate), RLS on all three tables, squawk clean.

## T-008-03: Triage job and API

**Files in scope:** `backend/app/features/ai/{triage,router,schemas}.py`, `prompts/triage/v1.md`, `backend/app/features/tickets/{service,router,schemas}.py` (enqueue, `ai_suggestion` field, override recording), `backend/app/features/flags/service.py` (`ai-triage`), `backend/app/workers/main.py`, tests
**Done:** AC-1, 2, 3, 5, 7, 8, 10 green with the fake adapter; contract fuzzing clean; acceptance tests reviewed by a human before implementation.

## T-008-04: Evals

**Files in scope:** `evals/triage/**`
**Done:** 50 synthetic tickets with expected category and priority; `run.py` prints the four metrics and exits non-zero below the spec thresholds; a first real run recorded in the PR.

## T-008-05: Web suggestion panel

**Files in scope:** `apps/web/src/features/ticket/**`, `apps/web/src/app/tickets/**`, `apps/web/e2e/triage.spec.ts`, `scripts/e2e_seed.py`
**Done:** AC-9 E2E + axe; accept button applies the suggestion.
