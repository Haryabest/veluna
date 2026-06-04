from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import VelunaError
from app.core.logging import setup_logging
from app.middleware.rate_limit import RateLimitMiddleware, RequestLoggingMiddleware
from app.websocket.manager import websocket_chat_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.debug)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(RequestLoggingMiddleware)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(VelunaError)
async def veluna_exception_handler(_request, exc: VelunaError):
    status_map = {
        "NOT_FOUND": 404,
        "FORBIDDEN": 403,
        "INSUFFICIENT_BALANCE": 402,
        "RATE_LIMIT": 429,
        "SERVICE_UNAVAILABLE": 503,
    }
    return JSONResponse(
        status_code=status_map.get(exc.code, 400),
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy", "app": settings.app_name, "env": settings.app_env}


@app.websocket("/ws/chat/{chat_id}")
async def ws_chat(websocket: WebSocket, chat_id: str):
    await websocket_chat_handler(websocket, chat_id)
