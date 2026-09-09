# Security

Report vulnerabilities privately through GitHub's security reporting interface.
Do not post credentials or sensitive documents in public issues.

## Trust boundaries

- API authentication establishes user identity. Workspace membership is resolved
  from database records; model-supplied tool arguments cannot choose another user.
- Retrieval, preview, and lifecycle endpoints enforce workspace membership. Document
  replacement/deletion additionally require document ownership.
- External tools require tool permission and personal connector credentials. Host
  filesystem/database access is administrator-only. GitHub repositories are allowlisted.
- Write proposals are persisted with exact arguments, owner, workspace, expiry,
  and an atomically consumed status. Client-controlled blanket approval is rejected.
- Model responses, documents, and connector outputs are untrusted data. Prompt
  instructions are not a security boundary; execution authorization is server-side.
- OAuth refresh tokens and connector tokens are encrypted at rest using a key
  derived from the deployment secret. Backups need appropriate encryption/access
  controls because document content and conversations are not application-encrypted.

## Deployment requirements

Generate a unique deployment secret. Production startup rejects missing/known weak
secrets. Use TLS and trusted origins; keep API/metrics/MCP endpoints appropriately
restricted. Set a database tool account with SELECT-only grants; query parsing and
read-only transactions do not replace least-privilege database roles.

The direct MCP server is an operator interface. Multi-user clients must use the
API gateway; the direct transport does not implement workspace/session policies.

## Known boundaries

This release is a single-worker pilot. It has no independent security certification,
no configured PostgreSQL row-security policies, no immutable external audit ledger,
and no multi-replica coordination. Bearer tokens are stored in browser localStorage.
A compromised browser or host remains outside the protection of application RBAC.
Credential removal affects subsequent runs; already-running upstream calls may
complete. Approval execution cannot provide exactly-once delivery across an external
provider and a process crash; ambiguous writes are not automatically retried.
