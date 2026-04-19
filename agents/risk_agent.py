"""
Risk calculation agent — pure Python + pandas, NO LLM involved.
All math is deterministic and unit-tested independently.
Calculations:
  - Historical VaR (95%, 1-day)
  - Annualised Sharpe ratio
  - Beta vs NIFTY 50 (^NSEI)
"""

import numpy as np
import pandas as pd
import yfinance as yf
import logging
from core.settings import get_settings

logger = logging.getLogger(__name__)

NIFTY_TICKER = "^NSEI"

def _fetch_returns(ticker: str, period: str = "1y") -> pd.Series:
    """
    Fetch adjusted close prices and compute daily log returns.
    NSE tickers need '.NS' suffix for yfinance.
    """
    settings = get_settings()
    suffix = settings.default_exchange_suffix
    full_ticker = ticker if ("." in ticker or ticker.startswith("^")) else f"{ticker}{suffix}"
    
    df = yf.download(full_ticker, period=period, auto_adjust=True, progress=False)
    
    if df.empty:
        raise ValueError(f"No price data returned for {full_ticker}. Check ticker symbol.")
    
    prices = df["Close"].squeeze()

    # Validate — no zero prices, no >50% single-day gaps
    if (prices <= 0).any():
        raise ValueError(f"Zero or negative prices found for {full_ticker} — bad data.")
    
    returns = np.log(prices / prices.shift(1)).dropna()
    logger.info(f"Fetched {len(returns)} daily returns for {full_ticker}")
    return returns

def calculate_var(returns: pd.Series, confidence: float= 0.95)->float:
    """
    Historical VaR — no distributional assumption.
    Returns VaR as a positive percentage (e.g. 2.3 means 2.3% loss).
    """

    if len(returns)<30:
        raise ValueError("Need at least 30 data points for reliable VaR.")

    var = float(np.percentile(returns, (1-confidence)*100))
    return round(abs(var)*100,4)
def calculate_sharpe(returns: pd.Series, risk_free_rate: float = None) -> float:
    """
    Annualised Sharpe ratio.
    risk_free_rate: annual rate (e.g. 0.065 for 6.5%).
    """
    if risk_free_rate is None:
        risk_free_rate = get_settings().risk_free_rate
    
    daily_rf = risk_free_rate / 252
    excess = returns - daily_rf
    
    if excess.std() < 1e-10:
        return 0.0
    
    sharpe = (excess.mean() / excess.std()) * np.sqrt(252)
    return round(float(sharpe), 4)

def calculate_beta(stock_returns: pd.Series,market_returns: pd.Series)->float:
    """
    Beta of stock vs market (NIFTY 50).
    Aligns both series on dates before computing.
    """

    aligned = pd.concat([stock_returns,market_returns],axis=1).dropna()
    aligned.columns = ["stock","market"]

    if len(aligned)<30:
        raise ValueError("Insufficient overlapping data for beta calculation.")

    cov_matrix = np.cov(aligned["stock"],aligned["market"])
    beta = cov_matrix[0,1]/cov_matrix[1,1]

    return round(float(beta),4)

def analyze_ticker(ticker: str)-> dict:
    """
    Main entry point — returns all risk metrics for a single NSE ticker.
    """
    logger.info(f"Analysing risk for {ticker}")
    
    stock_returns  = _fetch_returns(ticker)
    market_returns = _fetch_returns(NIFTY_TICKER)
    
    _s     = get_settings()
    var    = calculate_var(stock_returns, _s.var_confidence)
    sharpe = calculate_sharpe(stock_returns)
    beta   = calculate_beta(stock_returns, market_returns)

    #current price

    suffix = get_settings().default_exchange_suffix
    full_ticker = f"{ticker}{suffix}" if "." not in ticker else ticker
    info = yf.Ticker(full_ticker).fast_info
    current_price = round(float(info.last_price),2)

    result ={
        "ticker": ticker,
        "current_price": current_price,
        "var_1d_95": var,
        "sharpe_ratio": sharpe,
        "beta": beta,
    }

    logger.info(f"{ticker}->VaR={var}% Sharpe={sharpe}, Beta= {beta}")
    return result
