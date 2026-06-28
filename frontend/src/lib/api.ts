const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const AUTH_FLAG_KEY = "sentinel_authenticated";

function getAuthFlag(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(AUTH_FLAG_KEY);
}

function setAuthenticated(value: boolean) {
  if (typeof window === "undefined") return;
  if (value) {
    sessionStorage.setItem(AUTH_FLAG_KEY, "1");
  } else {
    sessionStorage.removeItem(AUTH_FLAG_KEY);
  }
}

export function clearTokens() {
  setAuthenticated(false);
}

export function isAuthenticated(): boolean {
  return getAuthFlag() === "1";
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: "include" });

  if (res.status === 401) {
    clearTokens();
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }

  return res;
}

export async function register(username: string, email: string, password: string) {
  const res = await apiFetch("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, email, password }),
  });
  return res.json();
}

export async function login(username: string, password: string) {
  const res = await apiFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  const data = await res.json();
  if (data.authenticated) {
    setAuthenticated(true);
  }
  return data;
}

export async function getMe() {
  const res = await apiFetch("/auth/me");
  if (res.ok) {
    setAuthenticated(true);
  }
  return res.json();
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
}

export async function chat(
  message: string,
  sessionId: string = "default"
): Promise<ChatResult> {
  const res = await apiFetch("/chat", {
    method: "POST",
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  return res.json();
}

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });
  return res.json();
}

export async function getDocumentCount() {
  const res = await apiFetch("/documents/list");
  return res.json();
}

export interface ConnectorStatus {
  name: string;
  mode: "live" | "mock" | "demo" | "empty" | "no_key";
  detail: string;
}

export async function getConnectorStatus(): Promise<ConnectorStatus[]> {
  const res = await apiFetch("/admin/connector-status");
  return res.json();
}

export async function logout() {
  const res = await apiFetch("/auth/logout", { method: "POST" });
  clearTokens();
  return res;
}
