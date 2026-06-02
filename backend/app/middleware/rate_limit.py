import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.redis import redis_client

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json"):
            return await call_next(request)

        settings = get_settings()
        client_ip = request.client.host if request.client else "unknown"
        key = f"rate_limit:{client_ip}:{int(time.time()) // settings.rate_limit_window_seconds}"

        try:
            current = await redis_client.incr(key)
            if current == 1:
                await redis_client.expire(key, settings.rate_limit_window_seconds)
            if current > settings.rate_limit_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": {"code": "RATE_LIMIT", "message": "Rate limit exceeded"}},
                )
        except Exception:
            logger.warning("rate_limit_redis_unavailable")

        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = (time.perf_counter() - start) * 1000
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration, 2),
        )
        return response
