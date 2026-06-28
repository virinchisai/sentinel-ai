"""Chat route with JWT auth, WebSocket streaming support, and tool trace response."""

from __future__ import annotations

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.agents.orchestrator import Orchestrator
from backend.auth.jwt import verify_token
from backend.auth.models import User, get_session_factory
from backend.auth.middleware import require_permission
from backend.auth.rbac import has_permission

router = APIRouter(tags=["chat"])
orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    enable_planning: bool = True


class ToolTraceItem(BaseModel):
    tool_name: str
    arguments: dict
    result: str
    duration_ms: float
    success: bool


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    tool_calls: list[str]
    tool_traces: list[ToolTraceItem]
    needs_approval: bool
    pending_action: str


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest, current_user: User = Depends(require_permission("chat"))
) -> ChatResponse:
    result = await orchestrator.run(
        session_id=f"{current_user.id}-{req.session_id}",
        user_message=req.message,
        enable_planning=req.enable_planning,
        auto_approve=False,
    )
    return ChatResponse(
        reply=result.text,
        session_id=req.session_id,
        tool_calls=result.tool_calls,
        tool_traces=[
            ToolTraceItem(
                tool_name=t.tool_name,
                arguments=t.arguments,
                result=t.result,
                duration_ms=t.duration_ms,
                success=t.success,
            )
            for t in result.trace.tool_traces
        ],
        needs_approval=result.needs_approval,
        pending_action=result.pending_action,
    )


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()

    try:
        init_data = await websocket.receive_json()
        token = init_data.get("token", "")
        payload = verify_token(token)
        if not payload:
            await websocket.send_json({"error": "unauthorized"})
            await websocket.close()
            return

        from backend.auth.routes import is_revoked

        if is_revoked(token, payload):
            await websocket.send_json({"error": "token_revoked"})
            await websocket.close()
            return

        db = get_session_factory()()
        try:
            user = db.query(User).filter(User.username == payload.get("sub")).first()
        finally:
            db.close()

        if not user or not has_permission(user.role, "chat"):
            await websocket.send_json({"error": "forbidden"})
            await websocket.close()
            return

        session_id = f"{user.id}-ws-{init_data.get('session_id', 'default')}"
        await websocket.send_json({"type": "connected", "session_id": session_id})

        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            if not message:
                continue

            result = await orchestrator.run(
                session_id=session_id,
                user_message=message,
                enable_planning=data.get("enable_planning", True),
                auto_approve=False,
            )

            await websocket.send_json({
                "type": "response",
                "reply": result.text,
                "tool_calls": result.tool_calls,
                "needs_approval": result.needs_approval,
                "pending_action": result.pending_action,
            })

    except WebSocketDisconnect:
        pass
