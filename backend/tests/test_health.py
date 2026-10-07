import httpx
import pytest
from fastapi import FastAPI

from app.core import telemetry
from app.core.config import Settings
from app.core.errors import ProblemError


async def test_healthz(client: httpx.AsyncClient) -> None:
    r = await client.get("/healthz")
    assert r.status_code == 200 and r.json() == {"status": "ok"}


async def test_readyz_checks_db(client: httpx.AsyncClient) -> None:
    r = await client.get("/readyz")
    assert r.status_code == 200 and r.json()["db"] == "ok"


async def test_unknown_route_is_problem_json(client: httpx.AsyncClient) -> None:
    r = await client.get("/nope")
    assert r.status_code == 404
    assert r.headers["content-type"] == "application/problem+json"
    assert r.json()["status"] == 404


async def test_problem_error_rendered_without_internals() -> None:
    from app.main import create_app

    app = create_app()

    @app.get("/boom")
    async def boom() -> None:
        raise ProblemError(409, "Conflict", "Ticket is resolved")

    @app.get("/crash")
    async def crash() -> None:
        raise RuntimeError("secret internals")

    transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/boom")
        assert r.status_code == 409 and r.json()["detail"] == "Ticket is resolved"
        r = await c.get("/crash")
        assert r.status_code == 500 and "secret" not in r.text


async def test_validation_error_is_problem_json() -> None:
    from app.main import create_app

    app = create_app()

    @app.get("/n/{n}")
    async def n(n: int) -> int:
        return n

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        r = await c.get("/n/abc")
    assert r.status_code == 422 and r.json()["errors"]


@pytest.mark.parametrize("endpoint", [None, "http://collector:4318"])
def test_telemetry_install_is_safe(endpoint: str | None) -> None:
    telemetry.install(FastAPI(), Settings(otel_exporter_otlp_endpoint=endpoint))
