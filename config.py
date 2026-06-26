from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    openai_model: str = "gpt-4o"

    github_token: str = ""
    github_default_repo: str = "octocat/Hello-World"

    mcp_auth_token: str = "dev-secret-change-me"

    chroma_persist_dir: str = ".chroma"

    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
