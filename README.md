# 🚀 StartupIQ - Multi-Agent Startup Validator

StartupIQ is a multi-agent AI system that takes a startup idea and produces
a complete, investor-style validation report — market opportunity,
competitor landscape, business strategy, MVP roadmap, and a final
"Invest / Consider Carefully / Do Not Invest" verdict.

It is built to be **simple enough to explain confidently in an interview**
while still demonstrating real multi-agent orchestration with LangGraph.

---

## 📌 Project Overview

A user types a startup idea (e.g. *"AI Fitness App for College Students"*),
and StartupIQ runs it through **4 specialized AI agents** plus a **Final
Aggregator**, each powered by **Google Gemini 2.5 Flash**, with optional
live web research via **Tavily Search**. The result is displayed in a
premium, glassmorphic Streamlit dashboard.

---

## 🏗️ Architecture Diagram

```
                ┌─────────────────────────┐
                │   User enters idea       │
                │  "AI Fitness App ..."    │
                └───────────┬──────────────┘
                            │
                            ▼
                ┌─────────────────────────┐
                │ 1. Market Research Agent │
                │  - Market overview       │
                │  - Industry trends       │
                │  - Target audience       │
                │  - Market score (0-10)   │
                └───────────┬──────────────┘
                            ▼
                ┌─────────────────────────┐
                │ 2. Competitor Analysis   │
                │  - Competitors           │
                │  - Competition level     │
                │  - Market gaps           │
                │  - Competitive advantage │
                └───────────┬──────────────┘
                            ▼
                ┌─────────────────────────┐
                │ 3. Business Strategy     │
                │  - SWOT analysis         │
                │  - Revenue strategy      │
                │  - Pricing model         │
                │  - Monetization ideas    │
                └───────────┬──────────────┘
                            ▼
                ┌─────────────────────────┐
                │ 4. MVP Planner Agent     │
                │  - MVP features          │
                │  - 90-day roadmap        │
                │  - Tech stack            │
                └───────────┬──────────────┘
                            ▼
                ┌─────────────────────────┐
                │   Final Aggregator       │
                │  - Startup score (0-100) │
                │  - Investor verdict      │
                │  - Confidence score      │
                │  - Opportunity / Risk    │
                │  - Next step             │
                └───────────┬──────────────┘
                            ▼
                ┌─────────────────────────┐
                │   Streamlit Dashboard    │
                │  (Glassmorphic UI)       │
                └─────────────────────────┘
```

---

## 🔄 Agent Flow (LangGraph)

All agents share a single `StartupState` TypedDict. Each agent:

1. **Reads** relevant fields from the shared state.
2. **Processes** them using Gemini 2.5 Flash (and optionally Tavily search).
3. **Writes** its results back into the shared state.

The graph is strictly **linear** — no branches, no loops:

```python
graph.set_entry_point("market_research")
graph.add_edge("market_research", "competitor_analysis")
graph.add_edge("competitor_analysis", "business_strategy")
graph.add_edge("business_strategy", "mvp_planner")
graph.add_edge("mvp_planner", "final_aggregator")
graph.add_edge("final_aggregator", END)
```

This linear design makes the data flow easy to trace and explain.

---

## 📁 Project Structure

```
StartupIQ/
├── app.py            # Streamlit dashboard (UI)
├── agents.py         # LangGraph multi-agent pipeline
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

---

## ⚙️ Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd StartupIQ
   ```

