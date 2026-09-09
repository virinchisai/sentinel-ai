"use client";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import {
  json,
  getConnectorStatus,
  ConnectorStatus,
  workspace,
} from "@/lib/api";
export default function Settings() {
  const [rows, setRows] = useState<ConnectorStatus[]>([]),
    [status, setStatus] = useState(""),
    [token, setToken] = useState(""),
    [clientId, setClientId] = useState(""),
    [clientSecret, setClientSecret] = useState(""),
    [refreshToken, setRefreshToken] = useState(""),
    [name, setName] = useState(""),
    [member, setMember] = useState("");
  const reload = () =>
    getConnectorStatus()
      .then(setRows)
      .catch((e) => setStatus(String(e)));
  useEffect(() => {
    reload();
  }, []);
  async function connect(provider: string, value: Record<string, string>) {
    try {
      await json("/connectors/" + provider, {
        method: "PUT",
        body: JSON.stringify(value),
      });
      setToken("");
      setClientSecret("");
      setRefreshToken("");
      setStatus("Credentials encrypted and saved for your account.");
      reload();
    } catch (e) {
      setStatus(String(e));
    }
  }
  const input = "block w-full bg-[var(--background)] border rounded p-2 my-3";
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8">
        <div className="max-w-3xl mx-auto space-y-6">
          <h1 className="text-2xl font-semibold">Connections & workspaces</h1>
          <p role="status">{status}</p>
          <section className="border rounded-xl p-5">
            <div className="flex justify-between">
              <h2 className="font-semibold">Connection health</h2>
              <button onClick={reload}>Refresh</button>
            </div>
            {rows.map((r) => (
              <div key={r.name} className="border-b py-3">
                <span className="font-medium">{r.name}</span>
                <span className="ml-3 text-xs uppercase text-[var(--accent)]">
                  {r.mode}
                </span>
                <p className="text-sm text-[var(--muted)]">{r.detail}</p>
              </div>
            ))}
          </section>
          <section className="border rounded-xl p-5">
            <h2 className="font-semibold">GitHub</h2>
            <p className="text-sm mt-2">
              Use a fine-grained token limited to your allowed repositories.
              Writes require a separate action approval.
            </p>
            <input
              aria-label="GitHub token"
              type="password"
              autoComplete="off"
              className={input}
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Personal access token"
            />
            <button
              disabled={!token}
              onClick={() => connect("github", { token })}
            >
              Connect GitHub
            </button>
            <button
              className="ml-5"
              onClick={() =>
                json("/connectors/github", { method: "DELETE" })
                  .then(reload)
                  .catch((e) => setStatus(String(e)))
              }
            >
              Disconnect
            </button>
          </section>
          <section className="border rounded-xl p-5">
            <h2 className="font-semibold">Google OAuth</h2>
            <p className="text-sm mt-2">
              Use your own OAuth application’s client credentials and an
              authorized refresh token for Gmail and Calendar. See the connector
              setup guide in the repository.
            </p>
            <input
              aria-label="Google client ID"
              className={input}
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              placeholder="Client ID"
            />
            <input
              aria-label="Google client secret"
              type="password"
              autoComplete="off"
              className={input}
              value={clientSecret}
              onChange={(e) => setClientSecret(e.target.value)}
              placeholder="Client secret"
            />
            <input
              aria-label="Google refresh token"
              type="password"
              autoComplete="off"
              className={input}
              value={refreshToken}
              onChange={(e) => setRefreshToken(e.target.value)}
              placeholder="Refresh token"
            />
            <button
              disabled={!clientId || !clientSecret || !refreshToken}
              onClick={() =>
                connect("google", {
                  client_id: clientId,
                  client_secret: clientSecret,
                  refresh_token: refreshToken,
                })
              }
            >
              Connect Google
            </button>
            <button
              className="ml-5"
              onClick={() =>
                json("/connectors/google", { method: "DELETE" })
                  .then(reload)
                  .catch((e) => setStatus(String(e)))
              }
            >
              Disconnect
            </button>
          </section>
          <section className="border rounded-xl p-5">
            <h2 className="font-semibold">Team workspace</h2>
            <input
              aria-label="New workspace name"
              className={input}
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Workspace name"
            />
            <button
              disabled={!name}
              onClick={() =>
                json("/workspaces", {
                  method: "POST",
                  body: JSON.stringify({ name }),
                })
                  .then((w) => {
                    localStorage.setItem("sentinel_workspace", w.id);
                    window.location.reload();
                  })
                  .catch((e) => setStatus(String(e)))
              }
            >
              Create workspace
            </button>
            <input
              aria-label="Member username"
              className={input}
              value={member}
              onChange={(e) => setMember(e.target.value)}
              placeholder="Existing user's username"
            />
            <button
              disabled={!member || !workspace()}
              onClick={() =>
                json(`/workspaces/${workspace()}/members`, {
                  method: "PUT",
                  body: JSON.stringify({ username: member }),
                })
                  .then(() => setStatus("Member added."))
                  .catch((e) => setStatus(String(e)))
              }
            >
              Add member to selected workspace
            </button>
          </section>
        </div>
      </main>
    </div>
  );
}
