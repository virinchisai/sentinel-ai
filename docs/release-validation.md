# Version 2.0 release validation

Validated locally on 2026-09-09:

| Check | Result |
|---|---|
| Backend regression suite | 41 tests passed |
| Frontend lint | Passed, no warnings |
| Next.js production build | Passed |
| Python dependency audit | No known vulnerabilities in requirements.lock |
| npm audit | No reported vulnerabilities at audit time |
| API and frontend Docker images | Built successfully on Linux containers |
| PostgreSQL migration and lexical retrieval | Passed |
| PostgreSQL vector insert/search and workspace isolation | Passed with deterministic vectors |
| Local Ollama embeddings | Passed with nomic-embed-text, 768 dimensions |
| Local streamed inference | Passed |
| Local agent tool call and source retrieval | Passed with qwen2.5:1.5b |
| Sample-document retrieval benchmark | 6/6 expected sources found within top 3 |
| Playwright CLI browser workflow | Registration, login, queued upload, preview, streaming UI, delete, logout passed |
| SQLite backup and restore | Data round trip and integrity checks passed |
| Python wheel/source distribution | Built and inspected for sample data inclusion and absence of local secrets/databases |

The browser streaming response is mocked to make UI regression testing deterministic.
The separate local-agent smoke test exercises actual model inference, MCP discovery,
workspace retrieval, and a source-backed final answer. Google API and OIDC tests use
mock HTTP responses; the OIDC test verifies real RSA signatures and nonce validation.
No email, calendar invitation, or GitHub issue was sent to a real external account
as part of these tests. Optional Docling and Langfuse deployments were not exercised.

The initial 7B local-model tool test exceeded its timeout on the CPU-only test host.
The smaller 1.5B model completed the workflow and is the default starter model.
These results are release checks, not enterprise security certification, production
accuracy estimates, or a concurrent-user performance guarantee.
