"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import {
  getDocumentCount,
  uploadDocument,
  json,
  isAuthenticated,
} from "@/lib/api";
type Doc = {
  id: string;
  name: string;
  version: number;
  status: string;
  sha256: string;
};
export default function Documents() {
  const router = useRouter();
  const [docs, setDocs] = useState<Doc[]>([]),
    [count, setCount] = useState(0),
    [status, setStatus] = useState(""),
    [busy, setBusy] = useState(false),
    [preview, setPreview] = useState<{ name: string; content: string } | null>(
      null,
    );
  const refresh = () =>
    getDocumentCount().then((d) => {
      setDocs(d.documents);
      setCount(d.total_chunks);
    });
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    refresh().catch((e) => setStatus(String(e)));
    const id = new URLSearchParams(window.location.search).get("id");
    if (id)
      json("/documents/" + id)
        .then(setPreview)
        .catch((e) => setStatus(String(e)));
  }, [router]);
  async function remove(d: Doc) {
    if (!window.confirm(`Delete ${d.name} and its indexed chunks?`)) return;
    try {
      await json("/documents/" + d.id, { method: "DELETE" });
      setPreview(null);
      await refresh();
    } catch (e) {
      setStatus(String(e));
    }
  }
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto p-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-semibold">Knowledge base</h1>
          <p className="text-[var(--muted)] my-3">
            {count} {count === 1 ? "chunk" : "chunks"} · Documents are visible
            only to members of this workspace.
          </p>
          <label className="block border border-dashed rounded-xl p-6 my-6">
            Upload Markdown, UTF-8 text, or PDF (up to 20 MB). Upload the same
            filename to replace and reindex it.
            <input
              aria-label="Upload document"
              className="block mt-4"
              type="file"
              disabled={busy}
              accept=".md,.txt,.pdf"
              onChange={async (e) => {
                const f = e.target.files?.[0];
                if (!f) return;
                setBusy(true);
                setStatus("Extracting and indexing…");
                try {
                  const r = await uploadDocument(f);
                  setStatus(
                    `${r.filename}: ${r.chunks} chunks, version ${r.version} (${r.search_mode})`,
                  );
                  await refresh();
                } catch (err) {
                  setStatus(String(err));
                } finally {
                  setBusy(false);
                  e.target.value = "";
                }
              }}
            />
          </label>
          <p role="status">{status}</p>
          <div className="space-y-3 mt-5">
            {docs.map((d) => (
              <article
                className="border rounded-lg p-4 flex justify-between gap-4"
                key={d.id}
              >
                <div>
                  <button
                    className="font-semibold underline"
                    onClick={() =>
                      json("/documents/" + d.id)
                        .then(setPreview)
                        .catch((e) => setStatus(String(e)))
                    }
                  >
                    {d.name}
                  </button>
                  <p className="text-xs text-[var(--muted)] mt-1">
                    Version {d.version} · {d.status} · SHA-256{" "}
                    {d.sha256.slice(0, 12)}
                  </p>
                </div>
                <button onClick={() => remove(d)}>Delete</button>
              </article>
            ))}
          </div>
          {preview && (
            <section className="border rounded-xl p-6 mt-6">
              <div className="flex justify-between">
                <h2 className="font-semibold">{preview.name}</h2>
                <button onClick={() => setPreview(null)}>Close</button>
              </div>
              <pre className="whitespace-pre-wrap text-sm mt-4">
                {preview.content}
              </pre>
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
