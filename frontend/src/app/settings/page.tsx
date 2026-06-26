"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { getMe, isAuthenticated } from "@/lib/api";

export default function SettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<{ id: number; username: string; email: string; role: string } | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push("/login");
      return;
    }
    getMe()
      .then((u) => u?.id && setUser(u))
      .catch(() => undefined);
  }, [router]);

  return (
    <div className="flex h-screen">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
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

          <section className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
            <h3 className="font-semibold mb-2">Connected Tools</h3>
            <p className="text-sm text-[var(--muted)] mb-4">
              MCP connectors available to the agent
            </p>
            <ul className="grid grid-cols-2 gap-2 text-sm">
              {[
                "GitHub",
                "Gmail",
                "Calendar",
                "File System",
                "PostgreSQL",
                "Knowledge Base (RAG)",
              ].map((tool) => (
                <li key={tool} className="px-3 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg flex items-center gap-2">
                  <span className="text-[var(--success)]">●</span>
                  {tool}
                </li>
              ))}
            </ul>
          </section>
        </div>
      </main>
    </div>
  );
}
