"""Reject NUL characters at the boundary, for every endpoint at once.

Postgres `text` can't store U+0000, so a NUL anywhere in a request (a company name, a
ticket body) used to reach the database and come back as a 500. Found by contract fuzzing
in M6. Valid JSON can carry NUL only as the escape `\\u0000`; URLs only as `%00`.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.errors import problem

JSON_NUL = b"\\u0000"


class RejectNul:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        if b"%00" in scope.get("query_string", b"") or "\x00" in scope.get("path", ""):
            await _reject(scope, receive, send)
            return
        body = b""
        more = True
        while more:  # buffer the body once, then replay it to the app unchanged
            message = await receive()
            body += message.get("body", b"")
            more = message.get("more_body", False)
        if JSON_NUL in body.lower():
            await _reject(scope, receive, send)
            return
        replayed = False

        async def replay() -> Message:
            nonlocal replayed
            if replayed:
                return await receive()
            replayed = True
            return {"type": "http.request", "body": body, "more_body": False}

        await self.app(scope, replay, send)


async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
    response = problem(422, "Invalid characters", "Text may not contain NUL (U+0000) characters.")
    await response(scope, receive, send)
