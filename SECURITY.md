# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅ |

## Reporting a Vulnerability

**Do not** open a public GitHub issue for security vulnerabilities.

If you discover a security issue in SentinelAI, please report it privately:

1. Use GitHub's **[Private vulnerability reporting](../../security/advisories/new)** feature, **or**
2. Email the maintainer directly via the address on the GitHub profile

You should receive an acknowledgment within **48 hours**. We'll work with you to verify and fix the issue, and credit you in the security advisory (unless you request anonymity).

### What to include
- A clear description of the vulnerability
- Steps to reproduce
- Impact assessment (what an attacker could achieve)
- Suggested fix, if any

## Security Controls

SentinelAI implements defense-in-depth across multiple layers:

### Authentication & Authorization
- **JWT** access tokens (30-min expiry by default) and refresh tokens (7 days)
- **Bcrypt** password hashing with auto-generated salt
- **Password policy**: minimum 8 chars, must contain a letter and a digit/special char, common passwords blocked
- **Token revocation** on logout (in-memory; use Redis in production)
- **Role-based access control** (admin / user / viewer)
- **Tampered token rejection** via cryptographic signature verification

### Rate Limiting
- `/auth/login` capped at **10 requests/minute per IP**
- `/auth/register` capped at **5 requests/minute per IP**
- Global default of **100 requests/minute per IP** on all routes
- Powered by [slowapi](https://github.com/laurents/slowapi)

### HTTP Security Headers
Every response sets:
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`

### Connector Sandboxing
- **File System** access is rooted at `WORKSPACE_DIR`; any path that resolves outside this root is rejected with `PermissionError`
- **Database** queries are restricted to `SELECT` statements; `DROP`, `DELETE`, `UPDATE`, `INSERT` are refused
- **Destructive agent actions** (creating GitHub issues, sending email) require explicit human approval before execution

### Audit Trail
- Every login, registration, logout, and agent action is recorded in the `audit_log` table with timestamp and IP address
- Admin role can view full audit log via `/admin/audit-log`

### Observability
- All requests carry an `x-request-id` for correlation
- Prometheus metrics expose auth failures, tool call rates, and latency for anomaly detection

### Dependency Security
- **Dependabot** opens PRs weekly for outdated Python and npm dependencies
- **CodeQL** scans every push/PR for SAST findings
- CI tests run on every commit; failing tests block merge

## Threat Model

| Threat | Mitigation |
|---|---|
| Brute-force login | Rate limit + bcrypt slow hash |
| Password stuffing | Common-password blocklist + minimum entropy |
| Token theft | Short expiry + revocation list + HTTPS-only deployment |
| XSS | CSP `default-src 'none'`, `X-Content-Type-Options: nosniff` |
| Clickjacking | `X-Frame-Options: DENY`, CSP `frame-ancestors 'none'` |
| MITM | HSTS, HTTPS termination at ingress |
| SQL injection | Parameterized queries, SELECT-only enforcement |
| Path traversal | Resolved-path containment check in FileSystem connector |
| Prompt injection | Human-approval gate on destructive actions, audit logging |
| Privilege escalation | RBAC enforced at every protected endpoint |
| Vulnerable deps | Dependabot + CodeQL |

## Things This Project is **Not** Hardened Against

This is a portfolio demonstration. For real production use you'd additionally need:

- TLS termination (use a reverse proxy: Caddy, Traefik, nginx)
- Persistent token revocation store (Redis)
- Secrets management (Vault, AWS Secrets Manager, etc.) — not `.env`
- Web Application Firewall (WAF)
- Anomaly detection on the audit log
- Penetration testing
- Compliance certification (SOC 2, ISO 27001) if handling regulated data

## Credits

Found a bug? Reporters who follow this disclosure process will be credited in the published advisory.
