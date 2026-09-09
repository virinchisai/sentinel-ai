"""Idempotent v1→v2 additive migration. Back up v1 databases before upgrading."""

from sqlalchemy import inspect, text
from backend.auth.models import get_engine, init_db


def migrate():
    engine = get_engine()
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        names = {c["name"] for c in inspector.get_columns("users")}
        if "token_version" not in names:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"
                    )
                )
    init_db()
    if engine.dialect.name == "postgresql":
        with engine.begin() as connection:
            connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            connection.execute(
                text("ALTER TABLE chunks ADD COLUMN IF NOT EXISTS semantic vector(768)")
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS chunks_fts ON chunks USING gin(to_tsvector('english', text))"
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS chunks_semantic ON chunks USING hnsw (semantic vector_cosine_ops)"
                )
            )


if __name__ == "__main__":
    migrate()
