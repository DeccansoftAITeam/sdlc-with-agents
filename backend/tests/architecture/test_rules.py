"""Architecture tests: rules from 04-ARCHITECTURE-DECISIONS that code must obey.

Instructions guide; these enforce.
"""

import ast
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

APP = Path(__file__).resolve().parents[2] / "app"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def test_routers_do_not_touch_the_database_directly() -> None:
    """No business logic or SQL in routers: routers call services (AD: feature folders)."""
    offenders = [
        str(p.relative_to(APP))
        for p in APP.glob("features/*/router.py")
        if p.parent.name != "health" and any(m.startswith(("sqlalchemy", "asyncpg")) for m in _imports(p))
    ]
    assert offenders == []


def test_no_cloud_sdk_in_domain_code() -> None:
    """Cloud-neutral domain (constitution: flexibility). Adapters live in app/adapters/."""
    offenders = [
        str(p.relative_to(APP))
        for p in APP.rglob("*.py")
        if "adapters" not in p.parts
        and any(m.startswith(("azure", "boto3", "google.cloud")) for m in _imports(p))
    ]
    assert offenders == []


def test_no_file_over_1000_lines() -> None:
    assert [p.name for p in APP.rglob("*.py") if len(p.read_text(encoding="utf-8").splitlines()) > 1000] == []


async def test_every_tenant_table_has_forced_rls(owner_engine: AsyncEngine) -> None:
    """Any table with a tenant_id column must ENABLE + FORCE RLS (ADR multi-tenancy, TM-003)."""
    async with owner_engine.connect() as c:
        rows = (
            await c.execute(
                text("""
            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
            FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid AND a.attname = 'tenant_id' AND NOT a.attisdropped
            WHERE n.nspname = 'public' AND c.relkind = 'r' AND c.relname <> 'rls_probe'
        """)
            )
        ).all()
    missing = [r.relname for r in rows if not (r.relrowsecurity and r.relforcerowsecurity)]
    assert missing == [], f"tables with tenant_id but no forced RLS: {missing}"
