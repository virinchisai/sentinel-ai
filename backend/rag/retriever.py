from backend.rag.documents import retrieve as _retrieve


def retrieve(query_text, top_k=3, workspace_id=None):
    if not workspace_id:
        raise ValueError("workspace_id is required")
    return _retrieve(query_text, workspace_id, top_k)
