from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    #LLM
    llm_provider : str ="gemini"
    google_api_key : str ="AIzaSyBG0A11TqZiPSH4HxplLT8vG9UtXVmu1y8"
    anthropic_api_key: str=""

    #vector DB
    pinecone_api_key:str ="pcsk_4RDtVi_Ac8hUU7yRp5Dn5ULUnnmNPTHi92oLCJ1hf3VnfXvNKVE5YQ6uCNsc6w2w8ak9Xc"
    pinecone_index: str = "portfolio-news"

    #News
    news_api_key : str="d695627d44164a81899d224557b77ef1"

    en: str="development"
    log_level : str="INFO"

    default_exchange_suffix : str=".NS"

    var_confidence : float=0.05
    var_window_days: int = 252
    risk_free_rate: float= 0.065

    class Config:
        env_file=".env"
        env_file_encoding="utf-8"
@lru_cache
def get_settings() -> Settings:
    return Settings()
