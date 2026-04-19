import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os
import time

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Portfolio Risk Advisor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.hero { background: #0f1422; border: 1px solid #1e2540; border-radius: 16px; padding: 2rem; margin-bottom: 1.5rem; }
.hero-badge { display: inline-block; background: rgba(56,130,246,0.12); color: #3882f6; border: 1px solid rgba(56,130,246,0.25); border-radius: 20px; padding: 3px 12px; font-size: 0.75rem; font-weight: 500; margin-bottom: 0.75rem; }
.hero-title { font-size: 1.8rem; font-weight: 600; color: #e8edf5; margin: 0; letter-spacing: -0.03em; }
.hero-subtitle { font-size: 0.85rem; color: #4a5568; margin-top: 0.4rem; }
.metric-card { background: #0f1422; border: 1px solid #1e2540; border-radius: 12px; padding: 1.25rem 1.5rem; height: 100%; }
.metric-label { font-size: 0.7rem; color: #4a5568; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.5rem; }
.metric-value { font-size: 1.5rem; font-weight: 600; color: #e8edf5; font-family: 'DM Mono', monospace; letter-spacing: -0.02em; }
.metric-sub { font-size: 0.72rem; color: #4a5568; margin-top: 0.25rem; }
.alert-box { background: rgba(239,68,68,0.06); border: 1px solid rgba(239,68,68,0.2); border-left: 3px solid #ef4444; border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.5rem; color: #fca5a5; font-size: 0.875rem; }
.rec-box { background: rgba(56,130,246,0.06); border: 1px solid rgba(56,130,246,0.2); border-left: 3px solid #3882f6; border-radius: 8px; padding: 1rem 1.25rem; color: #93c5fd; font-size: 0.875rem; line-height: 1.6; }
.section-header { font-size: 0.7rem; font-weight: 600; color: #4a5568; text-transform: uppercase; letter-spacing: 0.08em; margin: 1.5rem 0 0.75rem; border-bottom: 1px solid #1e2540; padding-bottom: 0.5rem; }
.news-card { background: #0f1422; border: 1px solid #1e2540; border-radius: 10px; padding: 1rem; margin-bottom: 0.75rem; }
.news-ticker { font-size: 0.7rem; font-weight: 600; color: #3882f6; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.4rem; }
.news-text { font-size: 0.82rem; color: #8892a4; line-height: 1.6; }
.disclaimer { font-size: 0.68rem; color: #2d3748; text-align: center; padding: 1rem; border-top: 1px solid #1e2540; margin-top: 2rem; }
#MainMenu {visibility: hidden;} footer {visibility: hidden;} .stDeployButton {display: none;}
</style>
""", unsafe_allow_html=True)


def safe_float(val, fallback=0.0):
    try: return float(val) if val is not None else fallback
    except: return fallback

def format_inr(val):
    val = safe_float(val)
    if val >= 1e7: return f"₹{val/1e7:.2f}Cr"
    elif val >= 1e5: return f"₹{val/1e5:.2f}L"
    return f"₹{val:,.0f}"


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:.75rem 0 1.25rem">
        <div style="font-size:1rem;font-weight:600;color:#e8edf5">Portfolio Input</div>
        <div style="font-size:0.75rem;color:#4a5568;margin-top:.2rem">NSE tickers · no .NS suffix</div>
    </div>""", unsafe_allow_html=True)

    portfolio_name = st.text_input("Portfolio name", "My NSE Portfolio")
    num_holdings   = st.slider("Number of holdings", 1, 15, 3)

    popular = ["RELIANCE","TCS","INFY","HDFCBANK","ICICIBANK",
               "WIPRO","ADANIENT","BAJFINANCE","SBIN","MARUTI"]
    holdings = []

    st.markdown('<div class="section-header">Holdings</div>', unsafe_allow_html=True)

    for i in range(int(num_holdings)):
        with st.expander(f"Holding {i+1}", expanded=(i < 3)):
            ticker = st.text_input("Ticker", key=f"t{i}",
                                   value=popular[i] if i < len(popular) else "",
                                   placeholder="e.g. RELIANCE").upper().strip()
            c1, c2 = st.columns(2)
            qty   = c1.number_input("Qty",     key=f"q{i}", min_value=1,    value=10)
            price = c2.number_input("Avg ₹",   key=f"p{i}", min_value=0.01, value=1000.0, format="%.2f")
            if ticker:
                holdings.append({"ticker": ticker, "quantity": qty, "avg_buy_price": price})

    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("Run Analysis", type="primary", use_container_width=True)

    st.markdown("""
    <div style="margin-top:1.5rem;padding:.75rem;background:#0a0e1a;border-radius:8px;border:1px solid #1e2540">
        <div style="font-size:0.68rem;color:#2d3748;line-height:1.7">
            LangChain · Gemini 1.5 Flash · Pinecone<br>
            Educational use only · Not financial advice
        </div>
    </div>""", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">AI-Powered · NSE/BSE · Multi-Agent</div>
    <div class="hero-title">Agentic Portfolio Risk Advisor</div>
    <div class="hero-subtitle">Real-time prices · RAG news analysis · VaR · Sharpe · Beta · Gemini synthesis</div>
</div>""", unsafe_allow_html=True)

if not analyze_btn:
    c1, c2, c3 = st.columns(3)
    c1.markdown("""<div class="metric-card"><div class="metric-label">Risk Metrics</div>
    <div class="metric-value" style="font-size:1.1rem;color:#3882f6">VaR · Sharpe · Beta</div>
    <div class="metric-sub">Historical 95% CI · vs NIFTY 50</div></div>""", unsafe_allow_html=True)
    c2.markdown("""<div class="metric-card"><div class="metric-label">News Intelligence</div>
    <div class="metric-value" style="font-size:1.1rem;color:#10b981">RAG Grounded</div>
    <div class="metric-sub">Pinecone vector search · Source-cited</div></div>""", unsafe_allow_html=True)
    c3.markdown("""<div class="metric-card"><div class="metric-label">AI Synthesis</div>
    <div class="metric-value" style="font-size:1.1rem;color:#f59e0b">Gemini Flash</div>
    <div class="metric-sub">Temp=0 · Structured output · Traceable</div></div>""", unsafe_allow_html=True)
    st.markdown("""<div style="text-align:center;margin-top:3rem;color:#2d3748;font-size:.85rem">
    Add holdings in the sidebar and click <strong style="color:#3882f6">Run Analysis</strong></div>""",
    unsafe_allow_html=True)

elif not holdings:
    st.warning("Add at least one holding in the sidebar.")

else:
    prog = st.progress(0, text="Fetching live prices...")
    try:
        prog.progress(30, text="Calculating VaR · Sharpe · Beta...")

        with st.spinner("Waking up API server... (first request may take 30-60s)"):
            for attempt in range(5):
                try:
                    wake = requests.get(f"{API_URL}/health", timeout=30)
                    if wake.status_code == 200:
                        break
                except:
                    time.sleep(5)

            resp = requests.post(
                f"{API_URL}/analyze",
                json={"holdings": holdings, "portfolio_name": portfolio_name},
                headers={"Content-Type": "application/json"},
                timeout=180,
            )
        prog.progress(80, text="Synthesising AI report...")
        resp.raise_for_status()
        data = resp.json()
        prog.progress(100, text="Complete")
        prog.empty()
    except requests.exceptions.ConnectionError:
        st.error("Cannot reach API. Make sure FastAPI is running on port 8000.")
        st.stop()
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.stop()

    # Metrics row
    tv = safe_float(data.get("total_value"))
    vr = safe_float(data.get("portfolio_var_1d_95"))
    sh = safe_float(data.get("portfolio_sharpe"))
    rl = str(data.get("overall_risk_level","medium")).lower()
    ts = data.get("data_timestamp", datetime.now().strftime("%Y-%m-%d %H:%M"))

    rc = {"low":"#10b981","medium":"#f59e0b","high":"#ef4444"}.get(rl,"#f59e0b")
    sc = "#10b981" if sh > 1 else "#f59e0b" if sh > 0 else "#ef4444"

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(f"""<div class="metric-card"><div class="metric-label">Total Value</div>
    <div class="metric-value">{format_inr(tv)}</div>
    <div class="metric-sub">{len(holdings)} holdings</div></div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card"><div class="metric-label">1-Day VaR 95%</div>
    <div class="metric-value" style="color:#ef4444">{vr:.2f}%</div>
    <div class="metric-sub">Max expected daily loss</div></div>""", unsafe_allow_html=True)
    c3.markdown(f"""<div class="metric-card"><div class="metric-label">Sharpe Ratio</div>
    <div class="metric-value" style="color:{sc}">{sh:.2f}</div>
    <div class="metric-sub">Risk-adjusted return</div></div>""", unsafe_allow_html=True)
    c4.markdown(f"""<div class="metric-card"><div class="metric-label">Overall Risk</div>
    <div class="metric-value" style="color:{rc};font-size:1.3rem">{rl.upper()}</div>
    <div class="metric-sub">as of {ts}</div></div>""", unsafe_allow_html=True)

    # Alerts
    alerts = data.get("alerts",[])
    if alerts:
        st.markdown('<div class="section-header">Risk Alerts</div>', unsafe_allow_html=True)
        for a in alerts:
            st.markdown(f'<div class="alert-box">⚠ {a}</div>', unsafe_allow_html=True)

    # Recommendation
    if data.get("recommendation"):
        st.markdown('<div class="section-header">AI Recommendation</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="rec-box">💡 {data["recommendation"]}</div>', unsafe_allow_html=True)

    # Charts
    hd = data.get("holdings",[])
    if hd:
        df = pd.DataFrame(hd)
        st.markdown('<div class="section-header">Holdings Breakdown</div>', unsafe_allow_html=True)
        cl, cr = st.columns(2)

        with cl:
            colors = ["#3882f6","#10b981","#f59e0b","#ef4444","#8b5cf6",
                      "#06b6d4","#ec4899","#84cc16","#f97316","#14b8a6"]
            fig = go.Figure(go.Pie(
                labels=df["ticker"], values=df["weight_pct"], hole=0.55,
                marker=dict(colors=colors[:len(df)], line=dict(color="#0a0e1a",width=2)),
                textinfo="label+percent",
                textfont=dict(family="DM Sans", size=11, color="#e8edf5"),
            ))
            fig.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", margin=dict(t=10,b=10,l=10,r=10),
                annotations=[dict(text=f"<b>{format_inr(tv)}</b>", x=0.5, y=0.5,
                    font_size=12, font_color="#e8edf5", showarrow=False)])
            st.markdown("**Allocation**")
            st.plotly_chart(fig, use_container_width=True)

        with cr:
            if "beta" in df.columns and "var_1d_95" in df.columns:
                rmap = {"low":"#10b981","medium":"#f59e0b","high":"#ef4444"}
                fig2 = go.Figure()
                for _, row in df.iterrows():
                    fig2.add_trace(go.Scatter(
                        x=[safe_float(row.get("beta"))],
                        y=[safe_float(row.get("var_1d_95"))],
                        mode="markers+text",
                        marker=dict(size=18, color=rmap.get(str(row.get("risk_level","medium")).lower(),"#f59e0b"),
                                    line=dict(color="#0a0e1a",width=2)),
                        text=[row["ticker"]], textposition="top center",
                        textfont=dict(size=10, color="#e8edf5"), showlegend=False,
                    ))
                fig2.add_vline(x=1.0, line_dash="dot", line_color="#2d3748", line_width=1)
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#0f1422",
                    xaxis=dict(title="Beta vs NIFTY 50", gridcolor="#1e2540", color="#4a5568", zerolinecolor="#1e2540"),
                    yaxis=dict(title="1-Day VaR 95% (%)", gridcolor="#1e2540", color="#4a5568", zerolinecolor="#1e2540"),
                    margin=dict(t=10,b=40,l=50,r=10))
                st.markdown("**Risk Map — VaR vs Beta**")
                st.plotly_chart(fig2, use_container_width=True)

        # Table
        disp = df[["ticker","weight_pct","current_price","var_1d_95","sharpe_ratio","beta","risk_level"]].copy()
        disp.columns = ["Ticker","Weight %","Price ₹","VaR 95%","Sharpe","Beta","Risk"]
        st.dataframe(disp.round(3), use_container_width=True, hide_index=True,
            column_config={
                "Weight %": st.column_config.NumberColumn(format="%.1f%%"),
                "Price ₹":  st.column_config.NumberColumn(format="₹%.2f"),
                "VaR 95%":  st.column_config.NumberColumn(format="%.2f%%"),
                "Sharpe":   st.column_config.NumberColumn(format="%.2f"),
                "Beta":     st.column_config.NumberColumn(format="%.2f"),
            })

        # News
        st.markdown('<div class="section-header">News Intelligence (RAG-Grounded)</div>', unsafe_allow_html=True)
        cols = st.columns(min(len(hd), 3))
        for i, h in enumerate(hd):
            with cols[i % len(cols)]:
                st.markdown(f"""<div class="news-card">
                <div class="news-ticker">{h.get('ticker','')}</div>
                <div class="news-text">{h.get('news_summary','No news available.')}</div>
                </div>""", unsafe_allow_html=True)

    # with st.expander("Raw API response", expanded=False):
    #     st.json(data)

    st.markdown("""<div class="disclaimer">
    For educational purposes only · Not financial advice · Consult a SEBI-registered advisor before investing
    </div>""", unsafe_allow_html=True)
