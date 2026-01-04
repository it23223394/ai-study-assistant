"""
Streamlit App for AI Study Assistant
Main user interface for the PDF tutor
"""

import streamlit as st
import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv
import fitz  # PyMuPDF - no external dependencies needed!
from PIL import Image
from io import BytesIO

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from pdf_processor import PDFProcessor
from rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if "pdf_processor" not in st.session_state:
    st.session_state.pdf_processor = PDFProcessor()

if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None

if "chunks" not in st.session_state:
    st.session_state.chunks = None

if "pdf_loaded" not in st.session_state:
    st.session_state.pdf_loaded = False

if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

if "pdf_images" not in st.session_state:
    st.session_state.pdf_images = None

if "current_page" not in st.session_state:
    st.session_state.current_page = 0

# Load system prompt
@st.cache_resource
def load_system_prompt():
    """Load the tutor system prompt"""
    prompt_path = "prompts/tutor_prompt.txt"
    try:
        with open(prompt_path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"System prompt not found at {prompt_path}")
        return "You are a helpful AI tutor. Answer questions based on the provided course material."

system_prompt = load_system_prompt()

# Main app layout
st.title("📚 AI Study Assistant")
st.markdown("Your Personal AI Tutor for Course PDFs")

# Sidebar for PDF upload
with st.sidebar:
    st.header("📤 Upload & Process PDF")
    
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload your course notes, lecture slides, or textbook PDF"
    )
    
    if uploaded_file is not None:
        # Save uploaded file
        pdf_path = f"data/uploaded_pdfs/{uploaded_file.name}"
        os.makedirs("data/uploaded_pdfs", exist_ok=True)
        
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.session_state.pdf_path = pdf_path
        st.success(f"✅ Successfully uploaded: **{uploaded_file.name}**")
        
        # Convert PDF to images using PyMuPDF (no poppler needed!)
        with st.spinner("Converting PDF to images..."):
            try:
                pdf_document = fitz.open(pdf_path)
                images = []
                for page_num in range(len(pdf_document)):
                    page = pdf_document[page_num]
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))  # 1.5x zoom for better quality
                    images.append(pix.tobytes("ppm"))
                st.session_state.pdf_images = images
                st.session_state.current_page = 0  # Reset to first page
                pdf_document.close()
                st.success(f"✅ Ready for viewing · {len(st.session_state.pdf_images)} pages loaded")
            except Exception as e:
                st.error(f"Error converting PDF: {str(e)}")
        
        # Process PDF button
        st.markdown('<div style="margin-top: 15px;"></div>', unsafe_allow_html=True)
        if st.button("🚀 Process PDF for Q&A", use_container_width=True, type="primary", help="Extract text and create search embeddings"):
            with st.spinner("Processing PDF..."):
                try:
                    # Extract and chunk text
                    st.session_state.chunks = st.session_state.pdf_processor.process_pdf(pdf_path)
                    
                    # Initialize RAG pipeline
                    st.session_state.rag_pipeline = RAGPipeline()
                    
                    # Ingest documents
                    with st.spinner("Creating embeddings (this may take a minute)..."):
                        st.session_state.rag_pipeline.ingest_documents(st.session_state.chunks)
                    
                    st.session_state.pdf_loaded = True
                    st.success(f"✅ PDF processed! · {len(st.session_state.chunks)} sections extracted")
                    st.info(f"Ready! Start asking questions about your PDF on the left →")
                
                except Exception as e:
                    st.error(f"❌ Error processing PDF: {str(e)}")
                    logger.error(f"Error: {str(e)}")
    
    # Display API key warning
    if not os.getenv("GROQ_API_KEY"):
        st.error("⚠️ API Key Required - Get your FREE Groq API key at https://console.groq.com and add it to Streamlit Secrets")

