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
    llm_provider: str = "anthropic"  # "anthropic" or "ollama"

    # Anthropic (cloud, needs an API key)
    llm_api_key: str = ""
    llm_api_url: str = "https://api.anthropic.com/v1/messages"
    llm_model: str = "claude-sonnet-4-6"
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 3

    # Ollama (local, free, no API key - runs on your own machine)
    ollama_api_url: str = "http://localhost:11434/api/chat"
    ollama_model: str = "llama3.2"

    # Redis - used by the tokenization vault (issue #50/#51, Sourish/Rishi)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Service
    log_level: str = "INFO"
    max_note_length: int = 20000


settings = Settings()
