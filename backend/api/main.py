"""FastAPI gateway for SentinelAI.

Run locally:
    uvicorn backend.api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from backend.api.routes_admin import router as admin_router
from backend.api.routes_chat import router as chat_router
from backend.api.routes_documents import router as documents_router
from backend.auth.models import init_db
from backend.auth.routes import router as auth_router
from backend.observability.logging import setup_logging
from backend.observability.tracing import TracingMiddleware

setup_logging()
init_db()

app = FastAPI(
    title="SentinelAI",
    description="Secure Enterprise AI Workspace — MCP-powered agent platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TracingMiddleware)

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "sentinel-ai"}


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
