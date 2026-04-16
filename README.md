# Agentic Portfolio Risk Advisor

> Multi-agent LLM system for real-time NSE/BSE portfolio risk analysis

[![CI](https://github.com/yourusername/portfolio-risk-advisor/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/portfolio-risk-advisor/actions)
[![Python 3.11](https://img.shields.io/badge/python-3.11-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-orange.svg)](https://langchain.com)

## Architecture

```
User (Streamlit UI)
    ↓
FastAPI Orchestration Layer
    ↓
Orchestrator Agent (LangChain + Gemini 1.5 Flash)
    ↓ delegates to
┌───────────────┬──────────────────┬────────────────┬──────────────┐
│  Price Agent  │  Risk Agent      │  News Agent    │ Memory Agent │
│  yfinance     │  VaR·Sharpe·Beta │  Pinecone RAG  │  SQLite      │
│  Live prices  │  vs NIFTY 50     │  NewsAPI       │  History     │
└───────────────┴──────────────────┴────────────────┴──────────────┘
```

## Features

- **Real-time NSE prices** via yfinance — live OHLCV, auto .NS suffix
- **Quantitative risk** — Historical VaR (95%), Sharpe ratio, Beta vs NIFTY 50
- **RAG news intelligence** — Pinecone vector search, source-cited summaries
- **LLM synthesis** — Gemini 1.5 Flash at temperature=0, structured Pydantic output
- **Conversation memory** — SQLite-backed session history
- **Production UI** — Dark theme Streamlit dashboard with Plotly charts
- **Model-agnostic** — swap Gemini → Claude Haiku → Ollama in one env var

## Stack

| Layer | Technology |
|-------|-----------|
| LLM | Gemini 1.5 Flash (free) / Claude Haiku 4.5 |
| Orchestration | LangChain AgentExecutor |
| Embeddings | BAAI/bge-small-en-v1.5 (local, free) |
| Vector DB | Pinecone (free tier) |
| API | FastAPI + Uvicorn |
| UI | Streamlit + Plotly |
| Data | yfinance + NewsAPI |
| Memory | SQLite via LangChain |

## Setup

### 1. Clone and install
```bash
git clone https://github.com/yourusername/portfolio-risk-advisor
cd portfolio-risk-advisor
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Fill in: GOOGLE_API_KEY, PINECONE_API_KEY, NEWS_API_KEY
```

### 3. Create Pinecone index
- Name: `portfolio-news` · Dimensions: `384` · Metric: `cosine`

### 4. Run tests
```bash
pytest tests/test_risk_agent.py -v
```

### 5. Start services
```bash
# Terminal 1
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2
streamlit run ui/app.py
```

Open `http://localhost:8501`

## Deployment

### FastAPI → Render
1. Push to GitHub
2. New Web Service on [render.com](https://render.com)
3. Connect repo → Build: `pip install -r requirements.txt`
4. Start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add env vars: `GOOGLE_API_KEY`, `PINECONE_API_KEY`, `NEWS_API_KEY`

### Streamlit UI → Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub repo → set main file: `ui/app.py`
3. Add secret: `API_URL = "https://your-render-url.onrender.com"`

## Resume Bullets

> Built a multi-agent LLM system using LangChain and Gemini 1.5 Flash that orchestrates real-time NSE price feeds, RAG-based news retrieval via Pinecone, and quantitative risk calculations (VaR 95%, Sharpe ratio, Beta vs NIFTY 50) to generate plain-language portfolio health reports via FastAPI + Streamlit.

> Designed model-agnostic LLM factory supporting Gemini, Claude Haiku, and Ollama with zero code changes; implemented conversation memory via SQLite-backed LangChain history and structured Pydantic output schemas to eliminate LLM hallucination of financial metrics.

## Disclaimer

Educational purposes only. Not financial advice. Consult a SEBI-registered advisor.
