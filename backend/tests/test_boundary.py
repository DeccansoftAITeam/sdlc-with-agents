"""Boundary rules every scaffolded API gets (scaffold v1.1, course M6 contract fuzzing)."""

import httpx


async def test_nul_in_query_is_422_problem(client: httpx.AsyncClient) -> None:
    r = await client.get("/healthz?x=a%00b")
    assert r.status_code == 422
    assert r.headers["content-type"].startswith("application/problem+json")


async def test_nul_in_json_body_is_rejected_before_routing(client: httpx.AsyncClient) -> None:
    r = await client.post(
        "/healthz", content=b'{"x": "a\u0000b"}', headers={"content-type": "application/json"}
    )
    assert r.status_code == 422  # not 405: the guard runs before any route


async def test_errors_are_documented_as_problem_details(client: httpx.AsyncClient) -> None:
    schema = (await client.get("/openapi.json")).json()
    for path in schema["paths"].values():
        for operation in path.values():
            assert "default" in operation["responses"]
