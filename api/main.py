import uuid
from agents.orchestrator import run_analysis
from api.schemas import PortfolioRequest, RiskReport
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
import sys
import os
import logging

# Fix for paths with spaces (Windows / Google Drive)
_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_dir)
os.chdir(_root)
if _root not in sys.path:
    sys.path.insert(0, _root)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Portfolio Risk Advisor",
    description="Multi-agent LLM system for NSE/BSE portfolio risk analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Portfolio Risk Advisor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "portfolio-risk-advisor"}


@app.get("/ping")
def ping():
    return {"pong": True}


@app.post("/analyze", response_model=RiskReport)
def analyze_portfolio(request: PortfolioRequest):
    if not request.holdings:
        raise HTTPException(
            status_code=400,
            detail="Portfolio must have at least one holding."
        )
    if len(request.holdings) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 holdings per request."
        )
    session_id = str(uuid.uuid4())
    try:
        report = run_analysis(request, session_id=session_id)
        return report
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Check API logs."}
    )
