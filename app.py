"""
app.py
-------
StartupIQ - Multi-Agent Startup Validator

A premium, glassmorphic Streamlit dashboard that uses a 4-agent
LangGraph pipeline (Market Research, Competitor Analysis, Business
Strategy, MVP Planner) plus a Final Aggregator to evaluate a startup
idea and present a full investor-style report.

Run with:
    streamlit run app.py

Required environment variables (set as Streamlit secrets or env vars):
    GOOGLE_API_KEY
    TAVILY_API_KEY
"""

import os
import time
import streamlit as st

from agents import run_validation, StartupState


# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="StartupIQ | Multi-Agent Startup Validator",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Load API keys (Streamlit secrets take priority over env vars)
# ---------------------------------------------------------------------------
def load_api_keys() -> None:
    """Load API keys from Streamlit secrets into environment variables."""
    for key in ("GOOGLE_API_KEY", "TAVILY_API_KEY"):
        if key in st.secrets:
            os.environ[key] = st.secrets[key]


load_api_keys()


# ---------------------------------------------------------------------------
# Custom CSS - Glassmorphism / Gradient / Neon Dashboard Theme
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
:root {
    --bg-deep: #0b0f1f;
    --bg-mid: #131a2e;
    --accent-cyan: #5eead4;
    --accent-violet: #a78bfa;
    --accent-pink: #f472b6;
    --text-light: #e6e9f5;
    --text-dim: #9aa3c2;
    --glass-bg: rgba(255, 255, 255, 0.05);
    --glass-border: rgba(255, 255, 255, 0.12);
}

/* App background */
.stApp {
    background: radial-gradient(circle at 15% 0%, #1b2440 0%, #0b0f1f 45%, #05070f 100%);
    color: var(--text-light);
    font-family: 'Inter', 'Segoe UI', sans-serif;
}

/* Hide default Streamlit chrome */
header[data-testid="stHeader"] {
    background: transparent;
}
footer {visibility: hidden;}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e1326 0%, #090c18 100%);
    border-right: 1px solid var(--glass-border);
}
section[data-testid="stSidebar"] * {
    color: var(--text-light) !important;
}

/* Hero section */
.hero-container {
    padding: 2.5rem 2rem;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(94, 234, 212, 0.12), rgba(167, 139, 250, 0.12));
    border: 1px solid var(--glass-border);
    margin-bottom: 1.5rem;
    text-align: center;
    backdrop-filter: blur(12px);
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-violet), var(--accent-pink));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 0.3rem;
}
.hero-subtitle {
    color: var(--text-dim);
    font-size: 1.05rem;
}

/* Glass card */
.glass-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 1rem;
}
.glass-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(94, 234, 212, 0.15);
}

/* Metric cards row */
.metric-card {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 10px 25px rgba(167, 139, 250, 0.18);
}
.metric-value {
    font-size: 2.2rem;
    font-weight: 800;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-violet));
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.metric-label {
    color: var(--text-dim);
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.3rem;
}

/* Verdict badge */
.verdict-badge {
    display: inline-block;
    padding: 0.5rem 1.4rem;
    border-radius: 999px;
    font-weight: 700;
    font-size: 1.1rem;
    margin-top: 0.5rem;
    letter-spacing: 0.03em;
}
.verdict-invest {
    background: linear-gradient(90deg, #34d399, #5eead4);
    color: #052e23;
}
.verdict-consider {
    background: linear-gradient(90deg, #fbbf24, #f59e0b);
    color: #2e1c00;
}
.verdict-no {
    background: linear-gradient(90deg, #f87171, #f472b6);
    color: #2e0707;
}

/* Progress bar container */
.progress-label {
    display: flex;
    justify-content: space-between;
    font-size: 0.9rem;
    color: var(--text-dim);
    margin-bottom: 0.3rem;
}
.progress-track {
    width: 100%;
    height: 12px;
    background: rgba(255,255,255,0.06);
    border-radius: 999px;
    overflow: hidden;
    border: 1px solid var(--glass-border);
}
.progress-fill {
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-violet));
    transition: width 1.2s ease-in-out;
}

/* Section heading */
.section-heading {
    font-size: 1.3rem;
    font-weight: 700;
    margin: 1.2rem 0 0.6rem 0;
    color: var(--text-light);
    border-left: 4px solid var(--accent-cyan);
    padding-left: 0.7rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, var(--accent-cyan), var(--accent-violet));
    color: #0b0f1f;
    font-weight: 700;
    border: none;
    border-radius: 12px;
    padding: 0.6rem 1.4rem;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 20px rgba(94, 234, 212, 0.3);
    color: #0b0f1f;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 10px 10px 0 0;
    padding: 0.6rem 1.2rem;
    color: var(--text-dim);
}
.stTabs [aria-selected="true"] {
    color: var(--accent-cyan) !important;
    border-bottom: 2px solid var(--accent-cyan);
}

