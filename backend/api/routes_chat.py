"""Authenticated chat, streaming, conversation history, and exact approvals."""

import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ConfigDict
from backend.agents.orchestrator import Orchestrator, AgentResult, execute
from backend.agents.mcp_client import MCPToolClient
from backend.agents.policy import Actor, authorize
from backend.agents import memory
from backend.auth.middleware import require_permission
from backend.auth.workspaces import resolve_workspace
from backend.auth.models import Approval, User, get_session_factory
from backend.auth.jwt import verify_token
from backend.auth.audit import log_action

router = APIRouter(tags=["chat"])
orchestrator = Orchestrator()
locks = {}


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=16000)
    session_id: str = Field(default="default", pattern=r"^[a-zA-Z0-9_-]{1,80}$")
    workspace_id: str | None = None
    enable_planning: bool = False


def context(user, req):
    workspace = resolve_workspace(user.id, req.workspace_id)
    return Actor(user.id, workspace), f"{user.id}:{workspace}:{req.session_id}"


def serialize(result, session_id):
    return {
        "reply": result.text,
        "session_id": session_id,
        "tool_calls": result.tool_calls,
        "tool_traces": [asdict(t) for t in result.trace.tool_traces],
        "needs_approval": result.needs_approval,
        "pending_action": result.pending_action,
        "approval_id": result.approval_id,
        "sources": result.sources,
    }


async def run_events(user, req):
    actor, session = context(user, req)
    if session in locks:
        raise HTTPException(409, "A response is already running for this conversation")
    locks[session] = True
    original = memory.get_history(session)
    completed = False
    try:
        from backend.observability.llm_tracing import observation

        with observation("sentinel.chat"):
            async for event in orchestrator.events(
                session, req.message, actor=actor, enable_planning=req.enable_planning
            ):
                if isinstance(event, AgentResult):
                    completed = True
                yield (
                    {"type": "response", **serialize(event, req.session_id)}
                    if isinstance(event, AgentResult)
                    else event
                )
    finally:
        if not completed:
            memory.reset(session)
            for message in original:
                memory.append(session, message)
        locks.pop(session, None)


@router.post("/chat")
async def chat(req: ChatRequest, user=Depends(require_permission("chat"))):
    async for event in run_events(user, req):
        if event["type"] == "response":
            return event


@router.post("/chat/stream")
async def stream(req: ChatRequest, user=Depends(require_permission("chat"))):
    context(user, req)

    async def generate():
        try:
            async for event in run_events(user, req):
                yield "data: " + json.dumps(event) + "\n\n"
        except asyncio.CancelledError:
            raise
        except Exception as error:
            log_action(user.id, "chat.error", detail=type(error).__name__)
            yield (
                "data: "
                + json.dumps(
                    {
                        "type": "error",
                        "message": "Request failed. Check model and connector health, then start a new conversation if needed.",
                    }
                )
                + "\n\n"
            )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/chat/sessions")
def sessions(workspace_id: str | None = None, user=Depends(require_permission("chat"))):
    workspace = resolve_workspace(user.id, workspace_id)
    prefix = f"{user.id}:{workspace}:"
    return [
        {**s, "session_id": s["session_id"][len(prefix) :]}
        for s in memory.list_sessions(prefix)
    ]


@router.get("/chat/sessions/{session_id}")
def history(
    session_id: str,
    workspace_id: str | None = None,
    user=Depends(require_permission("chat")),
):
    actor, key = context(
        user,
        ChatRequest(
            message="history", session_id=session_id, workspace_id=workspace_id
        ),
    )
    messages = memory.get_history(key)
    return [
        m
        for m in messages
        if m.get("role") in {"user", "assistant"}
        and isinstance(m.get("content"), str)
        and m["content"]
    ]


