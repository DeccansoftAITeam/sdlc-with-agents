#!/usr/bin/env python3
"""Seed for the web E2E smoke (apps/web/e2e): a desk with one breach-active ticket and one calm one.

Usage (from backend/, API running, database migrated):
    uv run python ../scripts/e2e_seed.py <api-base-url>
Prints one line `E2E_SEED={"slug", "email", "password", "breached", "calm"}`. Synthetic data only.
"""

import asyncio
import json
import os
import secrets
import sys
import uuid

import httpx
from sqlalchemy import text

PASSWORD = secrets.token_urlsafe(16)  # fresh per run; printed for the E2E test to log in with


async def main(base: str) -> None:
    sys.path.insert(0, os.getcwd())  # run from backend/, so `app` is importable
    from app.core.db import tenant_session
    from app.core.security import resolve_tenant
    from app.features.sla.sweep import sweep

    slug, email = f"e2e-{uuid.uuid4().hex[:8]}", "ada@example.com"
    async with httpx.AsyncClient(base_url=base, timeout=30) as c:
        signup = {"company_name": "E2E", "slug": slug, "admin_name": "Ada", "email": email}
        signup["password"] = PASSWORD
        (await c.post("/signup", json=signup)).raise_for_status()
        login = await c.post(f"/t/{slug}/auth/login", json={"email": email, "password": PASSWORD})
        login.raise_for_status()
        token = login.json()["access_token"]
        admin = {"Authorization": f"Bearer {token}"}
        reg = {"name": "Cara", "email": "cara@example.com", "password": PASSWORD}
        (cust := await c.post(f"/t/{slug}/auth/register", json=reg)).raise_for_status()
        flag = await c.put(f"/t/{slug}/flags/sla-breach-escalation", headers=admin, json={"enabled": True})
        flag.raise_for_status()
        numbers = []
        for subject in ("Printer on fire", "Password question"):
            body = {"subject": subject, "body": "Help", "requester_id": cust.json()["id"]}
            (r := await c.post(f"/t/{slug}/tickets", headers=admin, json=body)).raise_for_status()
            numbers.append(r.json()["number"])
    breached, calm = numbers
    tenant_id = await resolve_tenant(slug)
    async with tenant_session(tenant_id) as s:  # as if the first-response deadline had passed
        await s.execute(
            text("UPDATE tickets SET first_response_due_at = now() - interval '2 hours' WHERE number = :n"),
            {"n": breached},
        )
    await sweep()
    seed = {"slug": slug, "email": email, "password": PASSWORD, "breached": breached, "calm": calm}
    print("E2E_SEED=" + json.dumps(seed))  # prefixed: other stdout lines can't be mistaken for it


asyncio.run(main(sys.argv[1]))
