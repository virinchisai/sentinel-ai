# SentinelAI v2.0 production gap analysis

**Audit baseline:** `6b97765` (`v2.0.0`, 2026-09-09)  
**Review date:** 2026-09-14  
**Intended deployment reviewed:** self-hosted, single-worker, small-team pilot  
**Verdict:** appropriate for a controlled pilot after deployment hardening; not yet
appropriate for a high-assurance, multi-tenant, or highly available production
service.

## Executive summary

Version 2.0 closes most of the serious correctness and authorization problems found
in the earlier v1 review. Identity is converted into a trusted actor, workspace
membership is checked outside the model, tool permissions are enforced server-side,
connector credentials are per user, and external writes require exact expiring
single-use approvals. Upload, SQL, filesystem, session, WebSocket, persistence, and
retrieval behavior all have meaningful regression coverage.

No critical issue was identified in this code review. Four high-priority gaps remain
before the system should hold sensitive team data:

1. connector encryption has no independent, versioned key lifecycle;
2. tool authorization is not an explicit default-deny registry;
3. the external database connector selects demo mode from the wrong setting and
   leaks raw driver errors;
4. multi-tenant isolation relies only on application checks, with no database
   row-level-security backstop.

The browser token model, audit correlation, parser isolation, citation validation,
and single-process operating model are important next-tier risks. Several are
acceptable for the stated pilot only when the deployment is on trusted origins,
access is tightly limited, backups are tested, and operators accept downtime.

### Readiness scorecard

| Area | Pilot status | Broader production status | Main reason |
|---|---|---|---|
| Authentication and sessions | Good with caveats | Needs hardening | Rotation/logout work; browser storage and local JWT claims remain |
| Authorization and approvals | Good | Needs hardening | Exact approvals; no independent approver or explicit tool allowlist |
| Workspace data isolation | Good at app layer | Not defense-in-depth | No PostgreSQL RLS |
| Connector secrets | Functional | Needs redesign | Encryption key coupled to JWT secret; no rotation/versioning |
| Agent/tool safety | Good for fixed tool set | Needs hardening | Bounded loop and no write retries; future tools could inherit access |
| RAG and citations | Good pilot baseline | Not accuracy-assured | Scoped retrieval; small benchmark and no citation verifier |
| Upload and parsing | Good baseline | Needs sandboxing | Size/path/type checks; parser remains in API worker |
| Observability and audit | Partial | Insufficient | Useful records, but incomplete metrics and request correlation |
| Reliability and scale | Deliberately limited | Not ready | One API/ingestion worker, process-local controls, no HA |
| Delivery and dependencies | Good baseline | Needs ongoing operations | Locked dependencies, CI, CodeQL, container tests |

## What v2 fixed

The following earlier findings are materially resolved at this baseline:

| Earlier gap | v2 disposition |
|---|---|
| Model/client could imply blanket approval | Public requests reject extra fields and the orchestrator rejects `auto_approve` |
| Write approval was not bound to one action | Approval stores user, workspace, session, tool, canonical arguments, expiry, and single-use status |
| Writes could be retried automatically | Destructive tools receive one attempt; ambiguous post-crash state is surfaced |
| Tool access lacked per-tool policy | Role, membership, host-tool, credential, and GitHub repository checks run server-side |
| Shared connector credentials | GitHub and Google credentials are encrypted and stored per user |
| Shared/unscoped retrieval | Documents, chunks, conversations, and retrieval are workspace-scoped |
| Document replacement left stale chunks | Replacement and deletion update indexed chunks and metadata |
| Unsafe/unbounded uploads | Filename, extension, and byte limits are enforced; reads are streamed in bounded blocks |
| Filesystem sibling-prefix/path escape | Resolved paths must remain relative to the configured root |
| SQL accepted unsafe statements | One parsed `SELECT` is required, with read-only sessions, timeout, and row limits |
| Incomplete refresh/logout behavior | Refresh tokens are one-time and logout increments a durable token version |
| WebSocket authorization drift | WebSocket access is covered by authorization regression tests |
| Container definitions did not match the app | Backend/frontend images and PostgreSQL Compose stack are built in CI |
| Floating backend dependencies | `requirements.lock` exists and is used by CI/container builds |
| Minimal regression coverage | 41 backend tests plus PostgreSQL, browser, container, and retrieval checks |

