# 🎨 Architecture & Flow Diagrams

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (app.py)                        │
│  [Upload PDF] → [Process] → [Ask Question] → [Show Answer]     │
└────────────┬─────────────────────────────────────────────┬──────┘
             │                                               │
             ▼                                               ▼
    ┌──────────────────────┐                  ┌─────────────────────┐
    │  PDF PROCESSOR       │                  │   RAG PIPELINE      │
    │  (pdf_processor.py)  │                  │  (rag_pipeline.py)  │
    │                      │                  │                     │
    │ 1. Extract text      │                  │ 1. Get query embed  │
    │ 2. Create chunks     │ ─────chunks────► │ 2. Similarity search│
    │ 3. Save to disk      │                  │ 3. Retrieve top-K   │
    └──────────────────────┘                  │ 4. Generate answer  │
                                              │ 5. Return result    │
                                              └─────────────────────┘
                                                       │
                                                       ▼
                                              ┌─────────────────────┐
                                              │  OPENAI API         │
                                              │                     │
                                              │ • Embeddings        │
                                              │ • GPT-3.5-turbo     │
                                              └─────────────────────┘
```

---

## Data Flow: PDF Upload & Processing

```
User Action: Upload PDF
    │
    ▼
[File saved to disk]
    │
    ▼
pdf_processor.extract_text_from_pdf()
    │
    ├─► PyPDF2.PdfReader()
    │
    ├─► Extract text from each page
    │
    ▼
[Raw text: 50,000+ characters]
    │
    ▼
pdf_processor.chunk_text()
    │
    ├─► Split: 500 chars, 100 char overlap
    │
    ▼
[100+ chunks, each ~500 chars]
    │
    ▼
rag_pipeline.ingest_documents()
    │
    ├─► For each chunk:
    │   ├─► Send to OpenAI embedding API
    │   ├─► Receive 1536-dim vector
    │   └─► Store in memory
    │
    ▼
[Embeddings stored: [[0.1, 0.2, ...], [0.3, 0.1, ...], ...]]
    │
    ▼
✅ Ready for questions!
```

---

## Data Flow: Question Answering (RAG)

```
User Input: "Explain photosynthesis"
    │
    ▼
[Get query embedding]
    │
    ├─► Send "Explain photosynthesis" to OpenAI
    │
    ▼
query_embedding = [0.12, 0.34, 0.21, ..., 0.05]  (1536 dimensions)
    │
    ▼
[Calculate cosine similarity with all chunks]
    │
    ├─► similarity(query, chunk1) = 0.87 ✅ HIGH
    │
    ├─► similarity(query, chunk2) = 0.75 ✅ MEDIUM
    │
    ├─► similarity(query, chunk3) = 0.23 ❌ LOW
    │
    └─► ... (calculate for all chunks)
    │
    ▼
[Sort by similarity, take top 3]
    │
    ├─► Best chunks:
    │   1. "Photosynthesis is the process..." (0.87)
    │   2. "Plants use sunlight to convert..." (0.75)
    │   3. "The chloroplasts contain..." (0.72)
    │
    ▼
[Build context + prompt]
    │
    ├─► System prompt: "You are a helpful AI tutor..."
    │
    ├─► Context: "Photosynthesis is the process..."
    │
    ├─► User question: "Explain photosynthesis"
    │
    ▼
[Send to GPT-3.5-turbo]
    │
    ▼
[Generate answer using ONLY provided context]
    │
    ▼
Answer: "Photosynthesis is how plants make food. Here's how it works:
1. Plants absorb sunlight through leaves
2. Inside chloroplasts, light energy converts CO2 to glucose
3. This glucose fuels plant growth
Example: A green leaf turns sunlight into energy!"
    │
    ▼
[Return with source chunks & scores]
    │
    ▼
Display in Streamlit UI
```

---

## Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                       STREAMLIT (app.py)                         │
│  ┌────────────────┐  ┌──────────────────┐  ┌───────────────────┐ │
│  │ Sidebar:       │  │ Main Area:       │  │ Session State:    │ │
│  │ • Upload       │  │ • Question input │  │ • pdf_processor   │ │
│  │ • Process btn  │  │ • Answer display │  │ • rag_pipeline    │ │
│  │ • Settings     │  │ • Source material│  │ • chunks          │ │
│  └────────┬───────┘  └────────┬─────────┘  │ • pdf_loaded      │ │
│           │                   │            └───────────────────┘ │
└───────────┼───────────────────┼────────────────────────────────────┘
            │                   │
            ▼                   ▼
    ┌──────────────────┐  ┌──────────────────┐
    │ pdf_processor.py │  │ rag_pipeline.py  │
    │                  │  │                  │
    │ • extract_text() │  │ • get_embedding()│
    │ • chunk_text()   │  │ • ingest_docs()  │
    │                  │  │ • retrieve()     │
    └────────┬─────────┘  │ • generate()     │
             │            │ • answer_q()     │
             ▼            └────────┬─────────┘
    ┌──────────────────┐           │
    │ File System      │           │
    │ data/uploaded_   │           ▼
    │ pdfs/*.pdf       │    ┌──────────────────┐
    └──────────────────┘    │ OpenAI API       │
                            │                  │
                            │ • Embeddings     │
                            │ • GPT-3.5-turbo  │
                            └──────────────────┘
```

---

## Embedding & Vector Search Visualization

