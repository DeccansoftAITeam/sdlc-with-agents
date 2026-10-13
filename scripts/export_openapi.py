#!/usr/bin/env python3
"""Write the backend's OpenAPI schema to a file without starting a server.

Usage (from backend/): uv run python ../scripts/export_openapi.py out.json
Used by the PR gate's breaking-change check (oasdiff, base vs head).
"""
import json
import os
import sys

os.environ.setdefault("JWT_EPHEMERAL_KEY", "true")  # schema export only; no tokens are signed
sys.path.insert(0, os.getcwd())

from app.main import create_app  # noqa: E402  (path set above)

with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(create_app().openapi(), f, indent=2, sort_keys=True)
