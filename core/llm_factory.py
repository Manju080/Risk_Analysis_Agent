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
            model="gemini-2.5-flash",
            temperature=temperature,
            google_api_key=settings.google_api_key,
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
    Uses Google's text-embedding-004 model via API to save server RAM.
    Render's free tier (512MB RAM) cannot hold PyTorch/sentence-transformers.
    """
    global _embedder
    if _embedder is None:
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        settings = get_settings()
        _embedder = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=settings.google_api_key,
        )
    return _embedder
