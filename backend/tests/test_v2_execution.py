import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.auth.models import Approval, get_session_factory, User, Role
from backend.auth.jwt import create_access_token
from backend.agents.orchestrator import Orchestrator
from backend.agents.llm_provider import (
    ChatResponse,
    ToolCall,
)
from backend.connectors.credentials import save, connector_environment
from backend.agents import memory


class WriteProvider:
    def chat(self, messages, tools):
        return ChatResponse(
            text="",
            tool_calls=[
                ToolCall(
                    "call",
                    "github_create_issue",
                    {"title": "Review incident", "repo": "virinchisai/sentinel-ai"},
                )
            ],
        )

    def assistant_message(self, r):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call",
                    "type": "function",
                    "function": {"name": "github_create_issue", "arguments": "{}"},
                }
            ],
        }

    def tool_result_message(self, c, r):
        return {"role": "tool", "tool_call_id": c.id, "content": r}


@pytest.mark.asyncio
async def test_write_waits_for_exact_approval(actor, monkeypatch):
    from backend.config import settings

    monkeypatch.setattr(settings, "github_default_repo", "virinchisai/sentinel-ai")
    save(actor.user_id, "github", {"token": "test-only-not-a-real-token"})
    from backend.agents.mcp_client import MCPToolClient

    execute = AsyncMock(side_effect=AssertionError("Write must not execute"))
    monkeypatch.setattr(MCPToolClient, "call_tool", execute)
    r = await Orchestrator(WriteProvider()).run(
        "approval-session", "Create incident issue", actor=actor
    )
    assert r.needs_approval
    assert execute.await_count == 0
    with get_session_factory()() as db:
        a = db.get(Approval, r.approval_id)
        assert (
            a.status == "pending"
            and json.loads(a.arguments)["title"] == "Review incident"
        )
    assert memory.get_history("approval-session")[2]["tool_call_id"] == "call"


def test_approval_executes_once_and_owner_is_checked(actor, user, monkeypatch):
    from backend.agents.mcp_client import MCPToolClient

    run = AsyncMock(return_value="echo: approved")
    monkeypatch.setattr(MCPToolClient, "call_tool", run)
    with get_session_factory()() as db:
        db.add(
            Approval(
                id="execute",
                user_id=user.id,
                workspace_id=actor.workspace_id,
                session_id="s",
                tool="echo",
                arguments='{"message":"approved"}',
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        other = User(
            username="intruder",
            email="intruder@example.com",
            hashed_password="x",
            role=Role.USER,
        )
        db.add(other)
        db.commit()
    with TestClient(app) as c:
        h = lambda name: {
            "Authorization": "Bearer " + create_access_token({"sub": name, "ver": 0})
        }
        assert (
            c.post(
                "/approvals/execute", headers=h("intruder"), json={"approve": True}
            ).status_code
            == 404
        )
        assert (
            c.post(
                "/approvals/execute", headers=h(user.username), json={"approve": True}
            ).json()["status"]
            == "completed"
        )
        assert (
            c.post(
                "/approvals/execute", headers=h(user.username), json={"approve": True}
            ).status_code
            == 409
        )
    assert run.await_count == 1


def test_credentials_are_encrypted_and_user_scoped(actor):
    from backend.auth.models import ConnectorCredential

    save(actor.user_id, "github", {"token": "secret-test-value"})
    with get_session_factory()() as db:
        assert (
            "secret-test-value"
            not in db.get(ConnectorCredential, (actor.user_id, "github")).encrypted
        )
    assert connector_environment(actor.user_id)["GITHUB_TOKEN"] == "secret-test-value"
    assert connector_environment(999)["GITHUB_TOKEN"] == ""


def test_websocket_rejects_revoked_token(user):
    from starlette.websockets import WebSocketDisconnect

    token = create_access_token({"sub": user.username, "ver": user.token_version})
    with get_session_factory()() as db:
        db.query(User).filter_by(id=user.id).update({"token_version": 1})
        db.commit()
    with TestClient(app) as c:
        with c.websocket_connect("/ws/chat") as ws:
            ws.send_json({"token": token})
            with pytest.raises(WebSocketDisconnect):
                ws.receive_json()


def test_migration_preserves_v1_users(tmp_path, monkeypatch):
    from sqlalchemy import create_engine, text
    from backend.auth import models
    from backend.migrate import migrate

    engine = create_engine("sqlite:///" + str(tmp_path / "old.db"))
    with engine.begin() as db:
        db.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT)"))
        db.execute(text("INSERT INTO users VALUES(1,'original')"))
    monkeypatch.setattr(models, "_engine", engine)
    migrate()
    with engine.connect() as db:
        assert db.execute(text("SELECT username,token_version FROM users")).one() == (
            "original",
            0,
        )
