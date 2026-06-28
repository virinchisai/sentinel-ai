"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import ToolCallViewer from "@/components/ToolCallViewer";
import { chat, getMe, type ChatResult } from "@/lib/api";

type Message = {
  role: "user" | "assistant" | "system";
  content: string;
  result?: ChatResult;
};

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [authChecked, setAuthChecked] = useState(false);
  const [sessionId] = useState(() => `web-${Date.now()}`);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getMe()
      .then((u) => {
        if (!u?.id) {
          router.push("/login");
          return;
        }
        setAuthChecked(true);
      })
      .catch(() => router.push("/login"));
  }, [router]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setMessages((m) => [...m, { role: "user", content: text }]);
    setLoading(true);

    try {
      const result = await chat(text, sessionId);
      const reply = result.reply || (result as { detail?: string }).detail || "(no response)";
      setMessages((m) => [
        ...m,
        { role: "assistant", content: reply, result },
      ]);
    } catch (e) {
      setMessages((m) => [
        ...m,
        { role: "system", content: `Error: ${e instanceof Error ? e.message : "unknown"}` },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const examples = [
    "What are our password requirements?",
    "Search Gmail for recent incident reports",
    "List events on my calendar this week",
    "Show me employees in the Engineering department",
  ];

  return (
    <div className="flex h-screen">
      <Sidebar />

      <main className="flex-1 flex flex-col">
        {!authChecked ? (
          <div className="flex-1 flex items-center justify-center text-[var(--muted)]">Loading...</div>
        ) : (
          <>
        <header className="px-6 py-4 border-b border-[var(--border)] bg-[var(--card)]">
          <h2 className="font-semibold">Chat</h2>
          <p className="text-xs text-[var(--muted)]">Session {sessionId}</p>
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && (
            <div className="max-w-2xl mx-auto text-center">
              <h3 className="text-2xl font-semibold mb-2">How can SentinelAI help?</h3>
              <p className="text-[var(--muted)] mb-8">
                Ask about company docs, your calendar, internal databases, GitHub, or email.
              </p>
              <div className="grid grid-cols-2 gap-3 text-left">
                {examples.map((e) => (
                  <button
                    key={e}
                    onClick={() => setInput(e)}
                    className="p-3 bg-[var(--card)] hover:bg-[var(--card-hover)] border border-[var(--border)] rounded-lg text-sm transition"
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                    m.role === "user"
                      ? "bg-[var(--primary)] text-white"
                      : m.role === "system"
                        ? "bg-[var(--danger)]/10 border border-[var(--danger)] text-[var(--danger)]"
                        : "bg-[var(--card)] border border-[var(--border)]"
                  }`}
                >
                  <div className="whitespace-pre-wrap text-sm">{m.content}</div>
                  {m.result?.needs_approval && (
                    <div className="mt-2 text-xs text-[var(--accent)]">
                      ⚠ Action requires approval: {m.result.pending_action}
                    </div>
                  )}
                  {m.result?.tool_traces?.length ? (
                    <ToolCallViewer traces={m.result.tool_traces} />
                  ) : null}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex justify-start">
                <div className="bg-[var(--card)] border border-[var(--border)] rounded-2xl px-4 py-3 text-sm text-[var(--muted)]">
                  <span className="inline-block animate-pulse">●●●</span> thinking...
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="border-t border-[var(--border)] p-4 bg-[var(--card)]">
          <div className="max-w-3xl mx-auto flex gap-2">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Message SentinelAI..."
              rows={1}
              className="flex-1 px-4 py-2 bg-[var(--background)] border border-[var(--border)] rounded-lg resize-none focus:outline-none focus:border-[var(--primary)]"
            />
            <button
              onClick={send}
              disabled={loading || !input.trim()}
              className="px-6 py-2 bg-[var(--primary)] hover:bg-[var(--primary-hover)] text-white rounded-lg font-medium transition disabled:opacity-50"
            >
              Send
            </button>
          </div>
        </div>
          </>
        )}
      </main>
    </div>
  );
}
