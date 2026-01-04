"""
PDF Processing Module
Handles PDF extraction, text processing, and chunking
"""

import os
import PyPDF2
from typing import List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Processes PDF files and extracts text with chunking"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 100):
        """
        Initialize PDF Processor
        
        Args:
            chunk_size: Number of characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text from the PDF
        """
        try:
            text = ""
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                num_pages = len(pdf_reader.pages)
                logger.info(f"Extracting text from {num_pages} pages")
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    text += page.extract_text()
                    text += "\n"
            
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
        
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Raw text to chunk
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk.strip())
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def process_pdf(self, pdf_path: str) -> List[str]:
        """
        Complete pipeline: extract and chunk text
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of text chunks
        """
        text = self.extract_text_from_pdf(pdf_path)
        chunks = self.chunk_text(text)
        return chunks
    
    def save_processed_pdf(self, pdf_path: str, output_dir: str = "data/uploaded_pdfs") -> str:
        """
        Save uploaded PDF to storage
        
        Args:
            pdf_path: Path to source PDF
            output_dir: Directory to save the PDF
            
        Returns:
            Path to saved PDF
        """
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(pdf_path)
        output_path = os.path.join(output_dir, filename)
        
        with open(pdf_path, 'rb') as src:
            with open(output_path, 'wb') as dst:
                dst.write(src.read())
        
        logger.info(f"PDF saved to {output_path}")
        return output_path