# Main content
if st.session_state.pdf_loaded and st.session_state.rag_pipeline:
    st.markdown("---")
    
    # Create two-column layout
    col_left, col_right = st.columns([1, 1], gap="medium")
    
    # LEFT COLUMN: Question and Answer
    with col_left:
        st.markdown('<div class="section-header">❓ Ask Your Question</div>', unsafe_allow_html=True)
        question = st.text_area(
            "Your question:",
            placeholder="e.g., 'What is the main concept of Chapter 2?'",
            height=100,
            label_visibility="collapsed"
        )
        
        col_btn1, col_btn2 = st.columns([2, 1])
        
        with col_btn1:
            submit_button = st.button("🧠 Get Answer", use_container_width=True, type="primary", help="Send question to AI tutor")
        
        with col_btn2:
            retrieval_slider = st.slider("Sources:", 1, 5, 3, help="Number of PDF sections to reference")
        
        # Answer display
        if submit_button and question:
            with st.spinner("Generating answer..."):
                try:
                    answer, retrieved = st.session_state.rag_pipeline.answer_question(
                        question,
                        system_prompt,
                        top_k=retrieval_slider
                    )
                    
                    # Display answer
                    st.markdown("---")
                    st.subheader("✨ Answer")
                    st.write(answer)
                    
                    # Display retrieved chunks
                    with st.expander(f"📖 Source Material ({len(retrieved)} sections referenced)", expanded=False):
                        for i, (chunk, score) in enumerate(retrieved, 1):
                            st.markdown(f"**Section {i}** · Relevance: {score:.0%}")
                            st.info(chunk[:400] + "..." if len(chunk) > 400 else chunk)
                            st.divider()
                    
                except Exception as e:
                    st.error(f"❌ Error generating answer: {str(e)}")
                    logger.error(f"Error: {str(e)}")
        
        elif submit_button and not question:
            st.warning("⚠️ Please enter a question first!")
    
    # RIGHT COLUMN: PDF Viewer
    with col_right:
        st.subheader("📄 PDF Document")
        
        if st.session_state.pdf_images:
            total_pages = len(st.session_state.pdf_images)
            
            # Page navigation controls
            nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])
            
            with nav_col1:
                if st.button("⬅️ Previous"):
                    st.session_state.current_page = max(0, st.session_state.current_page - 1)
            
            with nav_col2:
                selected_page = st.slider(
                    "Page",
                    min_value=1,
                    max_value=total_pages,
                    value=st.session_state.current_page + 1,
                    label_visibility="collapsed"
                )
                st.session_state.current_page = selected_page - 1
            
            with nav_col3:
                if st.button("Next ➡️"):
                    st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
            
            # Display page number
            st.write(f"**Page {st.session_state.current_page + 1} of {total_pages}**")
            
            # Display the PDF image
            if st.session_state.current_page < len(st.session_state.pdf_images):
                image_data = st.session_state.pdf_images[st.session_state.current_page]
                img = Image.open(BytesIO(image_data))
                st.image(img, use_column_width=True)
        else:
            st.info("📄 PDF preview will appear here after upload")


else:
    # Welcome message using native Streamlit components (auto dark mode)
    st.info("### 👋 Welcome to AI Study Assistant!\nYour personal AI tutor for course PDFs. Get instant, detailed explanations from any document.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚀 Quick Start")
        st.markdown("""
1️⃣ **Upload PDF** - Use the sidebar to select your course material
2️⃣ **Process Document** - Click "Process PDF" to index the content
3️⃣ **Ask Questions** - Type any question about your course
4️⃣ **Get Answers** - Instant, detailed explanations with sources
        """)
    
    with col2:
        st.markdown("### ⭐ Key Features")
        st.markdown("""
- 📚 **Unlimited Questions** - Ask anything about your PDF
- 🧠 **Source Citation** - See exactly which part answered your question
- 🎓 **Smart Explanations** - Tutor-style responses made easy to understand
- ⚡ **Powered by Groq** - Fast, free AI (14.4k daily requests)
- 🔍 **PDF Preview** - Navigate pages side-by-side while asking
        """)

# Footer
st.markdown("---")
st.markdown("💡 Powered by Groq LLM + RAG Architecture  \n🎓 AI Study Assistant v1.0 | Made for students, by AI")
