# Connector setup

Credentials are per user and encrypted in the application database. Configure
them through Settings; never commit tokens or OAuth secrets. Credential changes
apply to the next agent run. A run already in flight may retain its credential.

## GitHub

Create a fine-grained personal access token restricted to the intended repository,
with read access for search and issue write access only when needed. Add it in
Settings. Configure `GITHUB_DEFAULT_REPO` and comma-separated `GITHUB_ALLOWED_REPOS`
on the host. The allowlist is an additional restriction, not a replacement for
GitHub token scopes. Issue and comment creation require exact user approval.

## Google

Create your own Google Cloud OAuth application and enable Gmail and Calendar APIs.
Authorize your account with offline access and obtain a refresh token. For a local
pilot you can use Google's OAuth Playground with **your own OAuth credentials**.
Request only the scopes needed: Gmail read access, Gmail compose for drafts, and
Calendar event/free-busy access for the desired features. Provider consent and
verification requirements depend on how you distribute the OAuth application.

Save client ID, client secret, and refresh token in Settings. The backend refreshes
access tokens at use time. Gmail draft replies remain drafts; SentinelAI does not
send email. Calendar creation can notify attendees and therefore requires approval.
The status page distinguishes configured credentials from a verified live account.

## Host tools and MCP

Filesystem and database tools are administrator-only. `WORKSPACE_DIR` restricts
file access. Use a dedicated SELECT-only database account in `TOOL_DATABASE_URL`;
never reuse the application's database owner. SQL is parsed as one SELECT,
executed in a read-only transaction, and bounded by timeout/result limits.
SQLite demo database queries are also read-only.

The application uses local MCP subprocesses under a trusted API gateway. Direct
MCP stdio/HTTP access is operator-level access, not a multi-user authorization API.
Do not expose the standalone MCP server to application users or the public network.
Use the authenticated API so workspace, tool policy, and approval enforcement apply.
