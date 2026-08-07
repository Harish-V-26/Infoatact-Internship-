"""
Environment-based configuration.

The LLM call has been removed from this service - the proxy's job is
purely to de-identify a clinical note and return the redacted/tokenized
text. No credentials are needed for this service to run.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Redis - used by the tokenization vault (issues #50/#51, Sourish)
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Service
    log_level: str = "INFO"
    max_note_length: int = 20000


settings = Settings()
