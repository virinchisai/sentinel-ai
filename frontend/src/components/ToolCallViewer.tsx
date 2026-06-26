"use client";

import { useState } from "react";
import type { ChatResult } from "@/lib/api";

type ToolTrace = ChatResult["tool_traces"][number];

export default function ToolCallViewer({ traces }: { traces: ToolTrace[] }) {
  const [expanded, setExpanded] = useState<number | null>(null);

  if (!traces.length) return null;

  return (
    <div className="mt-3 space-y-1">
      <div className="text-xs text-[var(--muted)] mb-1">
        🔧 {traces.length} tool call{traces.length === 1 ? "" : "s"}
      </div>
      {traces.map((t, i) => (
        <div
          key={i}
          className="bg-[var(--background)] border border-[var(--border)] rounded-lg text-xs overflow-hidden"
        >
          <button
            onClick={() => setExpanded(expanded === i ? null : i)}
            className="w-full px-3 py-2 flex items-center justify-between hover:bg-[var(--card-hover)] transition"
          >
            <div className="flex items-center gap-2">
              <span className={t.success ? "text-[var(--success)]" : "text-[var(--danger)]"}>
                {t.success ? "✓" : "✗"}
              </span>
              <code className="font-mono">{t.tool_name}</code>
              <span className="text-[var(--muted)]">{t.duration_ms.toFixed(0)}ms</span>
            </div>
            <span className="text-[var(--muted)]">{expanded === i ? "▾" : "▸"}</span>
          </button>
          {expanded === i && (
            <div className="px-3 py-2 border-t border-[var(--border)] space-y-2">
              <div>
                <div className="text-[var(--muted)] mb-1">Arguments</div>
                <pre className="bg-[var(--card)] p-2 rounded overflow-x-auto">
                  {JSON.stringify(t.arguments, null, 2)}
                </pre>
              </div>
              <div>
                <div className="text-[var(--muted)] mb-1">Result</div>
                <pre className="bg-[var(--card)] p-2 rounded overflow-x-auto whitespace-pre-wrap">
                  {t.result}
                </pre>
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
