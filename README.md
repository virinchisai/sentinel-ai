# Enterprise AI Assistant (MCP-based)

A reference implementation of an MCP-based enterprise AI assistant, demonstrating:

- **Model Context Protocol (MCP)** — tools exposed as MCP primitives via a FastMCP server
- **Tool calling** — provider-agnostic agent loop (Anthropic or OpenAI)
- **Authentication** — bearer-token auth on both the MCP server and the API layer
- **Enterprise connector** — GitHub (search issues/code, create issues, comment)
- **Agent workflows** — multi-turn tool-calling loop via `agent/orchestrator.py`
- **RAG** — local Chroma vector store over sample HR/eng policy docs
- **Evaluation** — a small eval dataset scored for tool-call correctness + keyword coverage
- **Deployment** — Docker, docker-compose, and a Fly.io config

See [`docs/architecture.md`](docs/architecture.md) for a diagram and rationale.

## Project layout

```
mcp_server/   MCP server: tools (system/github/rag), auth middleware, GitHub connector
agent/        LLMProvider abstraction, MCP client, orchestrator (agent loop), memory
rag/          Chroma store, ingest script, retriever, sample enterprise docs
api/          FastAPI app exposing POST /chat and GET /health
eval/         Eval dataset + runner + report
tests/        pytest suite (MCP tools, RAG retrieval, orchestrator agent loop)
deploy/       Dockerfile, docker-compose.yml, fly.toml
```

## Setup

Requires Python 3.11+.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in ANTHROPIC_API_KEY or OPENAI_API_KEY, GITHUB_TOKEN
```

Ingest the sample knowledge base:

```bash
python -m rag.ingest
```

## Run locally

```bash
uvicorn api.main:app --reload
```

```bash
curl -X POST http://localhost:8000/chat \
  -H "Authorization: Bearer dev-secret-change-me" \
  -H "Content-Type: application/json" \
  -d '{"message": "How many PTO days do I get per year?"}'
```

## Run tests

```bash
pytest
```

Covers: MCP tool round-trips over stdio, RAG retrieval relevance, and the
orchestrator's tool-calling loop against a fake LLM provider (no API key
needed for tests).

## Run the eval harness

Requires a real `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in `.env`, since this
exercises the live agent loop end-to-end:

```bash
python -m eval.run_eval
```

Scores each prompt in `eval/dataset.jsonl` on (1) whether the expected tool
was invoked, and (2) whether the final answer contains the expected
keywords. Results are written to `eval/results/latest.json` and printed as a
table.

## Docker

```bash
docker compose -f deploy/docker-compose.yml up --build
```

Or with Fly.io (from the project root):

```bash
fly launch --copy-config --dockerfile deploy/Dockerfile
fly secrets set ANTHROPIC_API_KEY=... GITHUB_TOKEN=... MCP_AUTH_TOKEN=...
fly deploy --config deploy/fly.toml
```

## Notes

- The GitHub connector defaults to a public demo repo (`octocat/Hello-World`)
  so it works without write access; pass `repo=` explicitly to target another
  repository (a `GITHUB_TOKEN` with appropriate scopes is required for write
  operations like creating issues/comments).
- The MCP client launches the MCP server as a subprocess over stdio per
  request; for higher-throughput deployments, switch to the server's
  `streamable-http` transport (`mcp_server/server.py --http`) and keep a
  persistent client connection instead.
