# Architecture

```
                ┌─────────────────────┐
   HTTP /chat   │   FastAPI (api/)     │
  ────────────▶ │  bearer-token auth   │
                └──────────┬───────────┘
                           │
                ┌──────────▼───────────┐
                │  Orchestrator         │   agent/orchestrator.py
                │  (agent loop)         │   - sends messages+tools to LLM
                └──────────┬───────────┘   - executes tool calls via MCP
                           │               - loops until final answer
                ┌──────────▼───────────┐
                │  LLMProvider          │   agent/llm_provider.py
                │  Anthropic | OpenAI   │   provider-agnostic chat interface
                └──────────┬───────────┘
                           │ tool calls
                ┌──────────▼───────────┐
                │  MCP Client            │  agent/mcp_client.py
                │  (stdio transport)      │  discovers + invokes server tools
                └──────────┬───────────┘
                           │ MCP protocol
                ┌──────────▼───────────┐
                │  MCP Server             │  mcp_server/server.py
                │  bearer auth (HTTP mode)│  mcp_server/auth.py
                ├─────────────────────────┤
                │ system_tools (echo)     │
                │ github_tools ──────────▶│──▶ GitHub REST API
                │ rag_tools    ──────────▶│──▶ Chroma vector store (rag/)
                └─────────────────────────┘
```

## Why these choices

- **MCP for tool exposure**: tools are defined once as MCP primitives and are
  reusable by any MCP-compatible client (Claude Desktop, this agent, future
  agents), not hard-wired into the orchestrator.
- **Provider-agnostic LLM layer**: `LLMProvider` normalizes Anthropic's and
  OpenAI's different tool-calling formats into one `ChatResponse`/`ToolCall`
  shape so the orchestrator never branches on provider.
- **Local embeddings for RAG**: sentence-transformers runs the embedding step
  locally so retrieval works independent of which chat LLM provider is
  configured, and ingestion doesn't burn API tokens.
- **Two auth layers**: the MCP server's HTTP transport and the FastAPI `/chat`
  endpoint both check a bearer token, modeling how an internal tool server and
  a public-facing API would each need their own access control.
