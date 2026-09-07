import os
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI ChatBot", page_icon="🤖", layout="wide")

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]
    
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("🤖 AI ChatBot")
    st.caption(f"Active Thread ID: `{st.session_state.thread_id}`")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    
    st.subheader("💬 Previous Threads")
    try:
        threads_res = requests.get(f"{BASE_URL}/threads", timeout=2)
        if threads_res.status_code == 200:
            all_threads = threads_res.json().get("threads", [])
            for t in all_threads[-6:]:
                if st.button(f"Thread: {t}", key=f"btn_{t}", use_container_width=True):
                    st.session_state.thread_id = t
                    hist_res = requests.get(f"{BASE_URL}/threads/{t}", timeout=2)
                    if hist_res.status_code == 200:
                        st.session_state.messages = []
                        for h in hist_res.json():
                            st.session_state.messages.append({"role": "user", "content": h["user_msg"]})
                            if h.get("ai_reply"):
                                st.session_state.messages.append({"role": "assistant", "content": h["ai_reply"]})
                    st.rerun()
    except Exception:
        st.caption("Backend not connected yet.")

st.title("🤖 AI Assistant")
st.caption("AI Assistant powered by LangGraph, Groq, and FastAPI.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask a question, set your preferences, or update your stack..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    f"{BASE_URL}/chat",
                    json={
                        "thread_id": st.session_state.thread_id,
                        "message": prompt
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    ai_reply = response.json().get("ai_msg", "")
                    st.markdown(ai_reply)
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.rerun()
                else:
                    st.error(f"Backend error: {response.text}")
            except Exception as e:
                st.error(f"Could not connect to backend: {e}")