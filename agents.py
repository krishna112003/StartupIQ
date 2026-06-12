"""
agents.py
----------
Defines the multi-agent pipeline for StartupIQ using LangGraph.

Architecture:
    Market Research Agent
        -> Competitor Analysis Agent
            -> Business Strategy Agent
                -> MVP Planner Agent
                    -> Final Aggregator

Each agent reads from a shared `StartupState`, calls Gemini 2.5 Flash
(optionally enriched with live web search results from Tavily), and
writes its findings back to the state as structured JSON.

The graph is intentionally linear (no branches) so it is easy to
explain in interviews.
"""

import os
import json
import re
from typing import TypedDict, List, Optional

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient


# ---------------------------------------------------------------------------
# Shared State Definition
# ---------------------------------------------------------------------------
class StartupState(TypedDict, total=False):
    """Shared memory passed between every agent in the graph."""

    # Input
    startup_idea: str

    # Agent 1: Market Research
    market_overview: str
    industry_trends: str
    target_audience: str
    market_score: int

    # Agent 2: Competitor Analysis
    competitors: str
    competition_level: str
    market_gaps: str
    competitive_advantage: str
    competition_score: int

    # Agent 3: Business Strategy
    swot_analysis: str
    revenue_strategy: str
    pricing_model: str
    monetization_opportunities: str

    # Agent 4: MVP Planner
    mvp_features: str
    roadmap_90_days: str
    tech_stack: str

    # Final Aggregator
    startup_score: int
    investor_verdict: str
    confidence_score: int
    biggest_opportunity: str
    biggest_risk: str
    next_step: str


# ---------------------------------------------------------------------------
# LLM + Search Setup
# ---------------------------------------------------------------------------
def get_llm() -> ChatGoogleGenerativeAI:
    """Create a Gemini 2.5 Flash LLM client using the GOOGLE_API_KEY env var."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0.4,
    )


def get_tavily_client() -> Optional[TavilyClient]:
    """Create a Tavily search client if an API key is configured."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return None
    return TavilyClient(api_key=api_key)


def web_search(query: str, max_results: int = 4) -> str:
    """
    Run a Tavily web search and return a compact text summary of results.

    If Tavily is not configured or the search fails, returns an empty
    string so the agent can gracefully fall back to the LLM's own
    knowledge.
    """
    client = get_tavily_client()
    if client is None:
        return ""

    try:
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        snippets = []
        for r in results:
            title = r.get("title", "")
            content = r.get("content", "")
            snippets.append(f"- {title}: {content}")
        return "\n".join(snippets)
    except Exception as exc:  # noqa: BLE001 - keep app running even if search fails
        return f"(Search unavailable: {exc})"


# ---------------------------------------------------------------------------
# Helper: robust JSON extraction from LLM responses
# ---------------------------------------------------------------------------
def extract_json(text: str) -> dict:
    """
    Extract a JSON object from an LLM response.

    Gemini sometimes wraps JSON in markdown code fences or adds
    extra commentary. This function strips that out and parses the
    first valid JSON object it finds.
    """
    # Remove markdown code fences if present
    cleaned = re.sub(r"```json|```", "", text).strip()

    # Try direct parse first
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fallback: find the first { ... } block
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    # Last resort: return an empty dict so the app doesn't crash
    return {}


def safe_int(value, default: int = 5) -> int:
    """Safely convert a value to an int, clamped between 0 and 100."""
    try:
        num = int(float(value))
        return max(0, min(100, num))
    except (TypeError, ValueError):
        return default


# ---------------------------------------------------------------------------
# Agent 1: Market Research Agent
# ---------------------------------------------------------------------------
def market_research_agent(state: StartupState) -> StartupState:
    """
    Researches the market opportunity for the startup idea.

    Writes to state:
        market_overview, industry_trends, target_audience, market_score
    """
    idea = state["startup_idea"]
    llm = get_llm()

    search_results = web_search(f"market size and trends for {idea} startup 2025")

    prompt = f"""
You are a Market Research Analyst evaluating a startup idea.

Startup Idea: "{idea}"

Live web research notes (may be empty):
{search_results}

Based on the idea and the research notes, respond with ONLY a JSON object
(no markdown, no commentary) with these exact keys:

{{
  "market_overview": "2-3 sentence overview of the market opportunity",
  "industry_trends": "2-3 sentence summary of relevant industry trends",
  "target_audience": "1-2 sentence description of the ideal target audience",
  "market_score": <integer 0-10 representing how attractive this market is>
}}
"""
    response = llm.invoke(prompt)
    data = extract_json(response.content)

    state["market_overview"] = data.get("market_overview", "No market overview generated.")
    state["industry_trends"] = data.get("industry_trends", "No industry trends generated.")
    state["target_audience"] = data.get("target_audience", "No target audience generated.")
    state["market_score"] = safe_int(data.get("market_score", 5), default=5)

    return state


