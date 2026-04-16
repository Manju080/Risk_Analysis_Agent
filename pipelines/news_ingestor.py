"""
News ingestion pipeline.
Fetches finance news → chunks → embeds → upserts into Pinecone.
Runs on schedule (APScheduler) or manually.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from newsapi import NewsApiClient
from pinecone import Pinecone
from core.settings import get_settings
from core.llm_factory import get_embedder

logger  = logging.getLogger(__name__)
settings = get_settings()


def _chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    words  = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def ingest_news_for_tickers(tickers: list[str]):
    """
    Fetch recent news for given NSE tickers, embed, and upsert to Pinecone.
    """
    newsapi  = NewsApiClient(api_key=settings.news_api_key)
    pc       = Pinecone(api_key=settings.pinecone_api_key)
    index    = pc.Index(settings.pinecone_index)
    embedder = get_embedder()

    from_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    for ticker in tickers:
        logger.info(f"Ingesting news for {ticker}")
        try:
            response = newsapi.get_everything(
                q=f"{ticker} NSE stock",
                from_param=from_date,
                language="en",
                sort_by="publishedAt",
                page_size=20,
            )
            articles = response.get("articles", [])
            
            vectors = []
            for article in articles:
                content = f"{article['title']}. {article.get('description', '')} {article.get('content', '')}"
                content = content[:1500]  # cap length
                
                chunks = _chunk_text(content)
                for i, chunk in enumerate(chunks):
                    uid = hashlib.md5(f"{ticker}_{article['url']}_{i}".encode()).hexdigest()
                    embedding = embedder.embed_query(chunk)
                    vectors.append({
                        "id": uid,
                        "values": embedding,
                        "metadata": {
                            "ticker": ticker,
                            "title": article["title"],
                            "source": article["source"]["name"],
                            "published_at": article["publishedAt"],
                            "url": article["url"],
                            "chunk": chunk,
                        }
                    })
            
            if vectors:
                index.upsert(vectors=vectors, namespace=ticker)
                logger.info(f"Upserted {len(vectors)} vectors for {ticker}")

        except Exception as e:
            logger.error(f"Failed to ingest news for {ticker}: {e}")


def start_scheduled_ingestor(tickers: list[str], interval_hours: int = 6):
    """Start APScheduler background job."""
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        ingest_news_for_tickers,
        "interval",
        hours=interval_hours,
        args=[tickers],
        next_run_time=datetime.now(),
    )
    scheduler.start()
    logger.info(f"News ingestor scheduled every {interval_hours}h for {tickers}")
    return scheduler