/* Text input */
.stTextInput > div > div > input {
    background: var(--glass-bg);
    border: 1px solid var(--glass-border);
    border-radius: 12px;
    color: var(--text-light);
    padding: 0.7rem 1rem;
}

/* Expander */
.streamlit-expanderHeader {
    background: var(--glass-bg);
    border-radius: 10px;
    border: 1px solid var(--glass-border);
    color: var(--text-light) !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Helper UI Components
# ---------------------------------------------------------------------------
def render_progress_bar(label: str, value: int, max_value: int = 10) -> None:
    """Render a custom animated gradient progress bar."""
    percent = int((value / max_value) * 100)
    st.markdown(
        f"""
        <div class="progress-label">
            <span>{label}</span>
            <span>{value} / {max_value}</span>
        </div>
        <div class="progress-track">
            <div class="progress-fill" style="width: {percent}%;"></div>
        </div>
        <div style="height: 0.8rem;"></div>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str) -> None:
    """Render a glassmorphic metric card."""
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_verdict_badge(verdict: str) -> str:
    """Return the CSS class for a given investor verdict."""
    mapping = {
        "Invest": "verdict-invest",
        "Consider Carefully": "verdict-consider",
        "Do Not Invest": "verdict-no",
    }
    return mapping.get(verdict, "verdict-consider")


def render_glass_card(title: str, content: str) -> None:
    """Render a titled glassmorphic content card."""
    st.markdown(
        f"""
        <div class="glass-card">
            <h4 style="margin-top:0; color: var(--accent-cyan);">{title}</h4>
            <p style="color: var(--text-light); line-height:1.6;">{content}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🚀 StartupIQ")
    st.markdown("**Multi-Agent Startup Validator**")
    st.markdown("---")
    st.markdown(
        """
        ### How it works
        1. 🔎 **Market Research Agent**
        2. 🥊 **Competitor Analysis Agent**
        3. 💡 **Business Strategy Agent**
        4. 🛠️ **MVP Planner Agent**
        5. 🏆 **Final Aggregator**
        """
    )
    st.markdown("---")
    st.markdown(
        """
        ### Tech Stack
        - LangGraph (multi-agent orchestration)
        - Gemini 2.5 Flash (LLM)
        - Tavily (live web search)
        - Streamlit (UI)
        """
    )
    st.markdown("---")
    st.caption("Built for engineering placement portfolios 💼")


# ---------------------------------------------------------------------------
# Hero Section
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-title">🚀 StartupIQ</div>
        <div class="hero-subtitle">
            AI-powered multi-agent startup validation — market insight,
            competitor intel, business strategy, and an investor verdict
            in seconds.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Input Section
# ---------------------------------------------------------------------------
col_input, col_button = st.columns([4, 1])

with col_input:
    startup_idea = st.text_input(
        "Enter your startup idea",
        placeholder="e.g. AI Fitness App for College Students",
        label_visibility="collapsed",
    )

with col_button:
    analyze_clicked = st.button("Analyze 🚀", use_container_width=True)


# ---------------------------------------------------------------------------
# Run the Multi-Agent Pipeline
# ---------------------------------------------------------------------------
if analyze_clicked:
    if not startup_idea.strip():
        st.warning("Please enter a startup idea to analyze.")
    elif not os.environ.get("GOOGLE_API_KEY"):
        st.error("⚠️ GOOGLE_API_KEY is not set. Please configure it in Streamlit secrets.")
    else:
        with st.spinner("🤖 Agents are analyzing your startup idea..."):
            try:
                result: StartupState = run_validation(startup_idea.strip())
                st.session_state["result"] = result
                st.session_state["idea"] = startup_idea.strip()
            except Exception as exc:  # noqa: BLE001
                st.error(f"❌ Something went wrong while running the agents: {exc}")


# ---------------------------------------------------------------------------
# Results Display
# ---------------------------------------------------------------------------
if "result" in st.session_state:
    result = st.session_state["result"]
    idea = st.session_state.get("idea", "")

    st.markdown(f"### 📋 Validation Report for: *{idea}*")

    # --- Top-level Metric Cards ---
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card("Startup Score", f"{result.get('startup_score', 0)}/100")
    with m2:
        render_metric_card("Market Score", f"{result.get('market_score', 0)}/10")
    with m3:
        render_metric_card("Competition Score", f"{result.get('competition_score', 0)}/10")
    with m4:
        render_metric_card("Confidence", f"{result.get('confidence_score', 0)}%")

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # --- Investor Verdict Card ---
    verdict = result.get("investor_verdict", "Consider Carefully")
    badge_class = render_verdict_badge(verdict)
    st.markdown(
        f"""
        <div class="glass-card" style="text-align:center;">
            <h3 style="margin-top:0;">🏆 Investor Verdict</h3>
            <span class="verdict-badge {badge_class}">{verdict}</span>
            <p style="margin-top:1rem; color: var(--text-dim);">
                Confidence: {result.get('confidence_score', 0)}%
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --- Score Meters ---
    meter_col1, meter_col2 = st.columns(2)
    with meter_col1:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("**📊 Market Score**")
        render_progress_bar("Market Attractiveness", result.get("market_score", 0), 10)
        st.markdown("</div>", unsafe_allow_html=True)
    with meter_col2:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("**🥊 Competition Score**")
        render_progress_bar("Low Competition = Higher Score", result.get("competition_score", 0), 10)
        st.markdown("</div>", unsafe_allow_html=True)

    # --- Tabs for Detailed Report ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📈 Market Analysis",
            "🥊 Competitor Analysis",
            "💡 Business Strategy",
            "🛠️ MVP Roadmap",
            "🏆 Investor Verdict",
        ]
    )

    # Tab 1: Market Analysis
    with tab1:
        render_glass_card("Market Overview", result.get("market_overview", ""))
        render_glass_card("Industry Trends", result.get("industry_trends", ""))
        render_glass_card("Target Audience", result.get("target_audience", ""))

    # Tab 2: Competitor Analysis
    with tab2:
        render_glass_card("Competitors", result.get("competitors", ""))
        render_glass_card("Competition Level", result.get("competition_level", ""))
        render_glass_card("Market Gaps", result.get("market_gaps", ""))
        render_glass_card("Competitive Advantage", result.get("competitive_advantage", ""))

    # Tab 3: Business Strategy
    with tab3:
        with st.expander("📋 SWOT Analysis", expanded=True):
            st.write(result.get("swot_analysis", ""))
        render_glass_card("Revenue Strategy", result.get("revenue_strategy", ""))
        render_glass_card("Pricing Model", result.get("pricing_model", ""))
        render_glass_card("Monetization Opportunities", result.get("monetization_opportunities", ""))

    # Tab 4: MVP Roadmap
    with tab4:
        with st.expander("🛠️ MVP Features", expanded=True):
            st.write(result.get("mvp_features", ""))
        with st.expander("🗺️ 90-Day Roadmap", expanded=True):
            st.write(result.get("roadmap_90_days", ""))
        render_glass_card("Suggested Tech Stack", result.get("tech_stack", ""))

    # Tab 5: Investor Verdict
    with tab5:
        v1, v2 = st.columns(2)
        with v1:
            render_glass_card("🌟 Biggest Opportunity", result.get("biggest_opportunity", ""))
        with v2:
            render_glass_card("⚠️ Biggest Risk", result.get("biggest_risk", ""))
        render_glass_card("✅ Recommended Next Step", result.get("next_step", ""))

else:
    st.info("👆 Enter a startup idea above and click **Analyze 🚀** to generate your report.")