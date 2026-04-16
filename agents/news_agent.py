"""
News RAG agent — retrieves relevant news chunks from Pinecone for a ticker.
Uses LLM to summarise retrieved context into 2-3 sentences.
"""
import logging
from pinecone import Pinecone
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from core.settings import get_settings
from core.llm_factory import get_embedder,get_llm

logger = logging.getLogger(__name__)
settings = get_settings()

NEWS_SUMMARY_PROMPT = PromptTemplate.from_template("""
You are a financial analyst. Below are recent news excerpts about {ticker} stock on the NSE.
Summarise ONLY what is stated in these excerpts in 2-3 sentences.
Do NOT add any external knowledge or opinions beyond what is written here.
If the news is neutral or there is nothing significant, say so clearly.

News excerpts:
{context}

Summary (2-3 sentences, grounded only in the excerpts above):
""")


def retriver_news(ticker: str, top_k: int =5) -> list[dict]:
    """
    Semantic search in Pinecone for a ticker's news namespace.
    Returns list of metadata dicts with chunk + source + published_at.
    """
    pc = Pinecone(api_key = settings.pinecone_api_key)
    index    = pc.Index(settings.pinecone_index)
    embedder = get_embedder()

    query_vec = embedder.embed_query(f"{ticker} NSE stock performance risk earnings")
    
    results = index.query(
        vector=query_vec,
        top_k=top_k,
        namespace=ticker,
        include_metadata=True,
    )

    chunks = []
    for match in results.matches:
        chunks.append({
            "score": round(match.score, 3),
            "chunk": match.metadata.get("chunk", ""),
            "source": match.metadata.get("source", ""),
            "published_at": match.metadata.get("published_at", ""),
            "title": match.metadata.get("title", ""),
            "url": match.metadata.get("url", ""),
        })
    
    logger.info(f"Retrieved {len(chunks)} chunks for {ticker} (top score: {chunks[0]['score'] if chunks else 'n/a'})")
    return chunks


def summarise_news(ticker: str) -> dict:
    """
    Retrieves chunks and generates a grounded LLM summary.
    Returns summary text + source citations.
    """
    chunks = retriver_news(ticker)
    
    if not chunks:
        return {
            "summary": "No recent news found for this ticker in the indexed sources.",
            "sources": [],
            "retrieved_chunks": [],
        }
    
    # Build context string with source tags for traceability
    context = "\n\n".join([
        f"[Source: {c['source']} | {c['published_at'][:10]}]\n{c['chunk']}"
        for c in chunks
    ])
    
    llm   = get_llm(temperature=0)
    chain = NEWS_SUMMARY_PROMPT | llm | StrOutputParser()
    
    summary = chain.invoke({"ticker": ticker, "context": context})
    
    sources = [
        {"title": c["title"], "source": c["source"], "published_at": c["published_at"], "url": c["url"]}
        for c in chunks
    ]
    
    return {
        "summary": summary.strip(),
        "sources": sources,
        "retrieved_chunks": chunks,  # kept for RAGAS eval
    }

