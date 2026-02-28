

import os
import requests
import json
from typing import List, Annotated, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver



import os
from dotenv import load_dotenv

load_dotenv()  # Loads variables from .env

openai_api_key = os.getenv("OPENAI_API_KEY")
monday_api_key = os.getenv("MONDAY_API_KEY")


# 1. DEFINE THE 4 MONDAY.COM TOOLS

@tool
def fetch_all_deals_data() -> str:
    """Fetches all items from the Deals / Sales Pipeline board (Overall revenue/pipeline)."""
    url = "https://api.monday.com/v2"
    headers = {"Authorization": os.environ.get("MONDAY_API_KEY"), "API-Version": "2024-01", "Content-Type": "application/json"}
    query = """query { boards(ids:["5026876479"]) { name items_page(limit: 100) { items { name column_values { column { title } text } } } } }"""
    response = requests.post(url, json={"query": query}, headers=headers)
    if response.status_code != 200: return json.dumps({"error": f"API status {response.status_code}"})
    try:
        items = response.json()["data"]["boards"][0]["items_page"]["items"]
        cleaned =[{"Item": i.get("name", "Unknown"), **{c["column"]["title"]: c.get("text", "N/A") or "N/A" for c in i.get("column_values",[])}} for i in items]
        return json.dumps({"board": "Deals Data", "data": cleaned})
    except Exception as e: return json.dumps({"error": str(e)})

@tool
def search_specific_deal(item_name: str) -> str:
    """Searches for a specific item strictly on the Deals board."""
    url = "https://api.monday.com/v2"
    headers = {"Authorization": os.environ.get("MONDAY_API_KEY"), "API-Version": "2024-01", "Content-Type": "application/json"}
    query = """query ($item_name: String!) { items_page_by_column_values(limit: 10, board_id: "5026876479", columns:[{column_id: "name", column_values:[$item_name]}]) { items { name column_values { column { title } text } } } }"""
    response = requests.post(url, json={"query": query, "variables": {"item_name": item_name}}, headers=headers)
    try:
        items = response.json()["data"]["items_page_by_column_values"]["items"]
        if not items: return json.dumps({"error": f"Deal '{item_name}' not found."})
        cleaned =[{"Item": i.get("name", "Unknown"), **{c["column"]["title"]: c.get("text", "N/A") or "N/A" for c in i.get("column_values",[])}} for i in items]
        return json.dumps({"board": "Deals Data", "data": cleaned})
    except Exception as e: return json.dumps({"error": str(e)})

@tool
def fetch_all_work_orders_data() -> str:
    """Fetches all items from the Work Orders Tracker board."""
    url = "https://api.monday.com/v2"
    headers = {"Authorization": os.environ.get("MONDAY_API_KEY"), "API-Version": "2024-01", "Content-Type": "application/json"}
    query = """query { boards(ids:["5026876495"]) { name items_page(limit: 100) { items { name column_values { column { title } text } } } } }"""
    response = requests.post(url, json={"query": query}, headers=headers)
    if response.status_code != 200: return json.dumps({"error": f"API status {response.status_code}"})
    try:
        items = response.json()["data"]["boards"][0]["items_page"]["items"]
        cleaned =[{"Item": i.get("name", "Unknown"), **{c["column"]["title"]: c.get("text", "N/A") or "N/A" for c in i.get("column_values",[])}} for i in items]
        return json.dumps({"board": "Work Orders Tracker", "data": cleaned})
    except Exception as e: return json.dumps({"error": str(e)})

@tool
def search_specific_work_order(item_name: str) -> str:
    """Searches for a specific item strictly on the Work Orders Tracker board."""
    url = "https://api.monday.com/v2"
    headers = {"Authorization": os.environ.get("MONDAY_API_KEY"), "API-Version": "2024-01", "Content-Type": "application/json"}
    query = """query ($item_name: String!) { items_page_by_column_values(limit: 10, board_id: "5026876495", columns:[{column_id: "name", column_values:[$item_name]}]) { items { name column_values { column { title } text } } } }"""
    response = requests.post(url, json={"query": query, "variables": {"item_name": item_name}}, headers=headers)
    try:
        items = response.json()["data"]["items_page_by_column_values"]["items"]
        if not items: return json.dumps({"error": f"Work Order '{item_name}' not found."})
        cleaned =[{"Item": i.get("name", "Unknown"), **{c["column"]["title"]: c.get("text", "N/A") or "N/A" for c in i.get("column_values",[])}} for i in items]
        return json.dumps({"board": "Work Orders Tracker", "data": cleaned})
    except Exception as e: return json.dumps({"error": str(e)})





# 2. DEFINE STATE & SCHEMA


class State(TypedDict):
    messages: Annotated[list, add_messages]
    sub_queries: List[str]

class QueryBreakdown(BaseModel):
    sub_queries: List[str] = Field(description="List of individual, simpler questions broken down from the user's main query.")





# 3. DEFINE LANGGRAPH NODE

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
tools =[fetch_all_deals_data, search_specific_deal, fetch_all_work_orders_data, search_specific_work_order]
llm_with_tools = llm.bind_tools(tools)

