"""FastAPI app exposing the agent over HTTP.

Run locally:
    uvicorn api.main:app --reload
"""

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from agent.orchestrator import Orchestrator
from config import settings

app = FastAPI(title="Enterprise AI Assistant")
orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, authorization: str | None = Header(default=None)) -> ChatResponse:
    expected = f"Bearer {settings.mcp_auth_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="unauthorized")

    reply = await orchestrator.chat(req.session_id, req.message)
    return ChatResponse(reply=reply, session_id=req.session_id)
