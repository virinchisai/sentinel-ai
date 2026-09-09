# Operations and upgrades

Version 2.0 targets a single API worker and a small-team pilot. Do not run multiple
API workers: conversation serialization and ingestion-worker recovery currently
assume one process. Multi-replica HA is not a supported deployment configuration.

## Upgrade from v1

1. Stop v1. Back up `sentinel.db`, `sentinel_memory.db`, `.chroma`, and the original
   configuration. Preserve backups outside the checkout.
2. Check out v2.0.0 and install the new locked dependencies and frontend dependencies.
3. Run `python scripts/configure.py` only when no `.env` exists; otherwise add the
   settings from `.env.example` without overwriting your secrets.
4. Run `python -m backend.migrate`. The additive migration retains user accounts
   and audit records, adds token versions, and creates v2 tables. Existing sessions
   must sign in again.
5. Re-upload source documents into the intended workspace. V1's shared Chroma
   collection has no ownership data and is intentionally not automatically exposed
   through v2. Historical v1 conversation files remain untouched; v2 starts new
   conversations because v1 did not preserve complete tool messages.
6. Start the app, verify workspace access, and test retrieval before inviting users.

## Backup and restore

SQLite: stop ingestion, then run `python scripts/backup.py sentinel.db backup.db`.
The script uses SQLite's consistent backup API and validates the result. Restore
into a **new** destination using the same command, swap configuration after
verification, and retain the original database until the restored app is checked.

PostgreSQL: use `pg_dump -Fc` with credentials provided through `.pgpass` or a
secret manager; restore with `pg_restore` into a new database. Restore the matching
JWT/encryption secret too, otherwise saved connector credentials cannot decrypt.
Schedule the backup script with your host's scheduler and retain encrypted copies
on a separate disk. Test restoration periodically; a backup file alone is not
proof of recoverability.

## Models and resources

Run `ollama pull qwen2.5:1.5b` and optionally
`ollama pull nomic-embed-text`. CPU inference works but can be slow. Select a smaller
tool-capable model if memory or latency is unsuitable. Measure on your hardware;
this release does not promise a concurrent-user capacity.

The default local `.env` uses keyword search to start without an embedding model.
Set `EMBEDDING_MODEL=nomic-embed-text` **before ingestion** for hybrid retrieval.
After changing embedding models, re-upload documents to reindex. PostgreSQL's HNSW
index is configured for 768-dimensional vectors; use a compatible model. SQLite
uses keyword scoring plus cosine similarity; PostgreSQL uses indexed full-text
and vector candidates with reciprocal-rank fusion.

Compose connects to Ollama on the host. On Linux or Docker Desktop, the host
service must listen on an address reachable from containers; configure your
firewall so the Ollama endpoint is not accessible to untrusted networks.
The API and frontend published ports are bound to loopback by default.

## Optional integrations

Docling: `pip install '.[docling]'`, set `DOCUMENT_PARSER=docling`. The basic parser
preserves PDF pages. Docling exports Markdown and currently presents the converted
document as a single logical page; do not interpret that as original pagination.

Langfuse: `pip install '.[observability]'`, configure `LANGFUSE_BASE_URL`,
`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY` for your self-hosted instance, then
set `ENABLE_LANGFUSE=true`. Traces contain span names and timing; document text and
credentials are not passed to the tracing API. Prometheus metrics remain available
at `/metrics`; restrict this endpoint at the proxy for shared deployments.

Keycloak: configure a public OIDC client with authorization code flow and S256 PKCE.
Set an exact valid redirect URI matching `OIDC_REDIRECT_URI`, and configure
`OIDC_ISSUER` and `OIDC_CLIENT_ID`. The sign-in button appears automatically.
Only RS256 ID tokens from the configured issuer/audience are accepted. SSO accounts
are bound to issuer+subject, not automatically linked by email. Local logout revokes
SentinelAI sessions; it does not log the user out of the identity provider.

## Reliability boundaries

Ingestion jobs survive restarts while queued. Jobs interrupted while running are
marked interrupted; re-upload to retry. Writes are never automatically retried.
An approval stuck in `running` after a crash may have completed upstream: inspect
the upstream system before creating a new action. A client disconnect cancels
streaming, but cannot undo an upstream action that already completed.

Document replacement retains a version counter and current source hash, but is
not an archive of prior document bytes. Use backups or source control for history.
Application-layer membership checks protect retrieval; database row-level-security
policies are not configured in this release. Browser bearer tokens are stored in
localStorage; deploy only behind trusted origins/TLS and maintain XSS defenses.

Local operators can assign a role with
`PYTHONPATH=. python scripts/manage_user.py USERNAME admin` (or `user`/`viewer`).
This command requires direct database access, revokes existing sessions, and
records an audit event. Team workspace owners manage membership in Settings;
platform administrators are a separate role.