# ---------------------------------------------------------------------------
# Agent 2: Competitor Analysis Agent
# ---------------------------------------------------------------------------
def competitor_analysis_agent(state: StartupState) -> StartupState:
    """
    Analyzes the competitive landscape for the startup idea.

    Reads from state:
        startup_idea, market_overview

    Writes to state:
        competitors, competition_level, market_gaps,
        competitive_advantage, competition_score
    """
    idea = state["startup_idea"]
    market_overview = state.get("market_overview", "")
    llm = get_llm()

    search_results = web_search(f"top competitors and alternatives to {idea}")

    prompt = f"""
You are a Competitor Analysis Specialist.

Startup Idea: "{idea}"

Market Overview (from a previous analysis): {market_overview}

Live web research notes (may be empty):
{search_results}

Based on this, respond with ONLY a JSON object (no markdown, no commentary)
with these exact keys:

{{
  "competitors": "List 2-4 real or plausible competitors with a 1-line description each",
  "competition_level": "Low, Medium, or High",
  "market_gaps": "2-3 sentence summary of gaps or underserved needs in the market",
  "competitive_advantage": "2-3 sentence suggestion for how this startup could differentiate",
  "competition_score": <integer 0-10, where 10 means LOW competition (favorable) and 0 means saturated market>
}}
"""
    response = llm.invoke(prompt)
    data = extract_json(response.content)

    state["competitors"] = data.get("competitors", "No competitor data generated.")
    state["competition_level"] = data.get("competition_level", "Medium")
    state["market_gaps"] = data.get("market_gaps", "No market gap analysis generated.")
    state["competitive_advantage"] = data.get(
        "competitive_advantage", "No competitive advantage generated."
    )
    state["competition_score"] = safe_int(data.get("competition_score", 5), default=5)

    return state


# ---------------------------------------------------------------------------
# Agent 3: Business Strategy Agent
# ---------------------------------------------------------------------------
def business_strategy_agent(state: StartupState) -> StartupState:
    """
    Develops a business strategy: SWOT, revenue model, pricing.

    Reads from state:
        startup_idea, market_overview, competitors, competitive_advantage

    Writes to state:
        swot_analysis, revenue_strategy, pricing_model, monetization_opportunities
    """
    idea = state["startup_idea"]
    market_overview = state.get("market_overview", "")
    competitors = state.get("competitors", "")
    competitive_advantage = state.get("competitive_advantage", "")
    llm = get_llm()

    prompt = f"""
You are a Business Strategy Consultant.

Startup Idea: "{idea}"

Context from previous agents:
- Market Overview: {market_overview}
- Competitors: {competitors}
- Competitive Advantage: {competitive_advantage}

Based on this, respond with ONLY a JSON object (no markdown, no commentary)
with these exact keys:

{{
  "swot_analysis": "A SWOT analysis formatted as a short paragraph with Strengths, Weaknesses, Opportunities, and Threats clearly labeled",
  "revenue_strategy": "2-3 sentence description of how this startup can generate revenue",
  "pricing_model": "1-2 sentence recommended pricing model (e.g. freemium, subscription, one-time)",
  "monetization_opportunities": "2-3 sentence list of additional monetization opportunities"
}}
"""
    response = llm.invoke(prompt)
    data = extract_json(response.content)

    state["swot_analysis"] = data.get("swot_analysis", "No SWOT analysis generated.")
    state["revenue_strategy"] = data.get("revenue_strategy", "No revenue strategy generated.")
    state["pricing_model"] = data.get("pricing_model", "No pricing model generated.")
    state["monetization_opportunities"] = data.get(
        "monetization_opportunities", "No monetization opportunities generated."
    )

    return state


# ---------------------------------------------------------------------------
# Agent 4: MVP Planner Agent
# ---------------------------------------------------------------------------
def mvp_planner_agent(state: StartupState) -> StartupState:
    """
    Plans the MVP: core features, tech stack, and a 90-day roadmap.

    Reads from state:
        startup_idea, market_overview, competitive_advantage, revenue_strategy

    Writes to state:
        mvp_features, roadmap_90_days, tech_stack
    """
    idea = state["startup_idea"]
    competitive_advantage = state.get("competitive_advantage", "")
    revenue_strategy = state.get("revenue_strategy", "")
    llm = get_llm()

    prompt = f"""
You are a Technical Product Manager planning an MVP.

Startup Idea: "{idea}"

Context from previous agents:
- Competitive Advantage: {competitive_advantage}
- Revenue Strategy: {revenue_strategy}

Based on this, respond with ONLY a JSON object (no markdown, no commentary)
with these exact keys:

{{
  "mvp_features": "A list of 4-6 core MVP features, each with a short description",
  "roadmap_90_days": "A 90-day roadmap broken into Days 1-30, 31-60, 61-90 with key milestones for each phase",
  "tech_stack": "A recommended, beginner-friendly tech stack for building this MVP (frontend, backend, database, hosting)"
}}
"""
    response = llm.invoke(prompt)
    data = extract_json(response.content)

    state["mvp_features"] = data.get("mvp_features", "No MVP features generated.")
    state["roadmap_90_days"] = data.get("roadmap_90_days", "No roadmap generated.")
    state["tech_stack"] = data.get("tech_stack", "No tech stack recommendation generated.")

    return state


