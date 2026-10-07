#!/usr/bin/env bash
# Render changed Alembic revisions to SQL and lint with squawk (no locking DDL).
set -euo pipefail
cd backend
base="${BASE_REF:-origin/main}"
git rev-parse -q --verify "$base" >/dev/null || base=main
changed=$(git diff --name-only --diff-filter=A "$base"...HEAD -- migrations/versions 2>/dev/null || true)
[ -z "$changed" ] && { echo "no new migrations"; exit 0; }
uv run alembic upgrade head --sql > /tmp/migrations.sql
npx --yes squawk-cli@2 /tmp/migrations.sql
