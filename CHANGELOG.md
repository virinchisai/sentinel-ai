# Changelog

## 2.0.0

SentinelAI becomes a local-first, workspace-scoped investigation application.

### Added
- Ollama provider and streaming chat with persistent history and source previews.
- Workspaces, membership management, owner-controlled document lifecycle, durable
  ingestion queue, and scoped local/PostgreSQL hybrid retrieval.
- Per-user encrypted GitHub and Google credentials and real Google API connectors.
- Exact expiring action approvals with atomic single-use transitions.
- Optional PKCE Keycloak sign-in, Docling extraction, and Langfuse tracing.
- Locked backend dependencies, Next.js 16/React 19, tested Docker definitions,
  database migration, backup helper, and retrieval release gates.

### Fixed
- Planner prompt formatting, loss of tool-call metadata in conversation history,
  upload path traversal and unbounded reads, missing per-tool permissions,
  incomplete logout/refresh behavior, WebSocket authorization, SQL validation,
  filesystem sibling-prefix/symlink escapes, stale document chunks, and TXT uploads.

### Upgrade notes
V1 sessions must sign in again. Re-upload documents into an explicitly chosen
workspace; v1's shared Chroma data has no ownership metadata. V1 conversation files
remain untouched and are not imported into the new complete-message format.
Back up databases and configuration before running the additive migration.

### Boundaries
Single-worker pilot deployment; no HA guarantee. Third-party connectors require
user-provided credentials and provider consent. Optional services are not bundled
as always-on infrastructure. Local inference throughput depends on hardware.
See docs/operations.md for the complete operational limits.
