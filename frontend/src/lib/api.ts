const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("sentinel_token");
}

export function setToken(token: string) {
  localStorage.setItem("sentinel_token", token);
}

export function setRefreshToken(token: string) {
  localStorage.setItem("sentinel_refresh_token", token);
}

export function clearTokens() {
  localStorage.removeItem("sentinel_token");
  localStorage.removeItem("sentinel_refresh_token");
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

async function apiFetch(path: string, options: RequestInit = {}) {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

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
  if (data.access_token) {
    setToken(data.access_token);
    setRefreshToken(data.refresh_token);
  }
  return data;
}

export async function getMe() {
  const res = await apiFetch("/auth/me");
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
  const token = getToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
  });
  return res.json();
}

export async function getDocumentCount() {
  const res = await apiFetch("/documents/list");
  return res.json();
}