2. **Create a virtual environment (recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables** (see below)

5. **Run the app**

   ```bash
   streamlit run app.py
   ```

---

## 🔑 Environment Variables

StartupIQ needs two API keys:

| Variable          | Purpose                                   | Where to get it                              |
|--------------------|-------------------------------------------|-----------------------------------------------|
| `GOOGLE_API_KEY`   | Access to Gemini 2.5 Flash                 | https://aistudio.google.com/app/apikey         |
| `TAVILY_API_KEY`   | Live web search for market/competitor data | https://tavily.com (free tier available)      |

### Local development

Create a `.streamlit/secrets.toml` file:

```toml
GOOGLE_API_KEY = "your-google-api-key"
TAVILY_API_KEY = "your-tavily-api-key"
```

Or set them as environment variables:

```bash
export GOOGLE_API_KEY="your-google-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```

---

## ☁️ Deployment Guide (Streamlit Community Cloud)

1. Push this project to a public (or private) GitHub repository.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **"New app"** and select your repository, branch, and `app.py`.
4. Under **"Advanced settings" → "Secrets"**, add:

   ```toml
   GOOGLE_API_KEY = "your-google-api-key"
   TAVILY_API_KEY = "your-tavily-api-key"
   ```

5. Click **Deploy**. No code changes are needed — it works out of the box.

---

## 🖼️ Screenshots

> _Add screenshots of the dashboard here after deployment._

- Hero section + input
- Startup score & verdict cards
- Market / Competitor tabs
- MVP roadmap tab

---

## 🎤 Interview Explanation Section

Use this section to confidently explain your project in interviews.

### What does this project do?

"StartupIQ takes a startup idea from the user and runs it through a
pipeline of AI agents. Each agent specializes in one part of startup
due diligence — market research, competitor analysis, business strategy,
and MVP planning. A final agent combines everything into an overall score
and an investor verdict, all displayed in a dashboard."

### Why LangGraph?

"LangGraph lets me define each agent as a node in a graph and connect
them with edges that represent the flow of information. It gives me a
shared state object (`StartupState`) that every agent can read from and
write to, so I don't have to manually pass data between function calls.
It also makes the architecture visual and easy to extend later — for
example, adding a branch for 'high-risk ideas need extra review' would
just mean adding a conditional edge."

### Why a Multi-Agent Architecture?

"Instead of asking one large prompt to do everything, I split the
problem into focused sub-tasks. Each agent has a narrow responsibility,
which makes prompts simpler, outputs more reliable, and the system easier
to debug — if the competitor analysis is wrong, I know exactly which
agent and prompt to fix."

### How do agents communicate?

"They all share one `StartupState` dictionary. Agent 1 writes
`market_overview` and `market_score`. Agent 2 reads those values to give
its competitor analysis better context, then writes its own results.
This continues down the chain, so by the time the Final Aggregator runs,
it has access to everything every previous agent produced."

### Why Gemini 2.5 Flash?

"Gemini 2.5 Flash is fast and cost-effective, which matters because this
pipeline makes 5 separate LLM calls per request. It's also strong at
following structured JSON output instructions, which I rely on heavily
to pass data between agents and the UI reliably."

### Why Tavily?

"Tavily provides real-time web search results. Since startup
validation depends on current market and competitor information — not
just what the model learned during training — I use Tavily to give the
Market Research and Competitor Analysis agents fresh, real-world context
before they generate their analysis."

---

## ❓ Common Interview Questions

**Q: What happens if an agent's LLM output isn't valid JSON?**
A: `agents.py` includes an `extract_json()` helper that strips markdown
code fences and uses regex to find the JSON object, with safe fallback
defaults so the app never crashes.

**Q: Is the graph state shared across requests?**
A: No — a fresh `StartupState` is created for every user request via
`run_validation()`, so there's no cross-user data leakage.

**Q: Why is the graph linear instead of using conditional edges?**
A: Simplicity. A linear pipeline is easy to trace, test, and explain.
Conditional branching could be a future enhancement (e.g., skip MVP
planning if the market score is too low).

**Q: How would you scale this?**
A: Add caching for repeated ideas, run independent agents in parallel
where state dependencies allow, and add a lightweight database to store
past reports — while keeping the same agent logic.

**Q: What if Tavily isn't configured?**
A: The `web_search()` function returns an empty string if no API key is
set, and agents simply rely on the LLM's own knowledge — the app degrades
gracefully rather than failing.

---

## 🛠️ Tech Stack Summary

- **Frontend:** Streamlit (custom glassmorphic CSS)
- **Agent Framework:** LangGraph (`StateGraph`)
- **LLM:** Google Gemini 2.5 Flash (`langchain-google-genai`)
- **Search:** Tavily Search API
- **Deployment:** Streamlit Community Cloud

---

## 📄 License

This project is open for educational and portfolio use.