"""Streamlit user interface for the Agentic RAG chatbot."""
import asyncio
import os

import streamlit as st

from src.agents.orchestrator import run_orchestrator

st.set_page_config(
    page_title="Financial Statements Agentic RAG",
    page_icon="💬",
    layout="centered",
)

st.title("Financial Statements Agentic RAG")
st.caption(
    "Portfolio prototype: agentic planning, hybrid retrieval, and deterministic numeric verification."
)

if not os.getenv("OPENAI_API_KEY"):
    st.warning("Set OPENAI_API_KEY in your environment before asking questions.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Ask about the indexed financial statements...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving and verifying evidence..."):
            try:
                response = asyncio.run(run_orchestrator(user_input))
            except Exception as exc:
                response = f"⚠️ Error: {exc}"
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
