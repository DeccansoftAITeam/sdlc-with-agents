#!/usr/bin/env sh
# Checks the course toolbox. Prints one line per tool.
for c in git gh python uv node pnpm docker az claude code; do
  if command -v "$c" >/dev/null 2>&1; then
    printf "%-8s %s\n" "$c" "$("$c" --version 2>/dev/null | grep -v WARNING | head -n 1)"
  else
    printf "%-8s MISSING\n" "$c"
  fi
done
