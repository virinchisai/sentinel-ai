"""MCP tool exposing retrieval over the local knowledge base."""


def register(mcp):
    @mcp.tool()
    def query_knowledge_base(query: str, top_k: int = 3) -> list[dict]:
        """Search the enterprise knowledge base (ingested docs) for relevant passages."""
        from backend.rag.retriever import retrieve

        return retrieve(query, top_k=top_k)
