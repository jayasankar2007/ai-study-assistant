import streamlit as st
from google import genai
from pypdf import PdfReader

# Set up page configuration
st.set_page_config(page_title="AI PDF Study Assistant", page_icon="📚", layout="centered")
st.title("📚 AI PDF Study Assistant")
st.caption("Upload your PDFs and textbooks, then ask anything!")

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

# Updated File Uploader to accept PDFs
uploaded_file = st.file_uploader("Upload your study PDF", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("Extracting text from PDF..."):
        try:
            # Read the PDF layers
            pdf_reader = PdfReader(uploaded_file)
            extracted_text = ""
            
            # Loop through pages and extract text
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
            
            st.success(f"Successfully processed: '{uploaded_file.name}' ({len(pdf_reader.pages)} pages)!")
        except Exception as e:
            st.error(f"Error reading PDF file: {e}")
            st.stop()
    
    # User Question Input
    user_question = st.text_input("Ask a question about this PDF:", placeholder="e.g., Explain the core concept of chapter 2.")
    
    if user_question:
        with st.spinner("Analyzing document and generating answer..."):
            try:
                # Structure the prompt with the extracted PDF content
                prompt = f"""
                You are a brilliant academic tutor. Use the following context extracted from a study PDF to answer the user's question accurately.
                If the answer cannot be found in the text, use your general knowledge but mention that it wasn't explicitly in the document.
                
                --- STUDY PDF CONTENT START ---
                {extracted_text}
                --- STUDY PDF CONTENT END ---
                
                User Question: {user_question}
                """
                
                # Generate response using gemini-2.5-flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                )
                
                # Display the answer
                st.subheader("💡 Answer:")
                st.write(response.text)
                
            except Exception as e:
                st.error(f"An error occurred while generating the answer: {e}")
