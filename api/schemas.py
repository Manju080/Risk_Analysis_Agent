from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"

class Holding(BaseModel):
    ticker: str = Field(..., description="NSE ticker e.g. RELIANCE, TCS, INFY")
    quantity: float
    avg_buy_price: float

class PortfolioRequest(BaseModel):
    holdings: List[Holding]
    portfolio_name: Optional[str] = "My Portfolio"

class HoldingRisk(BaseModel):
    ticker: str
    current_price: float
    weight_pct: float
    var_1d_95: float          # 1-day 95% VaR as % of position
    sharpe_ratio: float
    beta: float               # vs NIFTY 50
    risk_level: RiskLevel
    news_summary: str         # RAG-grounded, 2-3 sentences

class RiskReport(BaseModel):
    portfolio_name: str
    total_value: float
    portfolio_var_1d_95: float
    portfolio_sharpe: float
    overall_risk_level: RiskLevel
    holdings: List[HoldingRisk]
    alerts: List[str]         # e.g. ["ADANIENT: high beta (1.8), elevated news risk"]
    recommendation: str       # LLM-synthesized, grounded only in tool outputs
    data_timestamp: str
    faithfulness_score: Optional[float] = None   # RAGAS score logged per request
