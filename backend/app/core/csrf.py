"""Double-submit-cookie CSRF protection (Section 15 "CSRF-Schutz bei
Cookie-basierter Auth").

SameSite=Lax on the session cookie already blocks the classic
cross-site form/fetch CSRF vector, but we add a belt-and-suspenders
double-submit token: `login` also sets a readable `csrf_cookie_name`
cookie, and every state-changing request must echo its value back in
the `csrf_header_name` header (only JavaScript running on our own
origin can read the cookie to do that).

Requests that don't carry a session cookie at all are left alone here:
there is no authenticated session to forge on their behalf, and this
also keeps route-level tests that bypass cookie auth via FastAPI
dependency overrides (`client_as` in `tests/conftest.py`) working
without needing to fake a whole CSRF handshake.
"""

from __future__ import annotations

import secrets

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings

_SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()

        if request.method in _SAFE_METHODS:
            return await call_next(request)

        session_cookie = request.cookies.get(settings.session_cookie_name)
        if not session_cookie:
            return await call_next(request)

        csrf_cookie = request.cookies.get(settings.csrf_cookie_name)
        csrf_header = request.headers.get(settings.csrf_header_name)
        if not csrf_cookie or not csrf_header or not secrets.compare_digest(
            csrf_cookie, csrf_header
        ):
            return JSONResponse(
                status_code=403, content={"detail": "CSRF token missing or invalid"}
            )

        return await call_next(request)
