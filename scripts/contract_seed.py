#!/usr/bin/env python3
"""Project hook for scripts/contract_test.sh: create a throwaway tenant and an admin token so
Schemathesis can reach the authenticated endpoints. Prints {"headers": ..., "path": ...}.

Usage: contract_seed.py <base-url>   (synthetic data only, local or CI database)
"""
import json
import sys
import uuid

import httpx

base = sys.argv[1]
slug = f"contract-{uuid.uuid4().hex[:8]}"
password = "a-long-unique-passphrase"
with httpx.Client(base_url=base, timeout=30) as c:
    c.post(
        "/signup",
        json={"company_name": "Contract", "slug": slug, "admin_name": "Ada",
              "email": "ada@example.com", "password": password},
    ).raise_for_status()
    token = c.post(f"/t/{slug}/auth/login", json={"email": "ada@example.com", "password": password})
    token.raise_for_status()
print(json.dumps({"headers": {"Authorization": f"Bearer {token.json()['access_token']}"}, "path": {"slug": slug}}))