```
Original Chunks (Text)                  Embeddings (Vectors)

"Photosynthesis is a process..."  ──►  [0.12, 0.34, 0.21, ...]
                                        1536 dimensions
"Plants convert light to..."      ──►  [0.11, 0.33, 0.22, ...]
                                        Similar direction = Related!
"Mitochondria is the power..."    ──►  [0.02, 0.15, 0.45, ...]
                                        Different direction = Unrelated

Query Embedding Space (2D visualization):
```
```
       ▲
       │     ★ Query: "Explain photosynthesis"
       │    /│\
       │   / │ \
       │  /  │  \
       │ •1  •2  • ← Chunk embeddings
       │  (0.87) (0.75)
       │
       └──────────────────────►
       
Cosine Similarity Formula:
  similarity = cos(angle between vectors)
  
  • Angle = 0°    → similarity = 1.0  (identical!)
  • Angle = 90°   → similarity = 0.0  (unrelated)
  • Angle = 180°  → similarity = -1.0 (opposite)
  
This is how we rank relevance!
```

---

## System State Management (Streamlit Session)

```
Before PDF Upload:
┌─────────────────────────────────────┐
│ st.session_state                    │
│ ├── pdf_processor: PDFProcessor()    │
│ ├── rag_pipeline: None              │
│ ├── chunks: None                    │
│ └── pdf_loaded: False               │
└─────────────────────────────────────┘

After PDF Upload & Processing:
┌──────────────────────────────────────────────────┐
│ st.session_state                                 │
│ ├── pdf_processor: PDFProcessor()                │
│ ├── rag_pipeline: RAGPipeline()                  │
│ │   ├── chunks: [chunk1, chunk2, ...]           │
│ │   └── embeddings: [[0.1, 0.2...], ...]        │
│ ├── chunks: [chunk1, chunk2, ...]               │
│ └── pdf_loaded: True                            │
└──────────────────────────────────────────────────┘

This persists across Streamlit reruns, so:
✅ PDF not reprocessed on every interaction
✅ Embeddings stay in memory
✅ Questions answered instantly
```

---

## Prompt Engineering Flow

```
System Prompt Template:
┌────────────────────────────────────────┐
│ You are a helpful AI tutor             │
│ Answer ONLY from provided context      │
│ Use beginner-friendly language         │
│ Break into step-by-step explanations   │
│ Provide examples when helpful          │
│ Admit when information isn't available │
└────────────────────────────────────────┘
         │
         ▼
User Input + Context Assembly:
┌───────────────────────────────────────────────────┐
│ System: [tutoring instructions]                   │
│                                                   │
│ Context from PDF:                                 │
│ ───────────────────                              │
│ "Photosynthesis is a process where plants...     │
│  It occurs in chloroplasts...                    │
│  Light energy is converted to chemical energy..." │
│                                                   │
│ User Question:                                    │
│ ─────────────                                     │
│ "Explain photosynthesis for a beginner"          │
└───────────────────────────────────────────────────┘
         │
         ▼
GPT-3.5-turbo Generation:
┌───────────────────────────────────────────────────┐
│ Response: "Photosynthesis is how plants make food │
│ Here's how it works:                              │
│ 1. Plants absorb sunlight through leaves          │
│ 2. Inside chloroplasts, light energy is converted │
│    to glucose (a type of sugar)                   │
│ 3. This glucose gives plants energy to grow       │
│                                                   │
│ Think of it like a solar panel that plants use    │
│ to turn sunshine into food!"                      │
└───────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
User Action
    │
    ▼
Try Block:
    ├─► Extract PDF
    │   ├─► Success → Continue
    │   └─► Failure → Catch exception
    │
    ├─► Get embeddings
    │   ├─► Success → Continue
    │   └─► Failure (API error, rate limit) → Retry logic
    │
    ├─► Search & Generate
    │   ├─► Success → Show answer
    │   └─► Failure → Show error to user

Error Messaging:
    "❌ Error processing PDF: [specific error]"
    "⚠️ OpenAI API error: [error details]"
    "ℹ️ No API key set. Get one at [link]"
    
All errors logged for debugging
```

---

## Performance Timeline

```
User uploads PDF (10 pages, ~50KB)
│
├─► 0.0s - File saved ✅
│
├─► 0.5s - PDF extraction ✅
│        (PyPDF2 reads all pages)
│
├─► 3-5s - Text chunking ✅
│        (Split into 50+ chunks)
│
├─► 60-90s - Embedding creation ⏳
│         (50 API calls for 50 chunks)
│         Rate-limited: ~50-60 calls/min
│
├─► 0.1s - Embeddings stored ✅
│
└─► Ready for questions! 🎉
    
First Question:
├─► 0.1s - Query embedding ⚡
├─► 0.1s - Similarity search ⚡
├─► 3-5s - LLM generation ⏳
│
└─► Answer displayed! ✨

Total initial: ~2 minutes
Per question: ~3-5 seconds
```

---

## Scaling Considerations

```
Current (Single PDF in Memory):
├─ Max PDF size: Limited by memory (~500 MB)
├─ Max chunks: ~100,000
├─ Storage: RAM only
├─ Scalability: Single user
└─ Cost: $0.10-1.00 per user session

Production (Multiple Users):
├─ Vector Database: Pinecone/Weaviate
├─ Multi-user sessions: Redis for state
├─ Load balancing: Multiple app instances
├─ Caching: Redis for frequent questions
├─ Async: Background embedding jobs
└─ Cost: ~$0.01 per query (infrastructure)
```

---

**These diagrams help explain your system to interviewers! Print or reference during prep.**
