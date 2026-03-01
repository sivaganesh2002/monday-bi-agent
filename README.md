<img width="726" height="916" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/663254f4-d86f-440e-9fcf-3e454c6cae4c" />
Monday.com Founder BI Agent

An AI-powered Founder-Level Business Intelligence Agent built using LangGraph, LangChain, OpenAI, and Monday.com API.

This system allows founders and executives to ask natural language questions about:

💰 Sales Pipeline (Deals Board)

🛠 Work Orders Tracker

📈 Revenue & Operational Metrics

The agent autonomously:

Breaks down complex queries

Selects the correct data source

Calls live Monday.com APIs

Computes raw facts

Formats a clean executive summary

System Architecture
1️⃣ query_breakdown

Takes the user query

Breaks it into smaller logical sub-queries

Uses structured LLM output via Pydantic schema

2️⃣ agent

Acts as the BI Data Analyst

Decides which Monday.com tool to call

Focuses purely on data accuracy

Can:

Call tools

Ask clarifying questions

Return raw analytical facts

3️⃣ tools

Connected Monday.com tools:

Tool	Description
fetch_all_deals_data()	Pulls entire Sales Pipeline board
search_specific_deal(item_name)	Finds a specific deal
fetch_all_work_orders_data()	Pulls entire Work Orders board
search_specific_work_order(item_name)	Finds a specific work order

All tools use Monday.com's GraphQL API.

4️⃣ response_formatter

Acts as an Executive Assistant

Converts raw analytical output into:

Clean Markdown

Bullet points

Bold metrics

Executive summaries

Highlights missing data in a Data Caveats section

Does NOT modify numbers
