import os
import sqlite3
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
import re

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# --- Load environment variables ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
DB_PATH = os.getenv("DB_PATH", "src/banking_system.db")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Functions ---

@st.cache_data
def get_schema():
    """Caches the database schema to avoid reading the file on every run."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'banking_schema_sqlite.sql')
    with open(schema_path, 'r') as f:
        return f.read()

def run_query(query):
    """Connects to the DB and runs the given SQL query."""
    db_full_path = os.path.join(os.path.dirname(__file__), '..', '..', DB_PATH)
    conn = sqlite3.connect(db_full_path)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- Agent Setup ---

if not GROQ_API_KEY:
    st.error("❌ No Groq API key found. Please add it to the .env file in the 'code' directory.")
else:
    llm = ChatGroq(model="llama-3.1-8b-instant", api_key=GROQ_API_KEY)

    db_schema = get_schema()

    system_prompt = f"""
    You are a highly intelligent SQLite expert. Your task is to convert a user's natural language question into a valid SQLite query.

    **INSTRUCTIONS:**
    1. If the request is ambiguous and you truly cannot generate SQL, ask ONE clarification question (prefixed with `CLARIFICATION:`).
    2. Otherwise, make reasonable assumptions and generate the best possible SQL query directly.
    3. NEVER invent columns or tables — only use what is explicitly in the schema.
    4. Use JOINs correctly (e.g., to get a customer's city, JOIN `customers` with `branches`).
    5. Return ONLY the raw SQL query (or a clarification if absolutely needed). No explanations, no markdown.

    **Schema:**
    ```sql
    {db_schema}
    ```
    """

    # LangGraph state
    class State(dict):
        messages: list

    workflow = StateGraph(State)

    def call_llm(state: State):
        response = llm.invoke([SystemMessage(content=system_prompt)] + state["messages"])
        return {"messages": state["messages"] + [response]}

    workflow.add_node("llm", call_llm)
    workflow.set_entry_point("llm")
    workflow.add_edge("llm", END)

    agent_executor = workflow.compile()

    def run_agent(messages):
        events = agent_executor.stream({"messages": messages}, stream_mode="values")
        response = None
        for event in events:
            response = event["messages"][-1].content
        return response

# --- UI ---

st.set_page_config(page_title="Banking AI Assistant", layout="wide")

with st.sidebar:
    st.title("💳 Banking AI Assistant")
    st.info("This app uses AI to answer your questions about the bank's database. It remembers the conversation context and asks for clarification if needed.")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.results = []   # also clear results
        st.rerun()
    st.markdown("---")
    st.header("Example Conversation")
    st.markdown("1. **You:** Show me recent transactions.")
    st.markdown("2. **AI:** CLARIFICATION: What timeframe do you consider 'recent'?")
    st.markdown("3. **You:** In the last 7 days.")

if "messages" not in st.session_state:
    st.session_state.messages = []

if "results" not in st.session_state:
    st.session_state.results = []   # store query results persistently

st.header("Query the Banking Database")

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Get new user input
if user_input := st.chat_input("Ask a question about the database..."):

    # Handle clarification chaining
    if len(st.session_state.messages) >= 2:
        last_assistant = st.session_state.messages[-1]
        if "clarification" in last_assistant["content"].lower():
            # Merge clarification answer into previous user query
            st.session_state.messages[-2]["content"] += " " + user_input
            user_input = None

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            # Build conversation history with schema prompt only once
            schema_prompt = SystemMessage(content=system_prompt)
            api_messages = [schema_prompt]
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    api_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    api_messages.append(AIMessage(content=msg["content"]))

            response_from_model = run_agent(api_messages)

        if response_from_model:
            if response_from_model.startswith("CLARIFICATION:"):
                clarification_text = response_from_model.replace("CLARIFICATION:", "").strip()
                st.markdown(clarification_text)
                st.session_state.messages.append({"role": "assistant", "content": clarification_text})
            else:
                match = re.search(r'SELECT .*', response_from_model, re.IGNORECASE | re.DOTALL)
                sql = match.group(0).strip() if match else response_from_model.strip()
                if sql.endswith(';'):
                    sql = sql[:-1]
                st.code(sql, language="sql")
                try:
                    with st.spinner("🔍 Running query..."):
                        result_df = run_query(sql)

                    # Save result for history
                    st.session_state.results.append({"sql": sql, "data": result_df})
                    st.session_state.messages.append({"role": "assistant", "content": sql})

                except Exception as e:
                    error_message = f"Error running query: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": error_message})
        else:
            warning_message = "Could not generate a response. Please try rephrasing your question."
            st.warning(warning_message)
            st.session_state.messages.append({"role": "assistant", "content": warning_message})

# --- Show Results History ---
if st.session_state.results:
    st.subheader("📊 Query Results History")
    for i, res in enumerate(st.session_state.results):
        st.markdown(f"**Query {i+1}:**")
        st.code(res["sql"], language="sql")
        st.dataframe(res["data"])
