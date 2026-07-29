"""
Environment-based configuration.

No secrets are ever hardcoded here. LLM_API_KEY and any other credential
must be provided via environment variables or a local .env file (which is
gitignored) - never committed to the repository.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM provider config
    llm_provider: str = "anthropic"
    llm_api_key: str = ""
    llm_api_url: str = "https://api.anthropic.com/v1/messages"
    llm_model: str = "claude-sonnet-4-6"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 3

    # Redis - used by the tokenization vault (issue #50/#51, Sourish/Rishi)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Service
    log_level: str = "INFO"
    max_note_length: int = 20000


settings = Settings()
