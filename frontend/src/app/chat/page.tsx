"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ToolCallViewer from "@/components/ToolCallViewer";
import {
  streamChat,
  json,
  workspace,
  isAuthenticated,
  ChatResult,
} from "@/lib/api";
type Message = { role: string; content: string; result?: ChatResult };
type Approval = {
  id: string;
  tool: string;
  arguments: Record<string, unknown>;
};
const suffix = () =>
  workspace() ? `?workspace_id=${encodeURIComponent(workspace())}` : "";
export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]),
    [input, setInput] = useState(""),
    [busy, setBusy] = useState(false),
    [status, setStatus] = useState(""),
    [session, setSession] = useState(""),
    [sessions, setSessions] = useState<{ session_id: string }[]>([]),
    [approvals, setApprovals] = useState<Approval[]>([]);
  const abort = useRef<AbortController | null>(null);
  const reload = useCallback(() => {
    json("/chat/sessions" + suffix())
      .then(setSessions)
      .catch(() => {});
    json("/approvals" + suffix())
      .then(setApprovals)
      .catch(() => {});
  }, []);
  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/login");
      return;
    }
    setSession(crypto.randomUUID());
    reload();
    return () => abort.current?.abort();
  }, [reload, router]);
  async function select(id: string) {
    setSession(id);
    setMessages(await json("/chat/sessions/" + id + suffix()));
  }
  async function send() {
    if (!input.trim() || busy) return;
    const text = input;
    setInput("");
    setBusy(true);
    setStatus("Connecting to model…");
    setMessages((m) => [
      ...m,
      { role: "user", content: text },
      { role: "assistant", content: "" },
    ]);
    abort.current = new AbortController();
    try {
      await streamChat(
        text,
        session,
        (e) => {
          if (e.type === "token")
            setMessages((m) =>
              m.map((v, i) =>
                i === m.length - 1
                  ? { ...v, content: v.content + (e.text || "") }
                  : v,
              ),
            );
          if (e.type === "tool_start") setStatus(`Using ${e.tool}…`);
          if (e.type === "response") {
            setMessages((m) =>
              m.map((v, i) =>
                i === m.length - 1
                  ? {
                      role: "assistant",
                      content: e.reply || "",
                      result: e as ChatResult,
                    }
                  : v,
              ),
            );
            setStatus("");
          }
          if (e.type === "error") throw new Error(e.message);
        },
        abort.current.signal,
      );
    } catch (e) {
      setStatus(
        e instanceof Error && e.name === "AbortError"
          ? "Stopped. Start a new conversation if a tool was interrupted."
          : String(e),
      );
    } finally {
      setBusy(false);
      reload();
    }
  }
  async function decide(id: string, approve: boolean) {
    setBusy(true);
    try {
      const r = await json("/approvals/" + id, {
        method: "POST",
        body: JSON.stringify({ approve }),
      });
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content: `Action ${r.status}${r.result ? ": " + r.result : ""}`,
        },
      ]);
    } catch (e) {
      setStatus(String(e));
    } finally {
      setBusy(false);
      reload();
    }
  }
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0 flex flex-col">
        <header className="p-4 border-b border-[var(--border)] flex gap-3 items-center">
          <h2 className="font-semibold">Investigation workspace</h2>
          <select
            aria-label="Conversation"
            value={session}
            onChange={(e) => select(e.target.value)}
            disabled={busy}
            className="bg-[var(--card)] p-2 rounded"
          >
            <option value={session}>
              {session.slice(0, 8) || "New conversation"}
            </option>
            {sessions
              .filter((s) => s.session_id !== session)
              .map((s) => (
                <option key={s.session_id} value={s.session_id}>
                  {s.session_id.slice(0, 8)}
                </option>
              ))}
          </select>
          <button
            disabled={busy}
            onClick={() => {
              setSession(crypto.randomUUID());
              setMessages([]);
              setStatus("");
            }}
          >
            New chat
          </button>
        </header>
        <div className="flex-1 overflow-y-auto p-6 space-y-5">
          <div className="max-w-3xl mx-auto space-y-5">
            {!messages.length && (
              <div className="py-16">
                <p className="text-xs uppercase tracking-widest text-[var(--accent)]">
                  Private evidence. Controlled actions.
                </p>
                <h1 className="text-3xl font-semibold mt-3">
                  What are we investigating?
                </h1>
                <p className="mt-3 text-[var(--muted)]">
                  Upload a runbook, connect GitHub, and ask a question. Review
                  sources and approve each proposed change.
                </p>
                <button
                  className="mt-6 p-3 border rounded"
                  onClick={() =>
                    setInput(
                      "What does our incident response policy require? Cite the source.",
                    )
                  }
                >
                  Review the incident response policy
                </button>
              </div>
            )}
            {messages.map((m, i) => (
              <article
                key={i}
                className={`p-4 rounded-xl ${m.role === "user" ? "bg-[var(--primary)]/20" : "bg-[var(--card)]"}`}
              >
                <p className="text-xs text-[var(--muted)] mb-2">
                  {m.role === "user" ? "You" : "SentinelAI"}
                </p>
                <p className="whitespace-pre-wrap text-sm">
                  {m.content || "Thinking…"}
                </p>
                {m.result?.tool_traces?.length ? (
                  <ToolCallViewer traces={m.result.tool_traces} />
                ) : null}
                {m.result?.sources?.map((s, j) => (
                  <details key={j} className="mt-3 text-sm border rounded p-2">
                    <summary>
                      <Link href={`/documents?id=${s.document_id}`}>
                        {s.source} · page {s.page} · v{s.version}
                      </Link>
                    </summary>
                    <p className="mt-2 whitespace-pre-wrap">{s.text}</p>
                  </details>
                ))}
              </article>
            ))}
            {approvals.map((a) => (
              <section
                key={a.id}
                className="border border-amber-500 rounded-xl p-4"
              >
                <h3 className="font-semibold">Review action: {a.tool}</h3>
                <pre className="text-xs overflow-auto my-3">
                  {JSON.stringify(a.arguments, null, 2)}
                </pre>
                <p className="text-xs mb-3">
                  Approval expires after 10 minutes. This exact action can run
                  once.
                </p>
                <button
                  disabled={busy}
                  className="bg-[var(--primary)] px-4 py-2 rounded mr-3"
                  onClick={() => decide(a.id, true)}
                >
                  Approve action
                </button>
                <button disabled={busy} onClick={() => decide(a.id, false)}>
                  Reject
                </button>
              </section>
            ))}
          </div>
        </div>
        <footer className="p-4 border-t border-[var(--border)]">
          <p role="status" className="text-sm mb-2 max-w-3xl mx-auto">
            {status}
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
            className="max-w-3xl mx-auto flex gap-3"
          >
            <textarea
              aria-label="Message"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 bg-[var(--card)] border rounded-lg p-3"
              placeholder="Ask about your documents or connected tools"
            />
            {busy ? (
              <button type="button" onClick={() => abort.current?.abort()}>
                Stop
              </button>
            ) : (
              <button
                disabled={!input.trim()}
                className="bg-[var(--primary)] rounded-lg px-5"
              >
                Send
              </button>
            )}
          </form>
        </footer>
      </main>
    </div>
  );
}
