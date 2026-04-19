import yfinance as yf
import pandas as pd
from datetime import datetime
from core.settings import get_settings
import logging

logger = logging.getLogger(__name__)


def get_live_prices(tickers: list[str]) -> dict:
    """
    Returns {ticker: current_price} for a list of NSE tickers.    
    """

    settings = get_settings()
    suffix = settings.default_exchange_suffix
    full_tickers = [f"{t}{suffix}" if "." not in t else t for t in tickers]

    data = yf.download(full_tickers, period="1d",
                       auto_adjust=True, progress=False)

    prices = {}

    for ticker, full in zip(tickers, full_tickers):
        try:
            price = float(data["Close"][full].iloc[-1])
            prices[ticker] = round(price, 2)
        except Exception as e:
            logger.warning(f"Could not fetch price for {ticker}:{e}")
            prices[ticker] = None
    logger.info(f"Fetched live prices for {len(prices)} tickers at {
                datetime.now().strftime('%H:%M IST')}")
    return prices


def get_portfolio_value(holdings: list[dict]) -> dict:
    """
    holdings: [{"ticker": "RELIANCE", "quantity": 10, "avg_buy_price": 2800}, ...]
    Returns enriched holdings with current value and P&L.
    """

    tickers = [h["ticker"] for h in holdings]
    prices = get_live_prices(tickers)

    enriched = []
    total_value = 0.0

    for h in holdings:
        tickers = h["ticker"]
        qty = h["quantity"]
        avg_buy = h["avg_buy_price"]
        curr_px = prices.get(tickers) or avg_buy

        curr_val = round(curr_px * qty, 2)
        cost_val = round(avg_buy * qty, 2)
        pnl = round(curr_val - cost_val, 2)
        pnl_pct = round((pnl / cost_val) * 100, 2) if cost_val else 0

        total_value += curr_val
        enriched.append({
            **h,
            "current_price": curr_px,
            "current_value": curr_val,
            "pnl": pnl,
            "pnl_pct": pnl_pct,
        })
    for e in enriched:
        e["weight_pct"] = round(
            (e["current_value"] / total_value) * 100, 2) if total_value else 0

    return {"holdings": enriched, "total_value": round(total_value, 2)}
