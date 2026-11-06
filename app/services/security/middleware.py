import os
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.errors import body

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'",
}
LIMITED_PATHS = ("/api/v1/auth/login", "/api/v1/auth/register")


class LoginRateLimiter(BaseHTTPMiddleware):
    """At most N login/register attempts per minute per client IP (STRIDE: denial of service)."""

    def __init__(self, app):
        super().__init__(app)
        self.hits: dict[str, deque] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        if request.method == "POST" and request.url.path in LIMITED_PATHS:
            ip = request.client.host if request.client else "unknown"
            now = time.monotonic()
            window = self.hits[ip]
            while window and now - window[0] > 60:
                window.popleft()
            if len(window) >= settings.login_rate_per_minute:
                return JSONResponse(status_code=429, content=body("RATE_LIMITED", "Too many attempts. Wait a minute and try again."))
            window.append(now)
        return await call_next(request)


class SecurityHeaders(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("FORCE_HTTPS") == "1" and request.headers.get("x-forwarded-proto", request.url.scheme) == "http":
            return RedirectResponse(str(request.url.replace(scheme="https")), status_code=301)
        response = await call_next(request)
        for key, value in SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        if request.url.scheme == "https":
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return response
