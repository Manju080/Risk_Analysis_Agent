import logging
import json
from datetime import datetime
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from api.schemas import RiskReport, HoldingRisk, RiskLevel
from agents.price_agent import get_portfolio_value
from agents.risk_agent import analyze_ticker
from agents.news_agent import summarise_news
from agents.memory_agent import add_interaction, get_recent_context
from core.llm_factory import get_llm
from langchain_core.output_parsers import StrOutputParser
import json, re

logger = logging.getLogger(__name__)

SYNTHESIS_PROMPT = PromptTemplate.from_template("""
You are a senior financial risk analyst for NSE/BSE Indian equities.
Below are verified quantitative outputs from specialist tools.

Your job:
1. Classify each holding risk level: low / medium / high
2. Write 1-2 specific alerts for the riskiest holdings (mention ticker + reason)
3. Write a 3-sentence portfolio recommendation

STRICT RULES:
- Use ONLY numbers from the data below. Do NOT invent figures.
- No generic advice. Every sentence must reference specific tickers or numbers.
- Do NOT mention companies not in the portfolio data.

=== PORTFOLIO DATA ===
{portfolio_data}

=== PRIOR CONTEXT ===
{prior_context}

Return ONLY valid JSON — no markdown, no explanation:
{{
  "risk_classifications": {{"TICKER": "low|medium|high"}},
  "alerts": ["specific alert with ticker name and metric"],
  "recommendation": "3 sentences referencing specific tickers and numbers."
}}
""")


def _classify_risk(var: float, sharpe: float, beta: float) -> RiskLevel:
    score = 0
    if var > 3.0:      score += 2
    elif var > 1.5:    score += 1
    if sharpe < 0:     score += 2
    elif sharpe < 0.5: score += 1
    if beta > 1.5:     score += 2
    elif beta > 1.0:   score += 1
    if score >= 4: return RiskLevel.HIGH
    if score >= 2: return RiskLevel.MEDIUM
    return RiskLevel.LOW


def run_analysis(request, session_id: str = "default") -> RiskReport:
    tickers      = [h.ticker for h in request.holdings]
    holdings_raw = [h.model_dump() for h in request.holdings]

    # Step 1: Prices
    logger.info(f"Step 1 — fetching prices for {tickers}")
    price_data = get_portfolio_value(holdings_raw)

    # Step 2: Risk metrics
    logger.info("Step 2 — calculating risk metrics")
    risk_data = {}
    for ticker in tickers:
        try:
            risk_data[ticker] = analyze_ticker(ticker)
        except Exception as e:
            logger.warning(f"Risk calc failed for {ticker}: {e}")
            risk_data[ticker] = {
                "var_1d_95": 0, "sharpe_ratio": 0,
                "beta": 1.0, "current_price": 0
            }

    # Step 3: News RAG
    logger.info("Step 3 — fetching news summaries")
    news_data = {}
    for ticker in tickers:
        try:
            news_data[ticker] = summarise_news(ticker)
        except Exception as e:
            logger.warning(f"News failed for {ticker}: {e}")
            news_data[ticker] = {"summary": "News unavailable.", "sources": []}

    # Step 4: Build context
    portfolio_data_str = json.dumps({
        "total_value": price_data["total_value"],
        "holdings": [
            {
                "ticker":        h["ticker"],
                "weight_pct":    h["weight_pct"],
                "current_price": h["current_price"],
                "pnl_pct":       h["pnl_pct"],
                **risk_data.get(h["ticker"], {}),
                "news_summary":  news_data.get(h["ticker"], {}).get("summary", ""),
            }
            for h in price_data["holdings"]
        ]
    }, indent=2)

    prior_context = get_recent_context(session_id)

    # Step 5: LLM synthesis
    logger.info("Step 5 — LLM synthesis")
    llm   = get_llm(temperature=0)
    str_chain = SYNTHESIS_PROMPT | llm | StrOutputParser()
    try:
        raw = str_chain.invoke({
            "portfolio_data": portfolio_data_str,
            "prior_context":  prior_context,
        })
        # Strip markdown code blocks if Gemini wraps response
        raw = re.sub(r"```json\s*|\s*```", "", raw).strip()
        llm_out = json.loads(raw)
    except Exception as e:
        logger.error(f"LLM synthesis failed: {e}")
        llm_out = {
            "risk_classifications": {},
            "alerts": ["LLM synthesis failed — showing rule-based risk only"],
            "recommendation": "Analysis partially completed. Risk metrics above are accurate. LLM synthesis unavailable."
        }

    # Step 6: Assemble report
    holding_risks = []
    total_var, total_sharpe = 0.0, 0.0

    for h in price_data["holdings"]:
        t   = h["ticker"]
        rd  = risk_data.get(t, {})
        var = rd.get("var_1d_95", 0)
        sh  = rd.get("sharpe_ratio", 0)
        bt  = rd.get("beta", 1.0)
        w   = h["weight_pct"] / 100

        total_var    += var * w
        total_sharpe += sh  * w

        llm_cls  = llm_out.get("risk_classifications", {}).get(t)
        risk_lvl = (RiskLevel(llm_cls)
                    if llm_cls in ["low","medium","high"]
                    else _classify_risk(var, sh, bt))

        holding_risks.append(HoldingRisk(
            ticker        = t,
            current_price = h["current_price"],
            weight_pct    = h["weight_pct"],
            var_1d_95     = var,
            sharpe_ratio  = sh,
            beta          = bt,
            risk_level    = risk_lvl,
            news_summary  = news_data.get(t, {}).get("summary", ""),
        ))

    report = RiskReport(
        portfolio_name      = request.portfolio_name,
        total_value         = price_data["total_value"],
        portfolio_var_1d_95 = round(total_var, 4),
        portfolio_sharpe    = round(total_sharpe, 4),
        overall_risk_level  = _classify_risk(total_var, total_sharpe, 1.0),
        holdings            = holding_risks,
        alerts              = llm_out.get("alerts", []),
        recommendation      = llm_out.get("recommendation", ""),
        data_timestamp      = datetime.now().strftime("%Y-%m-%d %H:%M IST"),
    )

    add_interaction(
        session_id,
        user_input  = f"Analyse portfolio: {tickers}",
        ai_response = report.recommendation,
    )

    logger.info(f"Analysis complete — risk: {report.overall_risk_level}")
    return report