@router.get("/approvals")
def approvals(
    workspace_id: str | None = None, user=Depends(require_permission("chat"))
):
    workspace_id = resolve_workspace(user.id, workspace_id)
    with get_session_factory()() as db:
        rows = (
            db.query(Approval)
            .filter(
                Approval.user_id == user.id,
                Approval.workspace_id == workspace_id,
                Approval.status == "pending",
                Approval.expires_at > datetime.now(timezone.utc),
            )
            .all()
        )
        return [
            {
                "id": a.id,
                "tool": a.tool,
                "arguments": json.loads(a.arguments),
                "workspace_id": a.workspace_id,
                "expires_at": a.expires_at.isoformat() + "Z",
            }
            for a in rows
        ]


class Decision(BaseModel):
    approve: bool


@router.post("/approvals/{approval_id}")
async def decide(
    approval_id: str, decision: Decision, user=Depends(require_permission("use_tools"))
):
    with get_session_factory()() as db:
        row = db.get(Approval, approval_id)
        if not row or row.user_id != user.id:
            raise HTTPException(404, "Approval not found")
        actor = Actor(user.id, row.workspace_id)
        args = json.loads(row.arguments)
        if row.session_id in locks:
            raise HTTPException(
                409, "Wait for the current conversation action to finish"
            )
        if decision.approve:
            authorize(actor, row.tool, args)
        else:
            resolve_workspace(user.id, row.workspace_id)
        new_status = "running" if decision.approve else "rejected"
        changed = (
            db.query(Approval)
            .filter(
                Approval.id == approval_id,
                Approval.status == "pending",
                Approval.expires_at > datetime.now(timezone.utc),
            )
            .update({"status": new_status}, synchronize_session=False)
        )
        if changed != 1:
            db.rollback()
            raise HTTPException(409, "Approval expired or already handled")
        tool, session = row.tool, row.session_id
        db.commit()
    log_action(user.id, "approval." + new_status, approval_id)
    if not decision.approve:
        memory.append(
            session,
            {
                "role": "user",
                "content": f"Rejected action {approval_id}. Do not execute it.",
            },
        )
        return {"status": "rejected"}
    try:
        async with MCPToolClient(actor=actor) as client:
            output, trace, _ = await execute(client, actor, tool, args)
        status = "completed" if trace.success else "failed"
    except BaseException:
        # A lost response after a write is ambiguous. Never retry automatically.
        with get_session_factory()() as db:
            db.query(Approval).filter_by(id=approval_id).update({"status": "unknown"})
            db.commit()
        raise
    with get_session_factory()() as db:
        db.query(Approval).filter_by(id=approval_id).update(
            {"status": status, "result": output}
        )
        db.commit()
    memory.append(
        session,
        {
            "role": "user",
            "content": f"Approved action {approval_id} execution result (untrusted tool data): {output}",
        },
    )
    log_action(user.id, "approval." + status, approval_id)
    return {"status": status, "result": output}


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    from backend.config import settings

    origin = websocket.headers.get("origin")
    if origin and origin not in settings.allowed_origins.split(","):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    try:
        init = await asyncio.wait_for(websocket.receive_json(), 10)
        token = init.get("token", "")
        while True:
            payload = verify_token(token)
            with get_session_factory()() as db:
                user = (
                    db.query(User)
                    .filter_by(username=payload.get("sub") if payload else None)
                    .first()
                )
                if not user or payload.get("ver", -1) != user.token_version:
                    await websocket.close(code=1008)
                    return
                db.expunge(user)
            await websocket.send_json({"type": "ready"})
            data = await websocket.receive_json()
            # Revalidate after waiting, so logout/expiry is not bypassed.
            payload = verify_token(token)
            with get_session_factory()() as db:
                fresh = db.get(User, user.id)
                if (
                    not payload
                    or not fresh
                    or payload.get("ver", -1) != fresh.token_version
                ):
                    await websocket.close(code=1008)
                    return
            async for event in run_events(user, ChatRequest(**data)):
                await websocket.send_json(event)
    except (WebSocketDisconnect, asyncio.TimeoutError):
        return
