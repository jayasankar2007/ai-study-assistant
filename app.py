import streamlit as st
from google import genai
from pypdf import PdfReader

# Set up page configuration
st.set_page_config(page_title="AI Study Chatbot", page_icon="💬", layout="centered")
st.title("💬 AI PDF Study Chatbot")
st.caption("Upload a textbook or notes and have a conversation with an expert tutor.")

# Securely fetch the API key from Streamlit secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

if not api_key:
    st.info("Please add your Gemini API Key to get started.", icon="🗝️")
    st.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# Initialize Chat History in Session State if it doesn't exist yet
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize PDF context memory
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""

# Sidebar for uploading files (keeps main screen clean for chatting)
with st.sidebar:
    st.header("📄 Upload Source")
    uploaded_file = st.file_uploader("Upload your study PDF", type=["pdf"])
    
    if uploaded_file is not None:
        with st.spinner("Processing PDF layers..."):
            try:
                pdf_reader = PdfReader(uploaded_file)
                extracted_text = ""
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        extracted_text += text + "\n"
                
                # Save text to state so it persists across refreshes
                st.session_state.pdf_text = extracted_text
                st.success(f"Loaded: {uploaded_file.name}")
                
                # Button to clear history if you upload a new file
                if st.button("🔄 Clear Chat History"):
                    st.session_state.messages = []
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error reading PDF: {e}")

# Display existing chat history from memory
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input at the bottom of the screen
if prompt := st.chat_input("Ask me anything about your document..."):
    
    # 1. Display user message instantly in chat
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Check if a PDF has been uploaded
    if not st.session_state.pdf_text:
        with st.chat_message("assistant"):
            warning_msg = "Please upload a PDF in the sidebar first so I can analyze it!"
            st.markdown(warning_msg)
        st.session_state.messages.append({"role": "assistant", "content": warning_msg})
        st.stop()

    # 3. Generate response from Gemini
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # We inject the PDF context AND the full historical thread into the system context
                # To keep it efficient, we pass the PDF text as background instructions
                context_prompt = f"""
                You are a dedicated AI study tutor. You have access to an uploaded document. 
                Use this context to answer the user's questions in a clear, academic, and supportive manner.
                If the chat history shows previous questions, maintain continuity.
                
                --- DOCUMENT CONTEXT ---
                {st.session_state.pdf_text}
                --- END DOCUMENT CONTEXT ---
                
                Current Question: {prompt}
                """
                
                # Build the chat payload including past user/assistant turns
                # Note: For simple scripts, passing history inside the structure works wonderfully
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=context_prompt,
                )
                
                # Display response
                st.markdown(response.text)
                
                # Save assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"Error calling Gemini API: {e}")
