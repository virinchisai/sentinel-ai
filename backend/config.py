from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

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
    mcp_auth_token: str = "dev-secret-change-me"

    # RAG
    chroma_persist_dir: str = ".chroma"
    rag_backend: str = "chroma"  # "chroma" or "pgvector"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Auth / JWT
    jwt_secret_key: str = "sentinel-ai-dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

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
