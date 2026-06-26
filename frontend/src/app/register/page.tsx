"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { register, login } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await register(username, email, password);
      if (data.id) {
        await login(username, password);
        router.push("/chat");
      } else {
        setError(data.detail || "Registration failed");
      }
    } catch {
      setError("Connection error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-[var(--accent)]">SentinelAI</h1>
          <p className="text-[var(--muted)] mt-2">Create your workspace account</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-[var(--card)] rounded-xl p-8 shadow-xl border border-[var(--border)]">
          <h2 className="text-xl font-semibold mb-6">Register</h2>

          {error && (
            <div className="bg-[var(--danger)]/10 border border-[var(--danger)] text-[var(--danger)] px-4 py-2 rounded-lg mb-4 text-sm">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label className="block text-sm text-[var(--muted)] mb-1">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--primary)]"
              required
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm text-[var(--muted)] mb-1">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--primary)]"
              required
            />
          </div>

          <div className="mb-6">
            <label className="block text-sm text-[var(--muted)] mb-1">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg focus:outline-none focus:border-[var(--primary)]"
              required
              minLength={8}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg font-medium transition disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Create Account"}
          </button>

          <p className="text-center text-sm text-[var(--muted)] mt-4">
            Already have an account?{" "}
            <Link href="/login" className="text-[var(--primary)] hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
