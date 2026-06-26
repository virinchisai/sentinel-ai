"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearTokens, getMe } from "@/lib/api";

const NAV = [
  { href: "/chat", label: "Chat", icon: "💬" },
  { href: "/documents", label: "Documents", icon: "📄" },
  { href: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [user, setUser] = useState<{ username: string; role: string } | null>(null);

  useEffect(() => {
    getMe()
      .then((u) => u?.username && setUser(u))
      .catch(() => undefined);
  }, []);

  const logout = () => {
    clearTokens();
    router.push("/login");
  };

  return (
    <aside className="w-64 bg-[var(--card)] border-r border-[var(--border)] flex flex-col">
      <div className="p-6 border-b border-[var(--border)]">
        <h1 className="text-xl font-bold text-[var(--accent)]">SentinelAI</h1>
        <p className="text-xs text-[var(--muted)] mt-1">Enterprise AI Workspace</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {NAV.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg transition ${
                active
                  ? "bg-[var(--primary)] text-white"
                  : "text-[var(--foreground)] hover:bg-[var(--card-hover)]"
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-[var(--border)]">
        {user && (
          <div className="mb-3 px-2">
            <div className="text-sm font-medium">{user.username}</div>
            <div className="text-xs text-[var(--muted)] capitalize">{user.role}</div>
          </div>
        )}
        <button
          onClick={logout}
          className="w-full px-4 py-2 text-sm bg-[var(--background)] hover:bg-[var(--danger)]/20 border border-[var(--border)] rounded-lg transition"
        >
          Log out
        </button>
      </div>
    </aside>
  );
}
