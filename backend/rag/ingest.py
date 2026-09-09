"""Explicitly ingest sample documents into a user's workspace."""

from pathlib import Path
from backend.auth.workspaces import resolve_workspace
from backend.rag.documents import ingest_document

DOCS_DIR = Path(__file__).parent / "sample_docs"


def ingest(docs_dir=None, user_id=None, workspace_id=None):
    if user_id is None:
        raise ValueError("user_id is required for workspace-scoped ingestion")
    workspace_id = resolve_workspace(user_id, workspace_id)
    return sum(
        ingest_document(user_id, workspace_id, p.name, p.read_bytes())["chunks"]
        for p in sorted((docs_dir or DOCS_DIR).iterdir())
        if p.suffix.lower() in {".md", ".txt", ".pdf"}
    )


if __name__ == "__main__":
    import argparse
    from backend.migrate import migrate

    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    parser.add_argument("--workspace-id")
    parser.add_argument("--path", type=Path)
    args = parser.parse_args()
    migrate()
    print(ingest(args.path, args.user_id, args.workspace_id))
