"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { getDocumentCount, getMe, uploadDocument } from "@/lib/api";

export default function DocumentsPage() {
  const router = useRouter();
  const [count, setCount] = useState<number | null>(null);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    getMe()
      .then((u) => {
        if (!u?.id) {
          router.push("/login");
          return;
        }
        setAuthChecked(true);
        refresh();
      })
      .catch(() => router.push("/login"));
  }, [router]);

  const refresh = () => {
    getDocumentCount()
      .then((d) => setCount(d.total_chunks ?? 0))
      .catch(() => setCount(0));
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setStatus(null);
    try {
      const result = await uploadDocument(file);
      if (result.status === "ingested") {
        setStatus({ ok: true, text: `Ingested ${result.chunks} chunks from ${result.filename}` });
        refresh();
      } else {
        setStatus({ ok: false, text: result.error || result.detail || "Upload failed" });
      }
    } catch {
      setStatus({ ok: false, text: "Upload error" });
    } finally {
      setUploading(false);
      e.target.value = "";
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />

      <main className="flex-1 overflow-y-auto">
        {!authChecked ? (
          <div className="flex h-full items-center justify-center text-[var(--muted)]">Loading...</div>
        ) : (
          <>
        <header className="px-6 py-4 border-b border-[var(--border)] bg-[var(--card)]">
          <h2 className="font-semibold">Knowledge Base</h2>
          <p className="text-xs text-[var(--muted)]">RAG documents indexed for semantic search</p>
        </header>

        <div className="max-w-3xl mx-auto p-6 space-y-6">
          <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
            <div className="text-sm text-[var(--muted)]">Total chunks indexed</div>
            <div className="text-4xl font-bold text-[var(--accent)] mt-1">
              {count === null ? "—" : count}
            </div>
          </div>

          <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
            <h3 className="font-semibold mb-2">Upload Document</h3>
            <p className="text-sm text-[var(--muted)] mb-4">
              Supported formats: Markdown (.md), PDF (.pdf), Text (.txt)
            </p>

            <label className="inline-block">
              <input
                type="file"
                accept=".md,.pdf,.txt"
                onChange={onUpload}
                disabled={uploading}
                className="hidden"
              />
              <span className="inline-block px-4 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg cursor-pointer transition">
                {uploading ? "Uploading..." : "Choose File"}
              </span>
            </label>

            {status && (
              <div
                className={`mt-4 px-4 py-2 rounded-lg text-sm border ${
                  status.ok
                    ? "bg-[var(--success)]/10 border-[var(--success)] text-[var(--success)]"
                    : "bg-[var(--danger)]/10 border-[var(--danger)] text-[var(--danger)]"
                }`}
              >
                {status.text}
              </div>
            )}
          </div>
        </div>
          </>
        )}
      </main>
    </div>
  );
}
