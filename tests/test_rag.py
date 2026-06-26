from rag.ingest import ingest
from rag.retriever import retrieve


def test_retrieval_surfaces_relevant_doc():
    ingest()  # idempotent: upsert by deterministic chunk ids
    results = retrieve("How many days of paid time off do employees accrue?")
    assert results
    assert results[0]["source"] == "pto_policy.md"


def test_retrieval_respects_top_k():
    ingest()
    results = retrieve("incident severity", top_k=2)
    assert len(results) <= 2
