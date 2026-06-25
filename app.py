import streamlit as st
from google import genai
from tinydb import TinyDB, Query
import os
import time

# Set up page configuration
st.set_page_config(page_title="AI Study Hub with History", page_icon="💬", layout="centered")
st.title("💬 Saved-Chat Study Hub")

# Securely fetch the API key from Streamlit secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

if not api_key:
    st.info("Please add your Gemini API Key to get started.", icon="🗝️")
    st.stop()

# Initialize Database and Gemini Client
db = TinyDB("db.json")
Session = Query()
client = genai.Client(api_key=api_key)

# Initialize active tracking states
if "text_context" not in st.session_state:
    st.session_state.text_context = ""
if "active_session_id" not in st.session_state:
    st.session_state.active_session_id = None

# --- SIDEBAR: CHAT SESSIONS & UPLOADS ---
with st.sidebar:
    st.header("📂 Study Material")
    uploaded_file = st.file_uploader("Upload PDF / Text", type=["pdf", "txt"])
    
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()
        if file_ext == "txt":
            st.session_state.text_context = uploaded_file.read().decode("utf-8")
        elif file_ext == "pdf":
            from pypdf import PdfReader
            pdf_reader = PdfReader(uploaded_file)
            st.session_state.text_context = "".join([page.extract_text() or "" for page in pdf_reader.pages])
        st.success(f"Context loaded: {uploaded_file.name}")

    st.markdown("---")
    st.header("🗂️ Previous Chat Logs")
    
    # 1. Fetch distinct session titles from DB
    all_records = db.all()
    distinct_sessions = sorted(list(set([r["session_id"] for r in all_records])), reverse=True)
    
    # Button to start a completely brand new chat
    if st.button("➕ Start New Chat Thread", use_container_width=True):
        st.session_state.active_session_id = f"Session_{int(time.time())}"
        st.rerun()

    # 2. Render list of saved chats as clickable sidebar buttons
    if distinct_sessions:
        st.caption("Click a session below to load it:")
        for idx, s_id in enumerate(distinct_sessions):
            # Clean up display text
            display_name = s_id.replace("_", " ")
            if st.button(f"📝 {display_name}", key=f"session_btn_{idx}", use_container_width=True):
                st.session_state.active_session_id = s_id
                st.rerun()
    else:
        st.info("No saved logs yet.")

# If no active session, spin up a default one
if not st.session_state.active_session_id:
    st.session_state.active_session_id = f"Session_{int(time.time())}"

# --- MAIN DISPLAY: FETCH & RENDER HISTORY ---
active_id = st.session_state.active_session_id
st.caption(f"Active Thread: **{active_id.replace('_', ' ')}**")

# Get logs for ONLY the selected session from TinyDB
session_logs = db.search(Session.session_id == active_id)

# Display historical sequence
for log in session_logs:
    with st.chat_message(log["role"]):
        st.markdown(log["content"])

# --- CHAT ENGINE LOOP ---
if prompt := st.chat_input("Ask a question about your files..."):
    # Render user prompt immediately
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Write user input permanently to JSON Database
    db.insert({"session_id": active_id, "role": "user", "content": prompt})

    # Prepare Context Prompt Engineering block
    context_instruction = f"""
    You are an expert tutor. Answer the user prompt accurately based on this context:
    {st.session_state.text_context if st.session_state.text_context else "No document attached yet."}
    """
    
    # Run Generation via Gemini API
    with st.chat_message("assistant"):
        with st.spinner("Retrieving answers..."):
            try:
                # Build context mapping payload
                payload = [context_instruction]
                # Include previous messages from THIS session for conversational continuity
                for log in session_logs:
                    payload.append(f"{log['role']}: {log['content']}")
                payload.append(f"user: {prompt}")
                
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=payload,
                )
                
                answer_text = response.text
                st.markdown(answer_text)
                
                # Write model output permanently to JSON Database
                db.insert({"session_id": active_id, "role": "assistant", "content": answer_text})
                
            except Exception as e:
                st.error(f"Error: {e}")
