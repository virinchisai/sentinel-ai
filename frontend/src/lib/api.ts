const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const getToken = () =>
  typeof window === "undefined" ? null : localStorage.getItem("sentinel_token");
export function setToken(token: string) {
  localStorage.setItem("sentinel_token", token);
}
export function setRefreshToken(token: string) {
  localStorage.setItem("sentinel_refresh_token", token);
}
export function clearTokens() {
  localStorage.removeItem("sentinel_token");
  localStorage.removeItem("sentinel_refresh_token");
  localStorage.removeItem("sentinel_workspace");
  localStorage.removeItem("sentinel_upload_job");
}
export const isAuthenticated = () => !!getToken();
export const workspace = () =>
  typeof window === "undefined"
    ? ""
    : localStorage.getItem("sentinel_workspace") || "";
let refreshing: Promise<boolean> | null = null;
async function refresh() {
  const token = localStorage.getItem("sentinel_refresh_token");
  if (!token) return false;
  const r = await fetch(API_BASE + "/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: token }),
  });
  if (!r.ok) return false;
  const d = await r.json();
  setToken(d.access_token);
  setRefreshToken(d.refresh_token);
  return true;
}
export async function apiFetch(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<Response> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData))
    headers.set("Content-Type", "application/json");
  if (getToken()) headers.set("Authorization", `Bearer ${getToken()}`);
  const r = await fetch(API_BASE + path, { ...options, headers });
  if (r.status === 401 && retry && !path.startsWith("/auth/")) {
    refreshing ||= refresh().finally(() => {
      refreshing = null;
    });
    if (await refreshing) return apiFetch(path, options, false);
    clearTokens();
    window.dispatchEvent(new Event("sentinel:unauthorized"));
  }
  if (!r.ok) {
    const d = await r.json().catch(() => ({}));
    throw new Error(
      typeof d.detail === "string" ? d.detail : `Request failed (${r.status})`,
    );
  }
  return r;
}
export async function json(path: string, options: RequestInit = {}) {
  return (await apiFetch(path, options)).json();
}
export async function register(
  username: string,
  email: string,
  password: string,
) {
  return json("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
}
export async function login(username: string, password: string) {
  const d = await json("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(d.access_token);
  setRefreshToken(d.refresh_token);
  return d;
}
export async function logout() {
  try {
    await apiFetch("/auth/logout", { method: "POST" });
  } finally {
    clearTokens();
  }
}
export const getMe = () => json("/auth/me");
export interface Source {
  document_id: string;
  source: string;
  page: number;
  text: string;
  version: number;
}
export interface ChatResult {
  reply: string;
  session_id: string;
  tool_calls: string[];
  tool_traces: {
    tool_name: string;
    arguments: Record<string, unknown>;
    result: string;
    duration_ms: number;
    success: boolean;
  }[];
  needs_approval: boolean;
  pending_action: string;
  approval_id: string;
  sources: Source[];
}
export interface StreamEvent extends Partial<ChatResult> {
  type: string;
  text?: string;
  message?: string;
  tool?: string;
}
export async function streamChat(
  message: string,
  sessionId: string,
  onEvent: (e: StreamEvent) => void,
  signal: AbortSignal,
) {
  const r = await apiFetch("/chat/stream", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId,
      workspace_id: workspace() || null,
    }),
    signal,
  });
  const reader = r.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let end;
    while ((end = buffer.indexOf("\n\n")) >= 0) {
      const block = buffer.slice(0, end);
      buffer = buffer.slice(end + 2);
      if (block.startsWith("data: ")) onEvent(JSON.parse(block.slice(6)));
    }
  }
}
export async function uploadDocument(file: File) {
  const body = new FormData();
  body.append("file", file);
  const job = await json(
    "/documents/upload?background=true" +
      (workspace() ? `&workspace_id=${encodeURIComponent(workspace())}` : ""),
    { method: "POST", body },
  );
  localStorage.setItem("sentinel_upload_job", job.job_id);
  for (let i = 0; i < 600; i++) {
    await new Promise((r) => setTimeout(r, 1000));
    const status = await json("/documents/jobs/" + job.job_id);
    if (status.status === "completed") {
      localStorage.removeItem("sentinel_upload_job");
      return status.result;
    }
    if (["failed", "interrupted"].includes(status.status)) {
      localStorage.removeItem("sentinel_upload_job");
      throw new Error(
        status.result?.error || "Upload interrupted; re-upload to retry",
      );
    }
  }
  throw new Error(
    "Upload is still processing. Its job ID is saved in this browser.",
  );
}
export const getDocumentCount = () =>
  json(
    "/documents/list" +
      (workspace() ? `?workspace_id=${encodeURIComponent(workspace())}` : ""),
  );
export interface ConnectorStatus {
  name: string;
  mode: string;
  detail: string;
}
export const getConnectorStatus = (): Promise<ConnectorStatus[]> =>
  json("/connectors/status");
