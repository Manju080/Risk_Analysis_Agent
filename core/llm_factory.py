"""
Model-agnostic LLM factory.
Swap provider by changing LLM_PROVIDER in .env — zero code changes elsewhere.
"""

from core.settings import get_settings

def get_llm(temperature: float = 0):
    settings = get_settings()

    if settings.llm_provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model ="gemini-2.5-flash",
            temperature=temperature,
            google_api_key  = settings.google_api_key,
        )
    elif settings.llm_provider == "haiku":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            temperature=temperature,
            anthropic_api_key=settings.anthropic_api_key,
        )
    elif settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="llama3.1", temperature=temperature)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {settings.llm_provider}")

_embedder = None

def get_embedder():
    """
    Always uses local BAAI/bge-small-en-v1.5 — free, no API key, good for finance text.
    Cached as a module-level singleton so the model is only downloaded once per process.
    """
    global _embedder
    if _embedder is None:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        _embedder = HuggingFaceEmbeddings(
            model_name="BAAI/bge-small-en-v1.5",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embedder
