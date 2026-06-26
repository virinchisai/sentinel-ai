# SentinelAI — Secure Enterprise AI Workspace

> A self-hostable AI agent platform that securely connects employees to their internal knowledge, source code, email, calendar, and operational tools — built on the **Model Context Protocol (MCP)**.

![tests](https://github.com/akarshanamachanpally/sentinel-ai/actions/workflows/test.yml/badge.svg)
![python](https://img.shields.io/badge/python-3.11%2B-blue)
![next](https://img.shields.io/badge/next.js-14-black)
![license](https://img.shields.io/badge/license-MIT-green)

---

## What is SentinelAI?

Imagine one chat interface where an employee asks *"Did anyone email about last week's incident, and is there a related GitHub issue?"* — and the AI agent figures out which internal tools to query (Gmail + GitHub), runs them in parallel, and returns a single grounded answer with citations.

That's SentinelAI. It's not a ChatGPT wrapper — it's the AI platform layer that companies actually need: one agent, your data, your auth, your audit trail.

## Architecture

```
                    User
                     │
                     ▼
              Next.js Frontend
                     │
                     ▼
               FastAPI Gateway
                     │
      ┌──────────────┼───────────────┐
      ▼              ▼               ▼
 Authentication     RAG          Agent Engine
 (JWT/RBAC)     (PGVector)       (Planner)
      │              │               │
      └──────────────┼───────────────┘
                     ▼
                MCP Server
                     │
 ┌─────────┬─────────┬─────────┬─────────┐
 ▼         ▼         ▼         ▼         ▼
GitHub   Gmail   Calendar   Files    PostgreSQL
```

## Features

### Core AI
- Conversational enterprise assistant with multi-turn memory (SQLite-backed, session-isolated)
- RAG over enterprise documents (Markdown + PDF) with smart heading-aware chunking
- Citations on every retrieved answer
- Provider-agnostic LLM layer (swap Anthropic ↔ OpenAI via env var)
- Multi-step planning: decomposes complex queries into sub-tasks

### MCP Connectors (18 tools across 7 servers)
| Connector | Tools |
|---|---|
| **GitHub** | search_issues, create_issue, comment_on_issue, search_code |
| **Gmail** | search, get_thread, draft_reply |
| **Calendar** | list_events, create_event, check_availability |
| **File System** | list_files, read_file, search (sandboxed) |
| **PostgreSQL** | query (read-only SELECT), describe_schema |
| **Knowledge Base** | query_knowledge_base (RAG) |
| **System** | echo, current_time |

### Security
- JWT-based authentication with access + refresh tokens
- Role-based access control (admin / user / viewer)
- Bcrypt password hashing
- Audit log of every authenticated action
- Sandboxed file system access (prevents directory escape)
- Read-only enforcement on database queries
- Human-approval gate on destructive actions (create_issue, send_email)

### Agentic
- Tool calling with retry + exponential backoff on failure
- Structured tool-call traces for every conversation
- Pluggable LLM provider abstraction
- Stateless or stateful operation

### Enterprise
- Document ingestion (Markdown, PDF, plain text)
- Semantic search via sentence-transformers + Chroma/PGVector
- Document versioning by content hash
- Connector mock-mode for demos without real OAuth

### Observability
- Structured JSON logging (structlog)
- Prometheus metrics: request latency, tool call counts, LLM latency, RAG queries, auth events
- Request ID propagation for distributed tracing
- `/metrics` endpoint ready for Prometheus scraping

### Evaluation
- Eval dataset with expected tool calls and golden answers
- Tool-call correctness scoring
- Keyword grounding metrics
- LLM-as-judge for answer quality

### Deployment
- Docker images for backend + frontend
- Docker Compose for full local stack (Postgres + pgvector + Prometheus + Grafana)
- Kubernetes manifests for production deploy
- GitHub Actions CI runs tests on every push

## Quick Start

### 1. Clone & install
```bash
git clone https://github.com/akarshanamachanpally/sentinel-ai.git
cd sentinel-ai
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cd frontend && npm install && cd ..
```

### 2. Configure
```bash
cp .env.example .env
# edit .env: add ANTHROPIC_API_KEY or OPENAI_API_KEY
```

### 3. Ingest sample knowledge base
```bash
python -m backend.rag.ingest
```

### 4. Run
```bash
# terminal 1: backend
uvicorn backend.api.main:app --reload

# terminal 2: frontend
cd frontend && npm run dev
```

Visit **http://localhost:3000**, register an account, and start chatting.

## Repository Tour

```
sentinel-ai/
├── backend/
│   ├── api/             # FastAPI gateway: chat, auth, documents, admin routes
│   ├── auth/            # JWT, RBAC, bcrypt, audit log (SQLAlchemy)
│   ├── agents/          # LLM provider abstraction, MCP client, orchestrator, planner
│   ├── rag/             # Chunking, PDF parsing, Chroma / PGVector stores, retriever
│   ├── mcp_server/      # FastMCP server with 18 tools across 7 connectors
│   ├── observability/   # structlog, Prometheus metrics, request tracing
│   └── tests/           # pytest suite
├── frontend/            # Next.js 14 + Tailwind: login, chat, documents, settings
├── evaluation/          # Eval dataset, runner, report
├── docker/              # Dockerfile.backend, Dockerfile.frontend, docker-compose.yml
├── kubernetes/          # Production K8s manifests
└── .github/workflows/   # CI runs pytest + Next.js build on every push
```

## Testing

### Local
```bash
pytest backend/tests -v       # backend
cd frontend && npm run build  # frontend
```

### On GitHub
Every push and PR triggers `.github/workflows/test.yml`, which runs:
- Backend pytest on Python 3.11 and 3.12
- MCP server smoke test (verifies all 18 tools register)
- Frontend lint + production build

You can also click **"Run workflow"** from the [Actions tab](../../actions) to trigger a manual run.

## Production Deployment

```bash
docker compose -f docker/docker-compose.yml up
```

Boots the full stack: Postgres+pgvector, FastAPI backend, Next.js frontend, Prometheus, and Grafana with pre-provisioned dashboards.

For Kubernetes, apply `kubernetes/*.yaml`.

## Why this matters

Most "AI app" portfolio projects are thin ChatGPT wrappers. SentinelAI is the entire enterprise AI platform stack — auth, RBAC, multi-tool agents, RAG with citations, observability, evaluation, deployment — built on the modern protocol (MCP) that Anthropic, OpenAI, and the broader ecosystem are converging on. It demonstrates the full skill set required for **Applied AI Engineering**, **AI Platform Engineering**, and **Forward-Deployed Engineering** roles at frontier AI companies.

## License
MIT
