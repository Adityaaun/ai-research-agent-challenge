# RESEARCHOS: Evidence-First AI Research Intelligence Platform

RESEARCHOS is a premium, portfolio-level RAG (Retrieval-Augmented Generation) application designed to prevent LLM hallucinations by prioritizing evidence, citations, and algorithmic confidence scoring. 

Unlike generic ChatGPT clones, RESEARCHOS forces the AI (Gemini) to cite its sources down to the exact chunk and page number, dynamically extracting and cross-referencing factual claims against a hybrid knowledge base.

## 🚀 Features

# RESEARCHOS - Evidence-First AI Research Agent

RESEARCHOS is a production-grade, full-stack AI research agent designed to perform deep, grounded research over custom knowledge bases. It explicitly avoids hallucination by enforcing an "evidence-first" pipeline: retrieving, verifying, and citing sources before generating any final report.

## Architecture & Core Features

*   **Hybrid RAG Pipeline**: Combines dense vector search (ChromaDB + Gemini Embeddings) with sparse lexical search (BM25) to maximize recall across both semantic concepts and exact keywords.
*   **Reciprocal Rank Fusion (RRF)**: Merges vector and lexical results algorithmically without requiring score normalization.
*   **CrossEncoder Reranking**: Re-evaluates top hybrid candidates using a lightweight cross-encoder model (`ms-marco-MiniLM-L-6-v2`) to ensure absolute semantic relevance before passing context to the LLM.
*   **Multi-Agent Claim Verification**: 
    1. An Extraction Agent extracts factual claims from retrieved evidence.
    2. A Verification Agent cross-references each claim against *all* retrieved passages, labeling relationships as `SUPPORT`, `CONTRADICT`, or `NEUTRAL`.
*   **Heuristic Confidence Scoring**: Algorithmically scores claims based on the volume of independent supporting sources, CrossEncoder relevance scores, and heavily penalizes for any contradicting evidence found.
*   **Server-Sent Events (SSE)**: Streams real-time pipeline progress (Retrieval -> Extraction -> Verification -> Synthesis) directly to the React frontend.
*   **Interactive React Flow Graph**: Visualizes the relationships between the generated report, the verified claims, and the source documents.

## Tech Stack
*   **Backend**: Python, FastAPI, SQLAlchemy, SQLite, ChromaDB, Sentence-Transformers, Google Gemini API
*   **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion, React Flow

## Quickstart

### 1. Backend Setup
```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # Or venv/bin/activate on Linux/Mac
pip install -r requirements.txt
pip install sentence-transformers torch
```

Set your API key in `backend/.env`:
```
GEMINI_API_KEY=your_key_here
```

Run the backend:
```bash
uvicorn backend.app.main:app --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

## Running Evaluations
To run the automated retrieval evaluation (Recall@5):
```bash
cd backend
python -m scripts.evaluate_retrieval
```

To run unit tests:
```bash
cd backend
pytest tests/
```

## 🗺️ Roadmap
- [ ] Add Multi-Agent debate for contradictory evidence.
- [ ] Add Web-scraping capabilities to ingest URLs alongside static files.
- [ ] Introduce User Authentication & Team Workspaces.

---
*Built as a premium AI/ML Engineering Portfolio Project.*
