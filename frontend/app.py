import os
import uuid
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="AI ChatBot with SynapticMemory", page_icon="🧠", layout="wide")

BASE_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

# Initialize session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())[:8]
    
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 Synaptic Memory")
    st.caption(f"Active Thread ID: `{st.session_state.thread_id}`")
    
    if st.button("➕ New Chat", use_container_width=True, type="primary"):
        st.session_state.thread_id = str(uuid.uuid4())[:8]
        st.session_state.messages = []
        st.rerun()
        
    st.markdown("---")
    
    # 1. Thread Selector
    st.subheader("💬 Previous Threads")
    try:
        threads_res = requests.get(f"{BASE_URL}/threads", timeout=2)
        if threads_res.status_code == 200:
            all_threads = threads_res.json().get("threads", [])
            for t in all_threads[-6:]:
                if st.button(f"Thread: {t}", key=f"btn_{t}", use_container_width=True):
                    st.session_state.thread_id = t
                    # Fetch chat history for this thread
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

    st.markdown("---")

    # 2. Live Synaptic Memory Inspector
    st.subheader("🔍 Memory Graph Inspector")
    try:
        mem_res = requests.get(f"{BASE_URL}/memory/{st.session_state.thread_id}", timeout=2)
        if mem_res.status_code == 200:
            mem_data = mem_res.json()
            active_facts = mem_data.get("active_facts", [])
            superseded = mem_data.get("resolved_contradictions", [])
            
            with st.expander(f"Active Beliefs ({len(active_facts)})", expanded=True):
                if active_facts:
                    for f in active_facts:
                        st.markdown(f"- **{f['subject']}** `{f['predicate']}`: *{f['object']}*")
                else:
                    st.caption("No facts extracted yet.")
                    
            with st.expander(f"Resolved Conflicts ({len(superseded)})"):
                if superseded:
                    for f in superseded:
                        st.markdown(f"- ✗ ~~{f['subject']}: {f['object']}~~ *(Superseded)*")
                else:
                    st.caption("No contradictions yet.")
    except Exception:
        st.caption("Memory inspector unavailable.")

# --- MAIN CHAT AREA ---
st.title("🤖 AI Assistant with Neuro-Cognitive Memory")
st.caption("Equipped with Long-Term Memory, Automatic Contradiction Resolution, and Sub-300 Token Compaction.")

# Render message history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("Ask a question, set your preferences, or update your stack..."):
    # 1. Display and save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Call FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking & updating memory..."):
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