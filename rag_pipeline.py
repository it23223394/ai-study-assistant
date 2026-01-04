"""
RAG (Retrieval-Augmented Generation) Pipeline
Handles embeddings, vector store, and retrieval
"""

import os
import logging
from typing import List, Tuple, Optional
import numpy as np
from groq import Groq
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGPipeline:
    """Handles retrieval and augmented generation with LLM"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.3-70b-versatile"):
        """
        Initialize RAG Pipeline with Groq (Free!)
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: LLM model to use (default: llama-3.3-70b-versatile)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.client = Groq(api_key=self.api_key)
        
        # Use local embeddings (free, no API needed!)
        logger.info("Loading local embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
        
        self.chunks = []
        self.embeddings = []
        
        if not self.api_key:
            logger.warning("GROQ_API_KEY not set. LLM generation may fail.")
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using local model (FREE!)
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Use local sentence-transformers (no API cost!)
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error getting embedding: {str(e)}")
            raise
    
    def ingest_documents(self, chunks: List[str]) -> None:
        """
        Ingest document chunks and create embeddings
        
        Args:
            chunks: List of text chunks to ingest
        """
        self.chunks = chunks
        self.embeddings = []
        
        logger.info(f"Creating embeddings for {len(chunks)} chunks...")
        for i, chunk in enumerate(chunks):
            try:
                embedding = self.get_embedding(chunk)
                self.embeddings.append(embedding)
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed {i + 1}/{len(chunks)} chunks")
            
            except Exception as e:
                logger.error(f"Error embedding chunk {i}: {str(e)}")
                raise
        
        logger.info(f"Successfully created {len(self.embeddings)} embeddings")
    
    def retrieve_relevant_chunks(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """
        Retrieve most relevant chunks for a query
        
        Args:
            query: User query
            top_k: Number of top chunks to retrieve
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if not self.embeddings:
            logger.error("No embeddings available. Ingest documents first.")
            return []
        
        # Get query embedding
        query_embedding = self.get_embedding(query)
        query_embedding = np.array(query_embedding).reshape(1, -1)
        
        # Calculate similarities
        embeddings_array = np.array(self.embeddings)
        similarities = cosine_similarity(query_embedding, embeddings_array)[0]
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Return chunks with scores
        results = [
            (self.chunks[idx], float(similarities[idx]))
            for idx in top_indices
        ]
        
        logger.info(f"Retrieved {len(results)} relevant chunks")
        return results
    
    def generate_answer(self, query: str, context_chunks: List[str], system_prompt: str) -> str:
        """
        Generate answer using LLM with context
        
        Args:
            query: User queryGroq LLM (FREE!)
        
        Args:
            query: User query
            context_chunks: Relevant chunks from retrieval
            system_prompt: System prompt for the AI
            
        Returns:
            Generated answer
        """
        # Combine context
        context = "\n\n".join(context_chunks)
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": f"Context from the PDF:\n\n{context}\n\nQuestion: {query}"
            }
        ]
        
        try:
            # Using Groq's free API (14,400 requests/day!)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.info("Successfully generated answer with Groq")
            return answer
        
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            raise
    
    def answer_question(self, query: str, system_prompt: str, top_k: int = 3) -> Tuple[str, List[Tuple[str, float]]]:
        """
        Complete RAG pipeline: retrieve and generate
        
        Args:
            query: User query
            system_prompt: System prompt for the AI
            top_k: Number of chunks to retrieve
            
        Returns:
            Tuple of (answer, retrieved_chunks_with_scores)
        """
        # Retrieve relevant chunks
        retrieved = self.retrieve_relevant_chunks(query, top_k)
        
        if not retrieved:
            return "I couldn't find relevant information in the PDF.", []
        
        context_chunks = [chunk for chunk, _ in retrieved]
        
        # Generate answer
        answer = self.generate_answer(query, context_chunks, system_prompt)
        
        return answer, retrieved
