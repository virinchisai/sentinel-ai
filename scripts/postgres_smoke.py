"""Run inside the API container against an isolated Compose database."""

import uuid
from backend.migrate import migrate
from backend.auth.models import User, Role, get_session_factory, get_engine
from backend.auth.workspaces import resolve_workspace
from backend.rag.documents import ingest_document, retrieve
from backend.config import settings
from sqlalchemy import text

migrate()
settings.embedding_model = ""
with get_session_factory()() as db:
    u = User(
        username="pg-" + uuid.uuid4().hex,
        email=uuid.uuid4().hex + "@test.invalid",
        hashed_password="!disabled",
        role=Role.USER,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    uid = u.id
wid = resolve_workspace(uid)
r = ingest_document(
    uid, wid, "postgres-test.txt", b"PostgreSQL evidence verification ORCHID"
)
assert retrieve("evidence verification", wid)[0]["document_id"] == r["id"]
assert not retrieve("evidence verification", "unrelated-workspace")
with get_engine().connect() as db:
    assert (
        db.execute(
            text(
                "SELECT count(*) FROM pg_indexes WHERE indexname in ('chunks_fts','chunks_semantic')"
            )
        ).scalar()
        == 2
    )
print("PostgreSQL migration, indexes, ingestion, retrieval, workspace isolation: PASS")
# Deterministic vectors verify the SQL vector path without downloading models in CI.
import backend.rag.documents as document_store

original_embed = document_store.embed
document_store.embed = lambda texts: [[1.0] + [0.0] * 767 for _ in texts]
try:
    semantic = ingest_document(
        uid, wid, "semantic.txt", b"An isolated semantic record."
    )
    hits = retrieve("lexically-unrelated-question", wid)
    assert any(h["document_id"] == semantic["id"] for h in hits)
    assert not retrieve("lexically-unrelated-question", "unrelated-workspace")
finally:
    document_store.embed = original_embed
print("PostgreSQL vector insertion, similarity retrieval, workspace isolation: PASS")
