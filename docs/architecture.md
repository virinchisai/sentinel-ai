# Architecture

See the current diagram in [README](../README.md).

The API establishes user identity, resolves workspace membership, and creates a
trusted actor context. The actor is checked before schema exposure, before tool
execution, and again when a pending write is approved. MCP subprocesses receive
only that user's external connector credentials. Document retrieval is handled
in-process using the actor's workspace, never a model-selected workspace ID.

The SQL database holds users, memberships, documents, chunks, jobs, complete
conversation messages, approvals, refresh-token consumption, and audit events.
PostgreSQL adds pgvector and full-text indexes; SQLite is the local fallback.

See [operations](operations.md) for concurrency and recovery limits.