## High-priority gaps

### H1. Connector encryption needs an independent key lifecycle

**Evidence.** `backend/connectors/credentials.py` derives a single Fernet key by
hashing `JWT_SECRET_KEY`. Ciphertext contains no key identifier and the read path
supports only the current key. Operations therefore instruct users to restore the
JWT secret with the database.

**Risk.** Routine JWT signing-key rotation can make all saved connector credentials
undecryptable. Conversely, keeping a signing secret indefinitely to preserve stored
credentials weakens the session-key lifecycle. A leaked secret compromises both
token signing and encrypted connector data.

**Recommendation.** Introduce a separate `CONNECTOR_ENCRYPTION_KEY` managed by a
secret manager. Store a key version with each credential, support decrypt-old /
encrypt-current rotation, and add a transactional re-encryption command plus backup
and recovery tests. Do not silently fall back to the JWT secret in production.

**Effort:** medium. **Release gate:** required before sensitive shared deployment.

### H2. Tool authorization is not explicit default-deny

**Evidence.** `backend/agents/policy.py` applies special checks by prefixes such as
`fs_`, `db_`, and `github_`. Any otherwise unknown tool is permitted to a user with
`use_tools`. The orchestrator exposes every discovered schema that passes this
function.

**Risk.** A newly registered, renamed, or compromised MCP tool can accidentally
inherit ordinary-user access without a deliberate policy decision. A name that does
not match an expected prefix may bypass connector-specific controls.

**Recommendation.** Define a central immutable registry for all 18 tools containing
minimum role, credential provider, workspace behavior, approval requirement, and
argument validators. Reject every unregistered tool. Assert exact equality between
MCP discovery and the registry in CI, and derive the destructive-tool list from the
same source.

**Effort:** small to medium. **Release gate:** required before adding more tools.

### H3. External database tool configuration is incorrect and error output leaks

**Evidence.** `backend/mcp_server/connectors/database_client.py` sets demo mode from
`DATABASE_URL.startswith("sqlite")`, even though external access is configured by
`TOOL_DATABASE_URL`. A deployment using SQLite for SentinelAI and PostgreSQL for the
tool therefore opens the demo database instead. PostgreSQL schema description always
returns an empty list, and execution failures return raw `str(exception)` to the
agent.

**Risk.** Operators can believe they connected a restricted operational database
while the tool silently queries demo data. Raw driver errors may expose hostnames,
schema details, query fragments, or account information to conversation history and
the model.

**Recommendation.** Select mode solely from validated `TOOL_DATABASE_URL`; treat an
empty value as explicitly disabled or explicit demo mode. Implement bounded
PostgreSQL catalog introspection, map failures to stable public error codes, log
sanitized diagnostic details server-side, and add configuration-matrix tests.

**Effort:** small to medium. **Release gate:** required if enabling `db_*` tools.

### H4. Workspace isolation has no database enforcement layer

**Evidence.** Workspace checks are consistently present in application code, but
`docs/operations.md` and `SECURITY.md` confirm that PostgreSQL row-level security is
not configured. The application database credential can access every tenant row.

**Risk.** A missed filter in a future route, migration, background job, or reporting
query can become a cross-workspace disclosure. Compromise of the API's database
credential exposes all workspaces rather than the current tenant.

**Recommendation.** For multi-tenant use, add PostgreSQL RLS policies for documents,
chunks, conversations, approvals, jobs, and connector credentials. Set a verified
user/workspace context per transaction, use a non-bypass application role, and add
negative integration tests that intentionally omit application filters. Keep SQLite
documented as single-trust-domain only.

