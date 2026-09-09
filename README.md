<div align="center">

# 🛡️ SentinelAI

### Secure Enterprise AI Workspace

*A self-hostable AI agent platform that securely connects employees to their internal knowledge, source code, email, calendar, and operational tools — built on the **Model Context Protocol (MCP)**.*

<br>

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/virinchisai/sentinel-ai)

<br>

![tests](https://github.com/virinchisai/sentinel-ai/actions/workflows/test.yml/badge.svg)
![codeql](https://github.com/virinchisai/sentinel-ai/actions/workflows/codeql.yml/badge.svg)
![knowledge reliability](https://github.com/virinchisai/sentinel-ai/actions/workflows/knowledge-reliability.yml/badge.svg)
![last commit](https://img.shields.io/github/last-commit/virinchisai/sentinel-ai?color=22c55e)
![code size](https://img.shields.io/github/languages/code-size/virinchisai/sentinel-ai?color=blue)
![top language](https://img.shields.io/github/languages/top/virinchisai/sentinel-ai)
![stars](https://img.shields.io/github/stars/virinchisai/sentinel-ai?style=social)

![python](https://img.shields.io/badge/python-3.12-3776AB?logo=python&logoColor=white)
![next](https://img.shields.io/badge/Next.js-14-000000?logo=nextdotjs)
![fastapi](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![mcp](https://img.shields.io/badge/MCP-1.2-orange)
![tailwind](https://img.shields.io/badge/Tailwind-3-38BDF8?logo=tailwindcss&logoColor=white)
![docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![k8s](https://img.shields.io/badge/Kubernetes-326CE5?logo=kubernetes&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-green)

[**Live Demo (Codespaces)**](https://codespaces.new/virinchisai/sentinel-ai) · [**Architecture**](#-architecture) · [**Features**](#-features) · [**Quick Start**](#-quick-start) · [**Security**](#-security) · [**SECURITY.md**](SECURITY.md)

</div>

---

## 🚀 Try it in 30 seconds — no install needed

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/virinchisai/sentinel-ai)

Click the badge → wait ~30 sec for setup → frontend opens automatically. Log in with **`alice`** / **`sentinel-demo`**.

> Codespaces gives you a full cloud VS Code with both servers running and ports forwarded. Free 60 hours/month on personal GitHub accounts.

<details>
<summary><b>📸 Click to preview what you'll see</b></summary>

| Page | Description |
|---|---|
| 🔐 Login | JWT-secured sign-in with bcrypt password verification |
| 💬 Chat | Multi-turn conversation, agent tool calls visualized in real time |
| 📄 Documents | Drag-and-drop ingestion into the RAG knowledge base |
| ⚙️ Settings | Live status of every MCP connector (live / mock / demo) |
| 🔍 Tool Trace | Expand any agent response to see *exactly* which tools fired, with arguments + results + latency |

</details>

---

## 💡 What is SentinelAI?

Imagine one chat interface where an employee asks *"Did anyone email about last week's incident, and is there a related GitHub issue?"* — and the AI agent figures out which internal tools to query (Gmail + GitHub), runs them in parallel, and returns a single grounded answer with citations.

That's SentinelAI. It's not a ChatGPT wrapper — it's the AI platform layer that companies actually need: **one agent, your data, your auth, your audit trail**.

### Why MCP?

The [Model Context Protocol](https://modelcontextprotocol.io/) is the emerging standard for plugging tools into AI agents. Build a Gmail tool once as an MCP server and it works in Claude Desktop, Cursor, SentinelAI, and any future MCP-aware client. Without MCP, every integration is custom glue. With MCP, **build once, use everywhere**.

---

## 🏗️ Architecture

```mermaid
flowchart TD
    User([👤 User])
    UI[Next.js 14 Frontend<br/>Tailwind + shadcn/ui]
    API[FastAPI Gateway<br/>JWT + CORS + Rate Limit]
    Auth[Auth Layer<br/>JWT • RBAC • Bcrypt • Audit Log]
    RAG[RAG Engine<br/>Chroma / PGVector + Citations]
    Agent[Agent Orchestrator<br/>Planner • Retry • Tool Traces]
    LLM[(LLM Provider<br/>Anthropic / OpenAI)]
    MCP[MCP Server<br/>FastMCP]

    GitHub[GitHub<br/>4 tools]
    Gmail[Gmail<br/>3 tools]
    Cal[Calendar<br/>3 tools]
    FS[File System<br/>3 tools]
    DB[(PostgreSQL<br/>2 tools)]
    KB[Knowledge Base<br/>RAG tool]

    User --> UI
    UI --> API
    API --> Auth
    API --> RAG
    API --> Agent
    Agent --> LLM
    Agent --> MCP
    MCP --> GitHub
    MCP --> Gmail
    MCP --> Cal
    MCP --> FS
    MCP --> DB
    MCP --> KB
    RAG --> KB

    classDef gateway fill:#3b82f6,stroke:#1e40af,color:#fff
    classDef security fill:#ef4444,stroke:#991b1b,color:#fff
    classDef ai fill:#8b5cf6,stroke:#5b21b6,color:#fff
    classDef tool fill:#22c55e,stroke:#15803d,color:#fff
    class API,UI gateway
    class Auth security
    class Agent,RAG,LLM,MCP ai
    class GitHub,Gmail,Cal,FS,DB,KB tool
```

## ✨ Features

<details open>
<summary><b>Core AI</b> — Click to expand each section</summary>

### Core AI
- Conversational enterprise assistant with multi-turn memory (SQLite-backed, session-isolated)
- RAG over enterprise documents (Markdown + PDF) with smart heading-aware chunking
- Citations on every retrieved answer
- Provider-agnostic LLM layer (swap Anthropic ↔ OpenAI via env var)
- Multi-step planning: decomposes complex queries into sub-tasks

</details>

<details>
<summary><b>🔌 MCP Connectors (18 tools across 7 servers)</b></summary>


| Connector | Tools |
|---|---|
| **GitHub** | search_issues, create_issue, comment_on_issue, search_code |
| **Gmail** | search, get_thread, draft_reply |
| **Calendar** | list_events, create_event, check_availability |
| **File System** | list_files, read_file, search (sandboxed) |
| **PostgreSQL** | query (read-only SELECT), describe_schema |
| **Knowledge Base** | query_knowledge_base (RAG) |
| **System** | echo, current_time |

</details>

<details>
<summary><b>🛡️ Security</b></summary>


- **JWT** access + refresh tokens with cryptographic signature verification
- **Role-based access control** (admin / user / viewer)
- **Bcrypt** password hashing
- **Password policy**: ≥8 chars, letter + digit/special required, common-password blocklist
- **Rate limiting**: `/auth/login` 10/min, `/auth/register` 5/min, global 100/min per IP
- **Token revocation** on logout (defense against stolen tokens)
- **HTTP security headers** on every response: HSTS, CSP, X-Frame-Options DENY, X-Content-Type-Options nosniff, Referrer-Policy, Permissions-Policy
- **Sandboxed file system** access (path-traversal protection)
- **Read-only SQL** enforcement on database queries
- **Human-approval gate** on destructive actions (create_issue, send_email)
- **Audit log** of every authenticated action (timestamped, IP-tracked)
- **CodeQL SAST** scanning on every push (Python + TypeScript)
- **Dependabot** auto-updates for outdated dependencies
- Full vulnerability disclosure process — see **[SECURITY.md](SECURITY.md)**

</details>

<details>
<summary><b>🤖 Agentic, 📚 Enterprise, 📊 Observability, 🧪 Evaluation, 🚢 Deployment</b></summary>

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

</details>

## 🚀 Quick Start

### 1. Clone & install
```bash
git clone https://github.com/virinchisai/sentinel-ai.git
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

## 📂 Repository Tour

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
├── knowledge/           # Provenance-pinned claims over RAG sample documents
├── knowledge-tests/     # Deterministic expectations for critical policy values
├── docker/              # Dockerfile.backend, Dockerfile.frontend, docker-compose.yml
├── kubernetes/          # Production K8s manifests
├── .github/
│   ├── workflows/       # Application, CodeQL, and knowledge-reliability CI
│   └── dependabot.yml   # Weekly dep updates
└── SECURITY.md          # Vulnerability disclosure + threat model
```

## 🧪 Testing

### Local
```bash
pytest backend/tests -v       # 20 tests including 16 security regression tests
cd frontend && npm run build  # frontend
```

The security suite (`backend/tests/test_security.py`) proves every protection stays on:
- Password policy (length, common-password blocklist, character classes)
- JWT signature verification + type-mismatch rejection
- RBAC permission checks per role
- SQL injection blocking (DROP / DELETE / INSERT rejected)
- Path-traversal blocking on filesystem connector

### On GitHub
The repository uses four automated quality and maintenance checks:
- **[tests](../../actions/workflows/test.yml)** — pytest on Python 3.11 + 3.12, MCP smoke test (asserts ≥18 tools register), frontend lint + build
- **[CodeQL](../../actions/workflows/codeql.yml)** — SAST for Python + TypeScript with the security-and-quality query suite
- **[Knowledge Reliability](../../actions/workflows/knowledge-reliability.yml)** — validates the RAG sample documents for source drift, stale or contradictory claims, access leaks, and prompt-injection indicators; publishes SARIF, a KBOM, and source hashes
- **Dependabot** — weekly PRs for outdated pip / npm / GitHub Actions dependencies

You can also click **"Run workflow"** from the [Actions tab](../../actions) to trigger a manual run.

Knowledge claims live in `knowledge/` and point directly to files in `backend/rag/sample_docs/`. Their SHA-256 values make document changes explicit during review. After an intentional policy edit, update the matching claim value and source hash, then run:

```bash
pip install "git+https://github.com/virinchisai/knowledge-reliability-ci.git@v0.1.0"
knowledge-ci check .
knowledge-ci test . --tests knowledge-tests
```

## 🚢 Production Deployment

```bash
docker compose -f docker/docker-compose.yml up
```

Boots the full stack: Postgres+pgvector, FastAPI backend, Next.js frontend, Prometheus, and Grafana with pre-provisioned dashboards.

For Kubernetes, apply `kubernetes/*.yaml`.

## 🛡️ Security

SentinelAI is built defense-in-depth. Every protection has a **regression test** so disabling one breaks CI.

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limit (10/min) + bcrypt slow hash |
| Password stuffing | Common-password blocklist + minimum entropy policy |
| Token theft | Short access-token expiry + revocation list + HSTS |
| XSS / Clickjacking | CSP `default-src 'none'`, `X-Frame-Options: DENY` |
| SQL injection | Parameterized queries + SELECT-only enforcement |
| Path traversal | Resolved-path containment in FileSystem connector |
| Prompt injection → destructive action | Human-approval gate, audit logging |
| Vulnerable dependencies | Dependabot weekly + CodeQL on every push |

See **[SECURITY.md](SECURITY.md)** for the full threat model and the private vulnerability-reporting process.

The repo's **[Security tab](../../security)** surfaces CodeQL findings, Dependabot alerts, and the published security policy.

## 💼 Why this matters

Most "AI app" portfolio projects are thin ChatGPT wrappers. SentinelAI is the entire enterprise AI platform stack — auth, RBAC, multi-tool agents, RAG with citations, observability, evaluation, deployment — built on the modern protocol (MCP) that Anthropic, OpenAI, and the broader ecosystem are converging on. It demonstrates the full skill set required for **Applied AI Engineering**, **AI Platform Engineering**, and **Forward-Deployed Engineering** roles at frontier AI companies.

<details>
<summary><b>📋 Resume bullet (copy-paste ready)</b></summary>

> Designed and shipped a secure enterprise AI workspace implementing the **Model Context Protocol (MCP)** to orchestrate AI agents across GitHub, Gmail, Calendar, PostgreSQL, sandboxed FS, and an enterprise knowledge base. Engineered a FastAPI gateway with **JWT auth, RBAC, audit logging, rate limiting, HSTS/CSP headers, and token revocation**, a multi-step planner-driven agent loop, a citation-aware RAG pipeline (Chroma / PGVector), Prometheus observability, a Next.js 14 frontend, a 20-test pytest suite (16 dedicated security regressions), CodeQL + Dependabot in CI, and Docker / Kubernetes deployment.

</details>

## 📈 Star History

[![Star History Chart](https://api.star-history.com/svg?repos=virinchisai/sentinel-ai&type=Date)](https://star-history.com/#virinchisai/sentinel-ai&Date)

## 📜 License
MIT — see [LICENSE](LICENSE).

---

<div align="center">

**Built by [Virinchi Sai Athmakuri](https://github.com/virinchisai)** · [LinkedIn](https://www.linkedin.com/in/virinchisaiathmakuri/) · [Email](mailto:saivirinchi103@gmail.com)

⭐ Star this repo if you find it useful!

</div>


---

## 🚀 Version 2.0

[**Download SentinelAI v2.0.0**](https://github.com/virinchisai/sentinel-ai/releases/tag/v2.0.0)

The original README above is preserved in full. Its version-specific setup, architecture, demo credentials, and deployment descriptions reflect the earlier release. For v2.0, use the updated instructions and operating boundaries below.

A private engineering workspace for **evidence-backed investigation and approved
actions**. Run a local model, search documents within a workspace, inspect sources,
and approve exact changes to connected tools.

[![tests](https://github.com/virinchisai/sentinel-ai/actions/workflows/test.yml/badge.svg)](https://github.com/virinchisai/sentinel-ai/actions/workflows/test.yml)
[![CodeQL](https://github.com/virinchisai/sentinel-ai/actions/workflows/codeql.yml/badge.svg)](https://github.com/virinchisai/sentinel-ai/actions/workflows/codeql.yml)

### What works in v2

- Ollama local inference with streamed text and tool execution events; optional
  OpenAI/Anthropic adapters remain available.
- Persistent conversations with complete tool-call metadata, saved-session UI,
  cancellation, and optional validated planning.
- Personal/team workspaces, membership checks, owner-controlled document changes,
  and scoped retrieval. A viewer cannot execute host or external connector tools.
- Safe, bounded document uploads; durable ingestion jobs; previews; replacements
  with source hashes/version counters; deletion including indexed chunks.
- Local keyword search or hybrid search with Ollama embeddings. PostgreSQL uses
  full-text search, pgvector HNSW candidates, and rank fusion; SQLite supports a
  lightweight local deployment.
- Exact, expiring, single-use approvals for issue creation, comments, email drafts,
  and calendar events. Writes are never automatically retried.
- Encrypted per-user GitHub/Google credentials, real Gmail/Calendar API calls,
  refresh-token rotation, durable logout revocation, and optional Keycloak SSO.
- Prometheus metrics, tool/approval audit records, optional self-hosted Langfuse
  tracing, regression tests, retrieval benchmarks, and repaired container builds.

This is a **single-worker small-team pilot**, not a certified enterprise service.
See [operational boundaries](docs/operations.md) before using sensitive data.

### Run locally

Requires Python 3.11/3.12, Node 22.13+, and Ollama. The software can run without
paid inference APIs; hardware, electricity, hosting, and provider account rules
still apply.

```bash
git clone https://github.com/virinchisai/sentinel-ai.git
cd sentinel-ai
git checkout v2.0.0
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.lock
pip install --no-deps -e .
python scripts/configure.py
ollama pull qwen2.5:1.5b
python -m backend.migrate
uvicorn backend.api.main:app --host 127.0.0.1 --port 8000
```

Start Ollama separately if it is not running. In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**, register your account, and upload documents.
There is no shared demo password. To ingest the included sample policies into your
account, look up your ID from `/auth/me`, then run:

```bash
python -m backend.rag.ingest --user-id YOUR_USER_ID
```

Optional hybrid retrieval:

```bash
ollama pull nomic-embed-text
# Set EMBEDDING_MODEL=nomic-embed-text in .env, restart, then upload/reindex documents.
```

Use `OLLAMA_MODEL` to select a model suited to your hardware. Smaller models use
less memory, but evaluate tool selection and answer quality before relying on them.

### Docker Compose

```bash
python scripts/configure.py  # only if .env does not exist
# Run Ollama on an address reachable from Docker; see docs/operations.md.
docker compose --env-file .env -f docker/docker-compose.yml up --build -d
```

This starts PostgreSQL/pgvector, the API, and Next.js. Published ports bind to
loopback. Configure a TLS reverse proxy and trusted origins for shared access.

### Verify

```bash
pip install -e '.[dev]'
pytest backend/tests -q
PYTHONPATH=. python scripts/benchmark.py
cd frontend
npm run lint
npm run build
```

With both local servers running, `bash scripts/browser-smoke.sh` verifies
registration, upload, preview, streaming UI, deletion, and logout using the
Playwright CLI. Streaming UI is mocked; the separate live-agent smoke test
verifies real local inference and retrieval.

The sample retrieval benchmark is a deterministic release gate, not a claim of
production answer accuracy. Live local checks are available in
`scripts/local_smoke.py` and `scripts/live_agent_smoke.py`; run them from the repo
root with `PYTHONPATH=.` and a configured Ollama model.

### Architecture

```mermaid
flowchart LR
    UI[Next.js workspace] --> API[FastAPI identity and membership]
    API --> Agent[Bounded agent loop]
    Agent --> Ollama[Local Ollama model]
    Agent --> Policy[Tool authorization]
    Policy --> Read[Workspace document retrieval]
    Policy --> Approval[Exact action approval]
    Approval --> MCP[Per-user MCP session]
    Policy --> MCP
    MCP --> GitHub[GitHub]
    MCP --> Google[Gmail and Calendar]
    Read --> DB[(SQLite or PostgreSQL + pgvector)]
    API --> Jobs[Durable ingestion queue]
    Jobs --> DB
```

- [Upgrade, backups, deployment, optional tools](docs/operations.md)
- [Connector setup and permissions](docs/connectors.md)
- [Security model](SECURITY.md)
- [Version 2.0 changes](CHANGELOG.md)

### License

MIT for SentinelAI. Dependencies and model weights retain their own licenses.
