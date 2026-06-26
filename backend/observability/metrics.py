"""Prometheus metrics for SentinelAI."""

from prometheus_client import Counter, Histogram, Info

APP_INFO = Info("sentinel_ai", "SentinelAI application info")
APP_INFO.info({"version": "0.1.0", "name": "sentinel-ai"})

REQUEST_COUNT = Counter(
    "sentinel_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "sentinel_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

TOOL_CALL_COUNT = Counter(
    "sentinel_tool_calls_total",
    "Total MCP tool calls",
    ["tool_name", "success"],
)

TOOL_CALL_LATENCY = Histogram(
    "sentinel_tool_call_duration_seconds",
    "MCP tool call latency in seconds",
    ["tool_name"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0],
)

LLM_REQUEST_COUNT = Counter(
    "sentinel_llm_requests_total",
    "Total LLM API requests",
    ["provider", "model"],
)

LLM_REQUEST_LATENCY = Histogram(
    "sentinel_llm_request_duration_seconds",
    "LLM API request latency in seconds",
    ["provider"],
)

RAG_RETRIEVAL_COUNT = Counter(
    "sentinel_rag_retrievals_total",
    "Total RAG retrieval queries",
)

AUTH_EVENTS = Counter(
    "sentinel_auth_events_total",
    "Authentication events",
    ["event_type"],  # login, register, token_refresh, auth_failure
)
