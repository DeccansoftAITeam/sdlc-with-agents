#!/usr/bin/env bash
# Lint only the NEW Alembic revisions (vs the base branch) with squawk: no locking DDL.
# Renders `alembic upgrade <from>:head --sql` as the standard prescribes; Alembic's own
# alembic_version bookkeeping DDL is removed before linting (it is not our schema).
set -euo pipefail
base="${BASE_REF:-origin/main}"
git rev-parse -q --verify "$base" >/dev/null || base=main
new=$(git diff --name-only --diff-filter=A "$base"...HEAD -- backend/migrations/versions 2>/dev/null || true)
[ -z "$new" ] && { echo "no new migrations"; exit 0; }
cd backend
# <from> = down_revision of the oldest new revision; none means the first migration.
from=$(cd .. && python - $new <<'PY'
import re, sys
downs = {}
for f in sys.argv[1:]:
    text = open(f, encoding="utf-8").read()
    rev = re.search(r"^revision[^=]*=\s*['\"]([^'\"]+)", text, re.M).group(1)
    down = re.search(r"^down_revision[^=]*=\s*['\"]?([^'\"\s]+)", text, re.M).group(1)
    downs[rev] = down
new = set(downs)
oldest = [d for d in downs.values() if d not in new]
print("" if not oldest or oldest[0] == "None" else oldest[0])
PY
)
range="${from:+$from:}head"
out="$(mktemp -d)/migrations.sql"
uv run alembic upgrade "$range" --sql 2>/dev/null | python -c "
import re, sys
s = sys.stdin.read()
print(re.sub(r'(CREATE TABLE|INSERT INTO|UPDATE) alembic_version.*?;\s*', '', s, flags=re.S))
" > "$out"
npx --yes squawk-cli@2 --config ../.squawk.toml "$out"
