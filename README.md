#  Monday.com Founder BI Agent
<img width="726" height="916" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/baebdf46-dff0-495b-b357-de0a4188824f" />




##  Overview

This system allows founders and executives to ask questions like:

- 💰 “What’s our current weighted pipeline?”
- 📈 “How much revenue is closing this month?”
- 🛠 “Which work orders are delayed?”
- 📊 “What are our operational bottlenecks?”

The agent autonomously:

- Breaks down complex queries
- Selects the correct data source
- Calls live Monday.com APIs
- Computes raw facts
- Formats a clean executive summary

---

# ✨ Key Capabilities

### 🔎 Intelligent Query Decomposition
Breaks complex business questions into structured sub-queries using a Pydantic schema.

### 🧮 Accurate BI Computation
Pulls live data from Monday.com and computes real metrics.

### 📊 Multi-Board Intelligence
Understands relationships between:
- Sales Pipeline (Deals Board)
- Work Orders Tracker
- Revenue & Operational Metrics

### 🧾 Executive-Ready Output
Returns beautifully formatted Markdown summaries:
- Bold KPIs
- Bullet points
- Clean sections
- Data Caveats

---

# 🏗️ System Architecture

```
User Query
    ↓
query_breakdown
    ↓
agent (BI Analyst)
    ↓
Monday.com Tools
    ↓
response_formatter
    ↓
Executive Summary
```

---

## 1️⃣ query_breakdown

**Role:** Strategic Planner

- Takes user query
- Breaks into logical sub-queries
- Uses structured LLM output via Pydantic
- Ensures deterministic task planning

---

## 2️⃣ agent

**Role:** Senior BI Data Analyst

Responsibilities:

- Select correct Monday.com tool
- Call tools
- Compute accurate metrics
- Ask clarifying questions if needed
- Return raw analytical facts only

⚠️ The agent does NOT format output.  
It focuses purely on data accuracy.

---

## 3️⃣ tools (Monday.com Integrations)

All tools use Monday.com’s GraphQL API.

| Tool | Description |
|------|-------------|
| `fetch_all_deals_data()` | Pulls entire Sales Pipeline board |
| `search_specific_deal(item_name)` | Finds a specific deal |
| `fetch_all_work_orders_data()` | Pulls entire Work Orders board |
| `search_specific_work_order(item_name)` | Finds a specific work order |

---

## 4️⃣ response_formatter

**Role:** Executive Assistant

- Converts raw facts into clean Markdown
- Highlights key metrics
- Adds Risks section
- Adds Data Caveats section
- Does NOT modify numbers

---

# 📈 Example Output

### Executive Summary

**Total Open Pipeline:** $1.42M  
**Weighted Pipeline:** $930K  
**Deals Closing This Month:** 6  
**Delayed Work Orders:** 3  

---

### 🚨 Risks

- 42% of revenue tied to 2 deals
- 3 work orders overdue >14 days

---

### 📌 Data Caveats

- 1 deal missing probability field  
- 2 work orders missing due date  

---

# 🛠 Tech Stack

- LangGraph – Stateful agent orchestration
- LangChain – Tool abstraction
- OpenAI – LLM reasoning
- Monday.com GraphQL API – Live business data
- Pydantic – Structured output validation

