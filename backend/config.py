from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"
_DEFAULT_MCP_AUTH_TOKEN = "dev-secret-change-me"
_DEFAULT_JWT_SECRET_KEY = "sentinel-ai-dev-secret-change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    app_env: str = "development"

    # LLM
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "sonnet-4-6"
    openai_model: str = "gpt-4o"

    # GitHub connector
    github_token: str = ""
    github_default_repo: str = "octocat/Hello-World"

    # MCP server auth
    mcp_auth_token: str = _DEFAULT_MCP_AUTH_TOKEN

    # RAG
    chroma_persist_dir: str = ".chroma"
    rag_backend: str = "chroma"  # "chroma" or "pgvector"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Auth / JWT
    jwt_secret_key: str = _DEFAULT_JWT_SECRET_KEY
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    access_cookie_name: str = "sentinel_access_token"
    refresh_cookie_name: str = "sentinel_refresh_token"
    cookie_secure: bool = False

    # Database
    database_url: str = "sqlite:///sentinel.db"

    # Gmail / Calendar connectors (mock mode if empty)
    gmail_credentials_json: str = ""
    google_calendar_credentials_json: str = ""

    # File system connector
    workspace_dir: str = "./workspace"

    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = True


settings = Settings()


def _validate_security_settings() -> None:
    if settings.app_env.lower() in {"dev", "development", "test"}:
        return

    if settings.jwt_secret_key == _DEFAULT_JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be overridden outside development/test")

    if settings.mcp_auth_token == _DEFAULT_MCP_AUTH_TOKEN:
        raise ValueError("MCP_AUTH_TOKEN must be overridden outside development/test")


_validate_security_settings()
