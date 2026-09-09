import asyncio
from backend.migrate import migrate
from backend.auth.models import User, Role, get_session_factory
from backend.auth.workspaces import resolve_workspace
from backend.agents.policy import Actor
from backend.agents.orchestrator import Orchestrator
from backend.rag.documents import ingest_document


async def main():
    migrate()
    with get_session_factory()() as db:
        user = db.query(User).filter_by(username="local-smoke").first()
        if not user:
            user = User(
                username="local-smoke",
                email="local-smoke@example.invalid",
                hashed_password="!disabled",
                role=Role.VIEWER,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        uid = user.id
    wid = resolve_workspace(uid)
    ingest_document(
        uid,
        wid,
        "verification.txt",
        b"# Release verification\nThe SentinelAI release verification code is ORCHID-2048.",
    )
    import uuid

    r = await Orchestrator().run(
        "smoke-" + str(uuid.uuid4()),
        "Search the knowledge base for the release verification code and quote it with its source.",
        actor=Actor(uid, wid),
    )
    print("Reply:", r.text)
    print("Tools:", r.tool_calls)
    assert "query_knowledge_base" in r.tool_calls
    assert "ORCHID-2048" in r.text
    assert r.sources[0]["source"] == "verification.txt"
    print("Local tool calling and source retrieval: PASS")


asyncio.run(main())