def query_breakdown_node(state: State):
    """Node 1: Intercepts user input and breaks it into smaller logical sub-queries."""
    user_query = state["messages"][-1].content
    structured_llm = llm.with_structured_output(QueryBreakdown)
    prompt = f"Break down this query into simple, logical sub-questions: '{user_query}'"
    result = structured_llm.invoke(prompt)
    return {"sub_queries": result.sub_queries}

def agent_node(state: State):
    """Node 2: The logical brain. Queries data and calculates facts."""
    sub_queries = state.get("sub_queries",[])
    sys_prompt = SystemMessage(content=(
        "You are an expert BI Data Analyst. Your ONLY job is to pull data from monday.com and calculate the raw facts.\n"
        f"Tasks: {sub_queries}\n"
        "RULES:\n"
        "1. Focus purely on accuracy. You do not need to format the final output beautifully, just provide the facts.\n"
        "2. If a query spans both boards, call the appropriate search tools for both boards.\n"
        "3. If missing a specific name, ask a clarifying question."
    ))
    messages_to_process = [sys_prompt] + state["messages"]
    response = llm_with_tools.invoke(messages_to_process)
    return {"messages": [response]}

def response_formatter_node(state: State):
    """Node 3 (NEW): Takes the raw data/facts from the agent and formats them beautifully."""
    raw_agent_response = state["messages"][-1].content

    sys_prompt = SystemMessage(content=(
        "You are an Executive Assistant and BI Report Writer for a founder. "
        "Your task is to take the raw analytical data provided by the AI Data Analyst and format it into a "
        "beautiful, clean, and highly readable Executive Summary using Markdown.\n\n"
        "RULES:\n"
        "- Use clear headings, bullet points, and bold text for key metrics.\n"
        "- If the raw data contains caveats (like missing values), clearly highlight them in a 'Data Caveats' section.\n"
        "- DO NOT change any numbers or facts.\n"
        "- If the raw response is just asking a simple clarifying question (e.g., 'What is the person's name?'), "
        "just return the question cleanly without over-formatting it."
    ))

    # We use a standard LLM call here to generate the beautiful formatting
    formatter_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3) # slightly higher temp for better formatting
    formatted_response = formatter_llm.invoke([sys_prompt, HumanMessage(content=raw_agent_response)])

    return {"messages": [formatted_response]}






# 4. CUSTOM ROUTING FUNCTION

def route_after_agent(state: State) -> Literal["tools", "response_formatter"]:
    """
    If the Agent wants to call a tool, route to 'tools'.
    If the Agent gave a final text answer, route to 'response_formatter' instead of END.
    """
    last_message = state["messages"][-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"

    return "response_formatter"





# 5. BUILD THE GRAPH WITH MEMORY

graph_builder = StateGraph(State)

# Add Nodes
graph_builder.add_node("query_breakdown", query_breakdown_node)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", ToolNode(tools=tools))
graph_builder.add_node("response_formatter", response_formatter_node) # <-- ADD THE FORMATTER NODE

# Add Edges
graph_builder.add_edge(START, "query_breakdown")
graph_builder.add_edge("query_breakdown", "agent")

# Use our Custom Router!
graph_builder.add_conditional_edges("agent", route_after_agent)
graph_builder.add_edge("tools", "agent")

# The Formatter Node is now the final step before returning to the user
graph_builder.add_edge("response_formatter", END)

# Compile with Memory
memory = MemorySaver()
app = graph_builder.compile(checkpointer=memory)

# ==========================================
# 6. EXECUTION & CLI (WITH TRACES)
# ==========================================
# --- Replace the bottom terminal execution block in your code with this ---
import streamlit as st
import uuid

# Set up the Web Page
st.set_page_config(page_title="Founder BI Agent", page_icon="📊")
st.title("📊 Monday.com BI Agent")
st.markdown("Ask founder-level questions about the Sales Pipeline and Work Orders.")

# Initialize session state for memory and UI chat history
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4()) # Unique session per user
if "messages" not in st.session_state:
    st.session_state.messages =[]

config = {"configurable": {"thread_id": st.session_state.thread_id}}

# Display previous chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input Box
if user_input := st.chat_input("e.g., How is our pipeline for the energy sector?"):

    # 1. Add user message to UI
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2. Add AI response to UI
    with st.chat_message("assistant"):
        # This creates a nice dropdown box for the Evaluator to see the traces!
        with st.status("Agent is thinking... (Click to view traces)", expanded=True) as status:

            final_response = ""
            events = app.stream({"messages":[HumanMessage(content=user_input)]}, config=config)

            for event in events:
                if "query_breakdown" in event:
                    st.write(f"🧩 **Breakdown:** {event['query_breakdown']['sub_queries']}")

                elif "agent" in event:
                    agent_message = event["agent"]["messages"][-1]
                    if agent_message.tool_calls:
                        for tc in agent_message.tool_calls:
                            st.write(f"🛠️ **Tool Call:** `{tc['name']}`")
                    elif agent_message.content and not final_response:
                        # If agent asks a clarifying question directly
                        final_response = agent_message.content

                elif "tools" in event:
                    st.write("✅ **Live Data Extracted from Monday.com**")

                elif "response_formatter" in event:
                    final_response = event["response_formatter"]["messages"][-1].content

            status.update(label="Finished Processing", state="complete", expanded=False)

        # 3. Print the final beautiful answer
        st.markdown(final_response)

        st.session_state.messages.append({"role": "assistant", "content": final_response})