**Effort:** large. **Release gate:** required for high-assurance multi-tenant use;
accepted risk for a tightly controlled pilot.

## Medium-priority gaps

### M1. Browser bearer tokens are exposed to any successful XSS

The frontend stores access and refresh tokens in `localStorage`. Existing CSP and
security headers help, but any script execution in the trusted origin can read and
exfiltrate both tokens. Prefer secure, `HttpOnly`, `SameSite` cookies with CSRF
protection or a backend-for-frontend session. Until then, require TLS, restrict
origins, avoid third-party scripts, shorten refresh lifetime, and test CSP on the
deployed domain.

### M2. Approval is confirmation, not separation of duties

The same user who initiated an action can approve it, provided they retain tool
permission. This is a sound protection against accidental model writes but not a
four-eyes control. Add optional workspace policy requiring an owner or designated
approver distinct from the requester for high-impact tools. Preserve the exact
argument binding and expiry semantics.

### M3. Audit records lack end-to-end correlation and tamper resistance

`AuditLog` supports IP and detail fields, but most direct `log_action` calls omit the
request IP. Request IDs are not stored with audit, approval, model, or tool events.
Logs live in the same mutable database as application state. Add request/session/
workspace/approval correlation fields, consistently capture trusted proxy-aware
client identity, export security events to an append-only sink, define retention,
and alert on denials, failed approvals, credential changes, and admin role changes.

### M4. Declared observability is only partially instrumented

HTTP count/latency, tool count/latency, and LLM request count are used. The declared
LLM latency, RAG retrieval, and auth-event metrics are not incremented at this
baseline. Exceptions that escape `call_next` also bypass HTTP measurement, and
`ENABLE_METRICS` does not disable `/metrics`. Instrument success/error/cancellation
paths, provider latency and timeouts, retrieval outcomes, approval lifecycle, queue
depth/age, authorization denials, token usage where providers expose it, and model
labels accurately. Make the metrics switch effective and keep the endpoint private.

### M5. Upload parsing needs stronger content validation and isolation

Uploads are bounded and extension-checked, but MIME/magic bytes are not validated
and PDF parsing runs in the API process/thread pool. A malformed or adversarial file
can still consume parser CPU/memory or exploit a parser defect. Validate signatures,
cap page/chunk/extracted-text counts, run parsing in a resource-limited worker or
sandbox, scan files where the threat model requires it, and add malformed/corpus
fuzz tests. Keep parser dependencies patched.

### M6. Citation quality is prompt-enforced rather than verified

Retrieval returns source metadata and the prompt asks the model to cite it, but no
post-generation check ensures that a citation exists, maps to retrieved evidence,
or supports the claim. Add structured citation output, reject unknown source IDs,
measure citation precision/recall, and distinguish evidence-backed statements from
model synthesis in the UI.

### M7. The retrieval benchmark is too small for production confidence

The current deterministic gate contains six sample-document expectations and is
valuable for regression detection, not domain accuracy. Build a versioned dataset
from representative, permission-scoped queries including abstention, conflicting
documents, stale versions, prompt injection, multilingual text, tables, and
cross-workspace negative cases. Track retrieval and answer metrics by model/parser
configuration and require statistically meaningful thresholds.

### M8. Single-process coordination limits reliability and scale

Conversation locks, rate limits, MCP lifecycle, and ingestion recovery assume one
API process. A crash interrupts running ingestion and may leave an external write in
an intentionally ambiguous state. Move jobs and distributed locks to durable shared
infrastructure before adding replicas; introduce idempotency keys where providers
support them; separate readiness from liveness; drain workers on shutdown; and run
load, restart, and failure-injection tests. Do not scale the current API horizontally.

### M9. Local JWTs need tighter protocol constraints and rotation operations

Local JWTs validate signature, expiry, type, JTI, and token version, but omit issuer
and audience, expose the signing algorithm as general configuration, and provide no
overlapping signing-key rotation. Pin the intended algorithm in code, add issuer and
audience validation, support key IDs/rotation, clean expired `UsedRefresh` rows, and
document emergency revocation. The optional OIDC path already performs issuer and
audience checks for RS256 ID tokens.

