from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    # LLM
    llm_provider: str = "ollama"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "sonnet-4-6"
    openai_model: str = "gpt-4o"

    ollama_base_url: str = "http://localhost:11434"
    document_parser: str = "basic"
    embedding_model: str = ""
    ollama_model: str = "qwen2.5:1.5b"
    request_timeout: int = 300
    data_dir: str = "./data"
    max_upload_bytes: int = 20 * 1024 * 1024
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"
    github_allowed_repos: str = ""
    environment: str = "development"

    # GitHub connector
    github_token: str = ""
    github_default_repo: str = "octocat/Hello-World"

    # MCP server auth
    mcp_auth_token: str = "dev-secret-change-me"

    # RAG

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Auth / JWT
    jwt_secret_key: str = "sentinel-ai-dev-secret-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Database
    tool_database_url: str = ""
    database_url: str = "sqlite:///sentinel.db"

    # Gmail / Calendar connectors (mock mode if empty)
    gmail_credentials_json: str = ""
    google_calendar_credentials_json: str = ""

    # File system connector
    workspace_dir: str = "./workspace"

    enable_langfuse: bool = False
    oidc_issuer: str = ""
    oidc_client_id: str = ""
    oidc_redirect_uri: str = "http://localhost:3000/login"

    # Observability
    log_level: str = "INFO"
    enable_metrics: bool = True


settings = Settings()
