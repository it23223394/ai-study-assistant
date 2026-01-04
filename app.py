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

# Custom CSS for better UI
st.markdown("""
    <style>
    /* Header styling */
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 6px;
        margin-bottom: 15px;
        font-size: 1.2em;
        font-weight: 600;
    }
    
    /* Card styling - light mode */
    .info-card {
        background-color: #f0f4ff !important;
        border-left: 4px solid #667eea;
        padding: 15px;
        border-radius: 6px;
        margin: 10px 0;
        color: #1a1a1a !important;
    }
    
    .info-card * {
        color: #1a1a1a !important;
    }
    
    /* Dark mode card */
    @media (prefers-color-scheme: dark) {
        .info-card {
            background-color: #2d2d44 !important;
            border-left: 4px solid #667eea;
            color: #e0e0e0 !important;
        }
        .info-card * {
            color: #e0e0e0 !important;
        }
    }
    
    /* Step-by-step guide */
    .steps-guide {
        background-color: #f9f9f9 !important;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        color: #1a1a1a !important;
    }
    
    .steps-guide * {
        color: #1a1a1a !important;
    }
    
    @media (prefers-color-scheme: dark) {
        .steps-guide {
            background-color: #1e1e2e !important;
            border: 1px solid #3d3d5c;
            color: #e0e0e0 !important;
        }
        .steps-guide * {
            color: #e0e0e0 !important;
        }
    }
    
    .step {
        margin: 12px 0;
        padding: 10px;
        background: white !important;
        border-radius: 4px;
        border-left: 3px solid #667eea;
        color: #1a1a1a !important;
    }
    
    .step * {
        color: #1a1a1a !important;
    }
    
    @media (prefers-color-scheme: dark) {
        .step {
            background: #262637 !important;
            color: #e0e0e0 !important;
            border-left: 3px solid #667eea;
        }
        .step * {
            color: #e0e0e0 !important;
        }
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        color: #666;
        font-size: 13px;
        padding: 20px 0;
        border-top: 1px solid #e0e0e0;
        margin-top: 30px;
    }
    
    @media (prefers-color-scheme: dark) {
        .footer {
            color: #999;
            border-top: 1px solid #3d3d5c;
        }
    }
    
    /* Button styling improvements */
    [data-testid="stButton"] {
        width: 100%;
    }
    
    /* Question area */
    .question-area {
        background-color: #f8faff;
        border: 1px solid #e0e8ff;
        border-radius: 8px;
        padding: 15px;
    }
    
    @media (prefers-color-scheme: dark) {
        .question-area {
            background-color: #1e1e2e;
            border: 1px solid #3d3d5c;
        }
    }
    
    /* Answer area */
    .answer-area {
        background-color: #fffaf0 !important;
        border-left: 4px solid #ff9800;
        padding: 15px;
        border-radius: 4px;
        margin-top: 15px;
        color: #1a1a1a !important;
    }
    
    .answer-area * {
        color: #1a1a1a !important;
    }
    
    @media (prefers-color-scheme: dark) {
        .answer-area {
            background-color: #2d2620 !important;
            border-left: 4px solid #ff9800;
            color: #e0e0e0 !important;
        }
        .answer-area * {
            color: #e0e0e0 !important;
        }
    }
    
    /* PDF viewer area */
    .pdf-viewer {
        border: 2px solid #667eea;
        border-radius: 8px;
        padding: 10px;
        background-color: #f9f9f9;
    }
    
    @media (prefers-color-scheme: dark) {
        .pdf-viewer {
            border: 2px solid #667eea;
            background-color: #1e1e2e;
        }
    }
    </style>
""", unsafe_allow_html=True)

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
st.markdown('<div class="main-header">📚 AI Study Assistant</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 18px; color: #666; margin-bottom: 20px;">Your Personal AI Tutor for Course PDFs</p>', unsafe_allow_html=True)

# Sidebar for PDF upload
with st.sidebar:
    st.markdown('<div class="section-header">📤 Upload & Process PDF</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="info-card">👉 Select your PDF file below:</div>', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "Choose a PDF file",
        type="pdf",
        help="Upload your course notes, lecture slides, or textbook PDF",
        label_visibility="collapsed"
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
        st.error("⚠️ **API Key Required** - Get your FREE Groq API key at https://console.groq.com and add it to .env")

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
                    st.markdown('<div class="section-header">✨ Answer</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="answer-area">{answer}</div>', unsafe_allow_html=True)
                    
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
        st.markdown('<div class="section-header">📄 PDF Document</div>', unsafe_allow_html=True)
        
        if st.session_state.pdf_images:
            # Page navigation
            total_pages = len(st.session_state.pdf_images)
            
            col_nav1, col_nav2, col_nav3 = st.columns([0.8, 1.4, 0.8], gap="small")
            
            with col_nav1:
                if st.button("⬅️ Prev", use_container_width=True, help="Previous page"):
                    st.session_state.current_page = max(0, st.session_state.current_page - 1)
            
            with col_nav2:
                col_a, col_b = st.columns([1, 1])
                with col_a:
                    page_num = st.number_input(
                        "Go to page:",
                        min_value=1,
                        max_value=total_pages,
                        value=st.session_state.current_page + 1,
                        label_visibility="collapsed"
                    )
                    st.session_state.current_page = page_num - 1
                with col_b:
                    st.markdown(f"<div style='text-align:center; padding:8px; background:#f0f0f0; border-radius:4px;'><b>{st.session_state.current_page + 1}/{total_pages}</b></div>", unsafe_allow_html=True)
            
            with col_nav3:
                if st.button("Next ➡️", use_container_width=True, help="Next page"):
                    st.session_state.current_page = min(total_pages - 1, st.session_state.current_page + 1)
            
            # Display current page
            from PIL import Image
            from io import BytesIO
            image_data = st.session_state.pdf_images[st.session_state.current_page]
            img = Image.open(BytesIO(image_data))
            st.markdown('<div class="pdf-viewer">', unsafe_allow_html=True)
            st.image(
                img,
                use_column_width=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📄 PDF preview will appear here after upload")


else:
    # Welcome message
    st.markdown('<div class="info-card" style="font-size: 16px;">', unsafe_allow_html=True)
    st.markdown("## 👋 Welcome to AI Study Assistant!")
    st.markdown("""Your personal AI tutor for course PDFs. Get instant, detailed explanations from any document.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="steps-guide">', unsafe_allow_html=True)
        st.markdown("### 🚀 Quick Start")
        st.markdown("""
        <div class="step"><b>1️⃣ Upload PDF</b><br>Use the sidebar to select your course material</div>
        <div class="step"><b>2️⃣ Process Document</b><br>Click "Process PDF" to index the content</div>
        <div class="step"><b>3️⃣ Ask Questions</b><br>Type any question about your course</div>
        <div class="step"><b>4️⃣ Get Answers</b><br>Instant, detailed explanations with sources</div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="steps-guide">', unsafe_allow_html=True)
        st.markdown("### ⭐ Key Features")
        st.markdown("""
        - 📚 **Unlimited Questions** - Ask anything about your PDF
        - 🧠 **Source Citation** - See exactly which part answered your question
        - 🎓 **Smart Explanations** - Tutor-style responses made easy to understand
        - ⚡ **Powered by Groq** - Fast, free AI (14.4k daily requests)
        - 🔍 **PDF Preview** - Navigate pages side-by-side while asking
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
💡 Powered by Groq LLM + RAG Architecture<br>
🎓 AI Study Assistant v1.0 | Made for students, by AI
</div>
""", unsafe_allow_html=True)
