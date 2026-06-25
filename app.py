import streamlit as st
from google import genai

# Set up page configuration
st.set_page_config(page_title="AI Study Assistant", page_icon="📚", layout="centered")
st.title("📚 Your AI Study Assistant")
st.caption("Upload your notes/textbook and ask anything!")

# 1. Securely fetch the API key from Streamlit secrets
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    # Fallback to a sidebar input if not deployed yet
    api_key = st.sidebar.text_input("Enter Google Gemini API Key", type="password")

if not api_key:
    st.info("Please add your Gemini API Key to get started.", icon="🗝️")
    st.stop()

# Initialize the Gemini Client
client = genai.Client(api_key=api_key)

# 2. File Uploader Widget (Supports Text, Markdown, or Python files)
uploaded_file = st.file_uploader("Upload your study document (.txt, .md, or .py)", type=["txt", "md", "py"])

if uploaded_file is not None:
    # Read the text content of the uploaded file
    document_content = uploaded_file.read().decode("utf-8")
    st.success(f"Successfully loaded: '{uploaded_file.name}'!")
    
    # 3. User Question Input
    user_question = st.text_input("Ask a question about this material:", placeholder="e.g., Summarize the main points.")
    
    if user_question:
        with st.spinner("Analyzing your document and thinking..."):
            try:
                # Structure the prompt to give context to the AI
                prompt = f"""
                You are a helpful academic tutor. Use the following uploaded study content to answer the user's question accurately.
                
                --- STUDY CONTENT START ---
                {document_content}
                --- STUDY CONTENT END ---
                
                User Question: {user_question}
                """
                
                # Generate response using the fast gemini-2.5-flash model
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # Display the answer nicely
                st.subheader("💡 Answer:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")