# ---------------------------------------------------------------------------
# Final Aggregator
# ---------------------------------------------------------------------------
def final_aggregator(state: StartupState) -> StartupState:
    """
    Synthesizes all agent outputs into a final score and investor verdict.

    Reads from state: everything produced by the previous 4 agents.

    Writes to state:
        startup_score, investor_verdict, confidence_score,
        biggest_opportunity, biggest_risk, next_step
    """
    idea = state["startup_idea"]
    llm = get_llm()

    prompt = f"""
You are a Venture Capital Investment Committee summarizing a full startup
due-diligence report into a final verdict.

Startup Idea: "{idea}"

Full Analysis So Far:
- Market Overview: {state.get('market_overview', '')}
- Industry Trends: {state.get('industry_trends', '')}
- Target Audience: {state.get('target_audience', '')}
- Market Score (0-10): {state.get('market_score', 0)}
- Competitors: {state.get('competitors', '')}
- Competition Level: {state.get('competition_level', '')}
- Market Gaps: {state.get('market_gaps', '')}
- Competitive Advantage: {state.get('competitive_advantage', '')}
- Competition Score (0-10, higher = less competition): {state.get('competition_score', 0)}
- SWOT: {state.get('swot_analysis', '')}
- Revenue Strategy: {state.get('revenue_strategy', '')}
- Pricing Model: {state.get('pricing_model', '')}
- MVP Features: {state.get('mvp_features', '')}
- 90-Day Roadmap: {state.get('roadmap_90_days', '')}

Based on ALL of the above, respond with ONLY a JSON object (no markdown,
no commentary) with these exact keys:

{{
  "startup_score": <integer 0-100, overall viability score>,
  "investor_verdict": "Invest" or "Consider Carefully" or "Do Not Invest",
  "confidence_score": <integer 0-100, how confident you are in this verdict>,
  "biggest_opportunity": "1-2 sentence description of the biggest opportunity",
  "biggest_risk": "1-2 sentence description of the biggest risk",
  "next_step": "1-2 sentence recommended next action for the founder"
}}
"""
    response = llm.invoke(prompt)
    data = extract_json(response.content)

    state["startup_score"] = safe_int(data.get("startup_score", 50), default=50)
    state["investor_verdict"] = data.get("investor_verdict", "Consider Carefully")
    state["confidence_score"] = safe_int(data.get("confidence_score", 50), default=50)
    state["biggest_opportunity"] = data.get(
        "biggest_opportunity", "No opportunity analysis generated."
    )
    state["biggest_risk"] = data.get("biggest_risk", "No risk analysis generated.")
    state["next_step"] = data.get("next_step", "No next step generated.")

    return state


# ---------------------------------------------------------------------------
# Build the LangGraph
# ---------------------------------------------------------------------------
def build_graph():
    """
    Builds and compiles the linear LangGraph pipeline:

        market_research -> competitor_analysis -> business_strategy
        -> mvp_planner -> final_aggregator -> END

    Returns:
        A compiled LangGraph app ready to be invoked with an initial state.
    """
    graph = StateGraph(StartupState)

    # Register each agent as a node
    graph.add_node("market_research", market_research_agent)
    graph.add_node("competitor_analysis", competitor_analysis_agent)
    graph.add_node("business_strategy", business_strategy_agent)
    graph.add_node("mvp_planner", mvp_planner_agent)
    graph.add_node("final_aggregator", final_aggregator)

    # Define the linear flow
    graph.set_entry_point("market_research")
    graph.add_edge("market_research", "competitor_analysis")
    graph.add_edge("competitor_analysis", "business_strategy")
    graph.add_edge("business_strategy", "mvp_planner")
    graph.add_edge("mvp_planner", "final_aggregator")
    graph.add_edge("final_aggregator", END)

    return graph.compile()


def run_validation(startup_idea: str) -> StartupState:
    """
    Convenience function: builds the graph, runs it on a startup idea,
    and returns the final populated state.

    Args:
        startup_idea: The user's startup idea as free text.

    Returns:
        A fully populated StartupState dictionary.
    """
    app = build_graph()
    initial_state: StartupState = {"startup_idea": startup_idea}
    final_state = app.invoke(initial_state)
    return final_state