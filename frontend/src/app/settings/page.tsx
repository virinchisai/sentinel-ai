"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { getConnectorStatus, getMe, type ConnectorStatus } from "@/lib/api";

const MODE_STYLE: Record<ConnectorStatus["mode"], { label: string; color: string; dot: string }> = {
  live:   { label: "Live",      color: "text-[var(--success)]", dot: "bg-[var(--success)]" },
  demo:   { label: "Demo",      color: "text-[var(--accent)]",  dot: "bg-[var(--accent)]" },
  mock:   { label: "Mock",      color: "text-yellow-400",       dot: "bg-yellow-400" },
  empty:  { label: "Empty",     color: "text-[var(--muted)]",   dot: "bg-[var(--muted)]" },
  no_key: { label: "No API Key", color: "text-[var(--danger)]", dot: "bg-[var(--danger)]" },
};

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: number; username: string; email: string; role: string } | null>(null);
  const [connectors, setConnectors] = useState<ConnectorStatus[]>([]);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    getMe()
      .then((u) => {
        if (!u?.id) {
          router.push("/login");
          return;
        }
        setUser(u);
        setAuthChecked(true);
        if (u.role === "admin") {
          getConnectorStatus()
            .then((s) => Array.isArray(s) && setConnectors(s))
            .catch(() => undefined);
        }
      })
      .catch(() => router.push("/login"));
  }, [router]);

  return (
    <div className="flex h-screen">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        {!authChecked ? (
          <div className="flex h-full items-center justify-center text-[var(--muted)]">Loading...</div>
        ) : (
          <>
        <header className="px-6 py-4 border-b border-[var(--border)] bg-[var(--card)]">
          <h2 className="font-semibold">Settings</h2>
          <p className="text-xs text-[var(--muted)]">Account and workspace configuration</p>
        </header>

        <div className="max-w-3xl mx-auto p-6 space-y-6">
          <section className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
            <h3 className="font-semibold mb-4">Profile</h3>
            {user ? (
              <dl className="grid grid-cols-2 gap-y-3 text-sm">
                <dt className="text-[var(--muted)]">User ID</dt>
                <dd>{user.id}</dd>
                <dt className="text-[var(--muted)]">Username</dt>
                <dd>{user.username}</dd>
                <dt className="text-[var(--muted)]">Email</dt>
                <dd>{user.email}</dd>
                <dt className="text-[var(--muted)]">Role</dt>
                <dd className="capitalize">{user.role}</dd>
              </dl>
            ) : (
              <div className="text-[var(--muted)]">Loading...</div>
            )}
          </section>

          {user?.role === "admin" ? (
          <section className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
            <h3 className="font-semibold mb-2">Connector Status</h3>
            <p className="text-sm text-[var(--muted)] mb-4">
              Real status from the backend. Mock connectors return realistic sample data — to switch them to live, set the relevant credentials in <code className="text-xs bg-[var(--background)] px-1 rounded">.env</code>.
            </p>
            {connectors.length === 0 ? (
              <div className="text-[var(--muted)] text-sm">Loading status...</div>
            ) : (
              <ul className="space-y-2">
                {connectors.map((c) => {
                  const style = MODE_STYLE[c.mode];
                  return (
                    <li key={c.name} className="px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg flex items-start gap-3">
                      <span className={`mt-1.5 w-2 h-2 rounded-full ${style.dot} flex-shrink-0`}></span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-baseline gap-2 flex-wrap">
                          <span className="font-medium">{c.name}</span>
                          <span className={`text-xs uppercase tracking-wider ${style.color}`}>{style.label}</span>
                        </div>
                        <div className="text-xs text-[var(--muted)] mt-0.5">{c.detail}</div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
          ) : null}
        </div>
          </>
        )}
      </main>
    </div>
  );
}
