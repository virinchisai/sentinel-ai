"""Run inside the API container against an isolated Compose database."""

import uuid
from backend.migrate import migrate
from backend.auth.models import User, Role, get_session_factory, get_engine
from backend.auth.workspaces import resolve_workspace
import backend.rag.documents as document_store
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
r = document_store.ingest_document(
    uid, wid, "postgres-test.txt", b"PostgreSQL evidence verification ORCHID"
)
assert (
    document_store.retrieve("evidence verification", wid)[0]["document_id"] == r["id"]
)
assert not document_store.retrieve("evidence verification", "unrelated-workspace")
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
original_embed = document_store.embed
document_store.embed = lambda texts: [[1.0] + [0.0] * 767 for _ in texts]
try:
    semantic = document_store.ingest_document(
        uid, wid, "semantic.txt", b"An isolated semantic record."
    )
    hits = document_store.retrieve("lexically-unrelated-question", wid)
    assert any(h["document_id"] == semantic["id"] for h in hits)
    assert not document_store.retrieve(
        "lexically-unrelated-question", "unrelated-workspace"
    )
finally:
    document_store.embed = original_embed
print("PostgreSQL vector insertion, similarity retrieval, workspace isolation: PASS")
