from backend.rag.ingest import ingest
from backend.rag.retriever import retrieve


def test_retrieval_surfaces_relevant_doc(actor):
    ingest(
        user_id=actor.user_id, workspace_id=actor.workspace_id
    )  # idempotent: upsert by deterministic chunk ids
    results = retrieve(
        "How many days of paid time off do employees accrue?",
        workspace_id=actor.workspace_id,
    )
    assert results
    assert results[0]["source"] == "pto_policy.md"


def test_retrieval_respects_top_k(actor):
    ingest(user_id=actor.user_id, workspace_id=actor.workspace_id)
    results = retrieve("incident severity", top_k=2, workspace_id=actor.workspace_id)
    assert len(results) <= 2
