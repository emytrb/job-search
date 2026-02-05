from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://jobsearcher:changeme@localhost:5432/jobsearcher"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # LLM Configuration
    # Provider: "groq", "ollama", "openai", "anthropic", etc.
    llm_provider: str = "groq"
    llm_model: str = "openai/gpt-oss-120b"

    # Provider-specific API keys
    groq_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Ollama (for local models)
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "B-A-M-N/vibethinker:1.5b"

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: str = ""

    # API
    secret_key: str = "change-this-secret-key"
    api_v1_prefix: str = "/api/v1"

    # Scraping
    scrape_rate_limit_min: float = 5.0  # seconds
    scrape_rate_limit_max: float = 15.0  # seconds

    # Scoring weights
    weight_stack_match: float = 0.35
    weight_seniority: float = 0.25
    weight_sponsorship: float = 0.25
    weight_quality: float = 0.15

    # Digest
    digest_max_jobs: int = 10
    digest_hour_utc: int = 8

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
