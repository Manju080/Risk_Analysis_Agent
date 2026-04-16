# Deployment Steps — Step by Step

## Step 1 — Push to GitHub

```bash
cd your-project-folder
git init
git add .
git commit -m "feat: initial production release"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/portfolio-risk-advisor.git
git push -u origin main
```

## Step 2 — Deploy FastAPI to Render (free)

1. Go to https://render.com → Sign up with GitHub
2. Click "New +" → "Web Service"
3. Connect your GitHub repo
4. Fill in:
   - Name: `portfolio-risk-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
5. Add Environment Variables (click "Add Environment Variable"):
   - `GOOGLE_API_KEY` → your key
   - `PINECONE_API_KEY` → your key
   - `PINECONE_INDEX` → portfolio-news
   - `NEWS_API_KEY` → your key
   - `LLM_PROVIDER` → gemini
6. Click "Create Web Service"
7. Wait ~3 mins for build. Copy your URL: `https://portfolio-risk-api.onrender.com`

## Step 3 — Deploy Streamlit UI to Streamlit Cloud (free)

1. Go to https://share.streamlit.io → Sign in with GitHub
2. Click "New app"
3. Select your repo → Branch: main → Main file: `ui/app.py`
4. Click "Advanced settings" → Secrets:
```toml
API_URL = "https://portfolio-risk-api.onrender.com"
```
5. Click "Deploy"
6. Your app is live at: `https://yourname-portfolio-risk-advisor.streamlit.app`

## Step 4 — Update app.py to read API_URL from secrets

Add this to the top of ui/app.py (already done in the production version):
```python
import os
API_URL = os.getenv("API_URL", "http://localhost:8000")
```

Streamlit Cloud injects secrets as environment variables automatically.

## Step 5 — Verify deployment

1. Open your Streamlit URL
2. Enter: RELIANCE (10 qty, ₹2800) + TCS (5 qty, ₹4000)
3. Click Run Analysis
4. Should return full risk report in ~30-60 seconds

## Troubleshooting

**Render cold start**: Free tier sleeps after 15 mins. First request takes ~30s to wake up.
Add a loading message in Streamlit:
```python
st.info("API may take 30s to wake up on first request (free tier)")
```

**Pinecone empty**: Run news ingestion once after deployment:
```python
from pipelines.news_ingestor import ingest_news_for_tickers
ingest_news_for_tickers(["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK"])
```
