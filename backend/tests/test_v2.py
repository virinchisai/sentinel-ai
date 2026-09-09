from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.auth.models import get_session_factory, User, Role, Approval
from backend.auth.jwt import create_access_token
from backend.agents import memory
from backend.agents.planner import PLANNING_PROMPT
from backend.agents.policy import authorize
from backend.rag.documents import retrieve


@pytest.fixture
def client():
    with TestClient(app) as c:
        from backend.auth.routes import limiter

        limiter.reset()
        yield c


def headers(user):
    return {
        "Authorization": "Bearer "
        + create_access_token({"sub": user.username, "ver": user.token_version})
    }


def test_planner_formats_json():
    assert '"step"' in PLANNING_PROMPT.format(query="investigate")


def test_memory_preserves_native_messages():
    messages = [
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "abc", "function": {"name": "echo", "arguments": "{}"}}
            ],
        },
        {"role": "tool", "tool_call_id": "abc", "content": "ok"},
    ]
    for m in messages:
        memory.append("s", m)
    assert memory.get_history("s") == messages


def test_upload_rejects_path_and_size(client, user, monkeypatch):
    assert (
        client.post(
            "/documents/upload",
            headers=headers(user),
            files={"file": ("../escape.txt", b"bad")},
        ).status_code
        == 400
    )
    from backend.config import settings

    monkeypatch.setattr(settings, "max_upload_bytes", 3)
    assert (
        client.post(
            "/documents/upload",
            headers=headers(user),
            files={"file": ("x.txt", b"large")},
        ).status_code
        == 413
    )


def test_workspace_isolation_replacement_delete(client, user, actor):
    h = headers(user)
    first = client.post(
        "/documents/upload",
        headers=h,
        files={"file": ("policy.txt", b"Old policy code alpha")},
    ).json()
    second = client.post(
        "/documents/upload",
        headers=h,
        files={"file": ("policy.txt", b"New policy code beta")},
    ).json()
    assert second["version"] == 2 and second["id"] == first["id"]
    assert not retrieve("alpha", actor.workspace_id)
    with get_session_factory()() as db:
        other = User(
            username="other",
            email="other@example.com",
            hashed_password="x",
            role=Role.USER,
        )
        db.add(other)
        db.commit()
        db.refresh(other)
        h2 = headers(other)
    assert client.get("/documents/" + first["id"], headers=h2).status_code == 403
    assert client.get("/documents/list", headers=h2).json()["total_chunks"] == 0
    deleted = client.delete("/documents/" + first["id"], headers=h)
    assert deleted.status_code == 200
    assert not retrieve("beta", actor.workspace_id)


def test_viewer_cannot_execute_tools(actor, user):
    with get_session_factory()() as db:
        db.query(User).filter_by(id=user.id).update({"role": Role.VIEWER})
        db.commit()
    with pytest.raises(Exception):
        authorize(actor, "github_create_issue", {})
    with pytest.raises(Exception):
        authorize(actor, "db_query", {"sql": "SELECT 1"})
    authorize(actor, "query_knowledge_base", {"query": "policy"})


def test_no_blanket_approval(client, user):
    assert (
        client.post(
            "/chat",
            headers=headers(user),
            json={"message": "write", "auto_approve": True},
        ).status_code
        == 422
    )


def test_approval_reject_replay_and_wrong_owner(client, user, actor):
    with get_session_factory()() as db:
        db.add(
            Approval(
                id="a",
                user_id=user.id,
                workspace_id=actor.workspace_id,
                session_id="s",
                tool="echo",
                arguments='{"message":"ok"}',
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
            )
        )
        db.commit()
    assert (
        client.post(
            "/approvals/a", headers=headers(user), json={"approve": False}
        ).json()["status"]
        == "rejected"
    )
    assert (
        client.post(
            "/approvals/a", headers=headers(user), json={"approve": True}
        ).status_code
        == 409
    )


def test_refresh_rotation_logout(client):
    assert (
        client.post(
            "/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "StrongTest123!",
            },
        ).status_code
        == 201
    )
    tokens = client.post(
        "/auth/login", json={"username": "alice", "password": "StrongTest123!"}
    ).json()
    renewed = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert renewed.status_code == 200
    assert (
        client.post(
            "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        ).status_code
        == 401
    )
    h = {"Authorization": "Bearer " + renewed.json()["access_token"]}
    assert client.post("/auth/logout", headers=h).status_code == 204
    assert client.get("/auth/me", headers=h).status_code == 401
    assert (
        client.post(
            "/auth/refresh", json={"refresh_token": renewed.json()["refresh_token"]}
        ).status_code
        == 401
    )


def test_sql_rejects_stacked_and_select_into():
    from backend.mcp_server.connectors.database_client import DatabaseClient

    c = DatabaseClient()
    assert "error" in c.execute_query("SELECT 1; DROP TABLE employees")
    assert "error" in c.execute_query("SELECT * INTO stolen FROM employees")


def test_filesystem_blocks_sibling_prefix(tmp_path, monkeypatch):
    from backend.config import settings
    from backend.mcp_server.connectors.filesystem_client import FileSystemClient

    monkeypatch.setattr(settings, "workspace_dir", str(tmp_path / "safe"))
    with pytest.raises(PermissionError):
        FileSystemClient()._safe_path("../safe-escape/file")


def test_durable_ingestion_job(actor):
    from backend.rag.jobs import enqueue, process_one
    from backend.auth.models import DocumentJob

    job = enqueue(
        actor.user_id, actor.workspace_id, "queued.txt", b"Queue evidence durable"
    )
    assert process_one()
    with get_session_factory()() as db:
        row = db.get(DocumentJob, job["job_id"])
        assert row.status == "completed" and row.payload == ""
    assert retrieve("durable", actor.workspace_id)
