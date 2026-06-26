"""Request tracing: propagates a unique request ID through the request lifecycle."""

from __future__ import annotations

import time
import uuid
from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from backend.observability.metrics import REQUEST_COUNT, REQUEST_LATENCY

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class TracingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        rid = request.headers.get("x-request-id", str(uuid.uuid4()))
        request_id_var.set(rid)

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=rid)

        start = time.monotonic()
        response = await call_next(request)
        elapsed = time.monotonic() - start

        endpoint = request.url.path
        REQUEST_COUNT.labels(
            method=request.method, endpoint=endpoint, status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(method=request.method, endpoint=endpoint).observe(elapsed)

        response.headers["x-request-id"] = rid
        return response
