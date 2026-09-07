# RESEARCHOS: Evidence-First AI Research Intelligence Platform

RESEARCHOS is a premium, portfolio-level RAG (Retrieval-Augmented Generation) application designed to prevent LLM hallucinations by prioritizing evidence, citations, and algorithmic confidence scoring. 

Unlike generic ChatGPT clones, RESEARCHOS forces the AI (Gemini) to cite its sources down to the exact chunk and page number, dynamically extracting and cross-referencing factual claims against a hybrid knowledge base.

## 🚀 Features

*   **Drag-and-Drop Ingestion:** Effortlessly upload `.pdf` and `.txt` files via a sleek, dark-mode React frontend.
*   **Hybrid Retrieval Engine:** Combines semantic Vector Search (ChromaDB) with lexical keyword matching (BM25) using Reciprocal Rank Fusion (RRF) for unparalleled accuracy.
*   **Deep Research Orchestration:** Complex user queries are dynamically decomposed into sub-questions. Progress is streamed in real-time to the UI via Server-Sent Events (SSE).
*   **Algorithmic Claim Engine:** Rather than blindly summarizing, the agent extracts discrete, structured factual claims, algorithmically scoring their confidence based on source density and direct contradictions.
*   **Interactive Evidence Graph:** Powered by React Flow, a stunning nodal graph visually connects your original question to the generated claims and draws Support/Contradict edges directly to the raw source documents.
*   **Persistent Research Memory:** Powered by PostgreSQL and SQLAlchemy, every deep dive, extracted claim, and piece of evidence is permanently saved for later review.
*   **Exportable Briefs:** One-click Markdown export of structured, authoritative research reports (Executive Summary, Findings, Limitations).

## 🛠️ Architecture

*   **Frontend:** React, Vite, TypeScript, Tailwind CSS, shadcn/ui, React Flow, lucide-react.
*   **Backend:** Python 3, FastAPI, SQLAlchemy, PostgreSQL.
*   **AI/ML:** Google Gemini API, ChromaDB (Persistent Vector Store), rank-bm25, sentence-transformers.

## ⚙️ How to Run Locally

### 1. Database Setup
Ensure you have PostgreSQL running. The backend defaults to using a local sqlite database if PostgreSQL is not configured, but for production, set up the `DATABASE_URL` appropriately.

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

# Export your Gemini API key
export GEMINI_API_KEY="your-api-key-here"

# Run the FastAPI server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Navigate to `http://localhost:5173` to experience RESEARCHOS.

## 🗺️ Roadmap
- [ ] Add Multi-Agent debate for contradictory evidence.
- [ ] Add Web-scraping capabilities to ingest URLs alongside static files.
- [ ] Introduce User Authentication & Team Workspaces.

---
*Built as a premium AI/ML Engineering Portfolio Project.*
