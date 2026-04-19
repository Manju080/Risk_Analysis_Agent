from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # LLM
    llm_provider: str = "gemini"
    google_api_key: str = ""
    anthropic_api_key: str = ""

    # Vector DB
    pinecone_api_key: str = ""
    pinecone_index: str = "portfolio-news"

    # News
    news_api_key: str = ""

    env: str = "development"
    log_level: str = "INFO"

    default_exchange_suffix: str = ".NS"

    var_confidence: float = 0.05
    var_window_days: int = 252
    risk_free_rate: float = 0.065

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
