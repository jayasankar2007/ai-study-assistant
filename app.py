import streamlit as st
from google import genai
import os

# Set up page configuration
st.set_page_config(page_title="Multimodal AI Study Hub", page_icon="🎓", layout="centered")
st.title("🎓 Multimodal AI Study Hub")
st.caption("Upload PDFs, Documents, Audio lectures, or Videos and talk to your personal tutor.")

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

# Initialize persistent memory segments
if "messages" not in st.session_state:
    st.session_state.messages = []
if "active_file_ref" not in st.session_state:
    st.session_state.active_file_ref = None
if "text_context" not in st.session_state:
    st.session_state.text_context = ""

# Sidebar logic for uploading ANY media type
with st.sidebar:
    st.header("📂 Upload Study Materials")
    uploaded_file = st.file_uploader(
        "Supports PDF, TXT, Audio (MP3/WAV), or Video (MP4)", 
        type=["pdf", "txt", "mp3", "wav", "mp4"]
    )
    
    if uploaded_file is not None:
        # Check if we've already uploaded this exact file to avoid double uploads
        if "last_uploaded_name" not in st.session_state or st.session_state.last_uploaded_name != uploaded_file.name:
            
            with st.spinner(f"Processing and indexing '{uploaded_file.name}'..."):
                file_ext = uploaded_file.name.split(".")[-1].lower()
                
                # Clear previous session contexts cleanly
                st.session_state.active_file_ref = None
                st.session_state.text_context = ""
                st.session_state.messages = []
                
                try:
                    # ROUTE A: Handle raw text structures or small code/notes files
                    if file_ext in ["txt"]:
                        st.session_state.text_context = uploaded_file.read().decode("utf-8")
                        st.success("Loaded plain text file context successfully!")
                        
                    elif file_ext in ["pdf"]:
                        from pypdf import PdfReader
                        pdf_reader = PdfReader(uploaded_file)
                        extracted_text = "".join([page.extract_text() or "" for page in pdf_reader.pages])
                        st.session_state.text_context = extracted_text
                        st.success(f"Extracted text from PDF ({len(pdf_reader.pages)} pages)!")
                        
                    # ROUTE B: Handle Heavy Audio/Video via the Files API
                    elif file_ext in ["mp3", "wav", "mp4"]:
                        # Save uploaded file temporarily to local disk so the SDK can push it
                        temp_filename = f"temp_upload_source.{file_ext}"
                        with open(temp_filename, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # Upload using Google GenAI Files cloud infrastructure
                        cloud_file = client.files.upload(file=temp_filename)
                        st.session_state.active_file_ref = cloud_file
                        
                        # Clean up local temporary file
                        if os.path.exists(temp_filename):
                            os.remove(temp_filename)
                            
                        st.success("Media successfully uploaded and cached into Gemini Cloud! Ready to discuss.")
                        
                    st.session_state.last_uploaded_name = uploaded_file.name
                except Exception as e:
                    st.error(f"Failed to process file: {e}")

    if st.button("🔄 Clear Active Thread"):
        st.session_state.messages = []
        st.rerun()

# Render active chat timeline UI
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Main Chat loop
if prompt := st.chat_input("Ask a question about your uploaded materials..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Block requests if no content context exists
    if not st.session_state.text_context and not st.session_state.active_file_ref:
        with st.chat_message("assistant"):
            st.markdown("Please upload a file in the left sidebar configuration panel before chatting!")
        st.stop()

    with st.chat_message("assistant"):
        with st.spinner("Analyzing content timeline..."):
            try:
                # Compile dynamic contents payloads depending on document type
                payload_contents = []
                
                # Append structural file cloud indicators if media track is active
                if st.session_state.active_file_ref:
                    payload_contents.append(st.session_state.active_file_ref)
                
                # Inject prompt engineering block context
                system_instruction = f"""
                You are an expert multi-disciplinary university professor.
                Analyze the attached media/document to provide structurally clear explanations, definitions, or code syntax where appropriate.
                
                Text Context (if applicable):
                {st.session_state.text_context}
                """
                
                payload_contents.append(system_instruction)
                payload_contents.append(f"User Query: {prompt}")
                
                # Run content evaluation via modern gemini-2.5-flash
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=payload_contents,
                )
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
                
            except Exception as e:
                st.error(f"API Generation Error: {e}")