### M10. Secrets are passed to MCP subprocesses through environment variables

The per-run environment is deliberately restricted, but it includes connector
tokens and the deployment/database settings needed by the child. Environment values
may be visible to same-host privileged process inspection or crash tooling. Minimize
the child contract, remove `JWT_SECRET_KEY` unless proven necessary, pass ephemeral
credentials over a protected IPC channel where practical, redact subprocess errors,
and document that host administrators remain fully trusted.

### M11. CI lacks Python static-quality gates

CI runs backend tests on two Python versions, a deterministic benchmark, frontend
lint/build/audit, PostgreSQL smoke, container builds, browser smoke, CodeQL, package
builds, and knowledge checks. It does not run an explicit Python formatter/linter or
type checker. Add Ruff (or equivalent), a type checker on security-critical modules,
secret scanning, dependency audit as a recurring CI job, migration upgrade tests,
and a Compose startup smoke. Pin third-party actions by immutable commit for a
stronger supply-chain posture.

## Low-priority and operational improvements

- `/health` is static liveness. Add `/ready` checks for database access, migration
  compatibility, ingestion-worker state, and—when required by deployment policy—
  model reachability.
- File search bounds per-file reads and result count but not total traversal time or
  file count. Add a traversal deadline and entry budget for very large roots.
- MCP starts a local subprocess for each agent run. Measure its startup overhead and
  consider a supervised pool only after preserving per-user credential isolation.
- Document replacement keeps a counter and current hash, not old bytes. Add explicit
  version storage only if document history is a product requirement.
- Rate limiting is process-local and IP-based. Move to a shared store and define
  trusted-proxy handling before multi-process or internet-facing deployment.
- Define tested recovery objectives, encrypted off-host backup retention, restore
  drills, incident response, credential revocation, and data-deletion procedures.

## Recommended implementation sequence

### Phase 1 — safe pilot hardening

1. Fix the database connector mode/error/schema behavior (H3).
2. Replace prefix authorization with an exact tool registry (H2).
3. Separate and version the connector encryption key (H1).
4. Complete metrics and audit correlation (M3, M4).
5. Add upload signature checks and parser resource limits (M5).
6. Add readiness checks, backup alerts, and deployment runbooks.

### Phase 2 — sensitive team deployment

1. Move browser sessions to an `HttpOnly` design (M1).
2. Add structured citation validation and a representative evaluation suite
   (M6, M7).
3. Add optional independent approval policies (M2).
4. Harden local JWT claims and signing-key rotation (M9).
5. Add Python static/security gates and failure-injection tests (M11).

### Phase 3 — multi-tenant or highly available service

1. Add and test PostgreSQL RLS (H4).
2. Externalize queues, locks, rate limits, and security-event storage (M3, M8).
3. Define supported replica topology, zero-downtime migration strategy, SLOs,
   capacity limits, disaster recovery, and on-call ownership.
4. Commission an independent penetration test and remediate findings before making
   security or compliance claims.

## Acceptance gates

The small-team pilot can be considered responsibly deployed when all Phase 1 items
are complete or explicitly risk-accepted, TLS and trusted origins are configured,
`/metrics` and direct MCP access are private, provider credentials are least
privilege, and a restore drill has succeeded.

Do not call the service high-assurance multi-tenant or highly available until H4 and
Phase 3 are complete. Do not claim answer accuracy from the six-case benchmark;
publish evaluation scope, model/parser versions, and observed uncertainty alongside
any future quality claim.

## Review limitations

This is a source, configuration, workflow, and documented-release review of commit
`6b97765`. It is not a penetration test, formal verification, compliance audit, or
load test. The existing release validation used mocked Google/OIDC calls and mocked
browser streaming; it did not send real external writes or exercise optional Docling
and Langfuse deployments. Findings should be re-evaluated after architectural or
threat-model changes.
