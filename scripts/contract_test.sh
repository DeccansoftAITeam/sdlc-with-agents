#!/usr/bin/env bash
# Contract fuzzing (Schemathesis): every generated request must get a non-5xx answer that
# matches the OpenAPI schema. Run from the repo root with the database migrated.
#
# Optional project hook: scripts/contract_seed.py prints a JSON object
#   {"headers": {"Authorization": "Bearer ..."}, "path": {"slug": "acme"}}
# so the fuzzer gets past authentication. Without it, only public endpoints are exercised.
set -euo pipefail
# A free port per run: a leftover server from an interrupted run can't be fuzzed by mistake.
port="${CONTRACT_PORT:-$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1])')}"
port="${port%$'\r'}"
base="http://127.0.0.1:${port}"
log="${TMPDIR:-/tmp}/contract-api.log"
if curl -fs "$base/healthz" >/dev/null 2>&1; then
  echo "Port $port is already serving an API: refusing to fuzz a server we didn't start (stale code)." >&2
  exit 2
fi

(cd backend && JWT_EPHEMERAL_KEY=true uv run uvicorn app.main:app --port "$port" >"$log" 2>&1) &
api=$!
trap 'kill $api 2>/dev/null || true' EXIT
for _ in $(seq 1 60); do curl -fs "$base/healthz" >/dev/null && break; sleep 1; done

args=(--checks not_a_server_error,status_code_conformance,response_schema_conformance
      --max-examples "${CONTRACT_MAX_EXAMPLES:-30}" --no-color)
if [ -f scripts/contract_seed.py ]; then
  seed="$(cd backend && uv run python ../scripts/contract_seed.py "$base")"
  # One "Name: value" per line; strip CR so it also works in Git Bash on Windows.
  while IFS= read -r header; do args+=(-H "$header"); done < <(python -c '
import json, sys
for k, v in json.loads(sys.argv[1]).get("headers", {}).items():
    print(f"{k}: {v}")' "$seed" | tr -d '\r')
  python -c '
import json, sys
print("[parameters]")
for k, v in json.loads(sys.argv[1]).get("path", {}).items():
    print(f"\"path.{k}\" = \"{v}\"")' "$seed" > schemathesis.toml
fi
status=0
PYTHONUTF8=1 uvx schemathesis@4 run "$base/openapi.json" "${args[@]}" || status=$?
rm -f schemathesis.toml
if [ "$status" -ne 0 ]; then echo "--- API log (last 60 lines) ---"; tail -60 "$log"; fi
exit "$status"
