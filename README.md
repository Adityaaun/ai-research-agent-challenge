# Veritas RAG — Evidence-Grounded AI Research Agent

Veritas RAG is a full-stack AI research agent that performs deep, evidence-grounded research over custom knowledge bases. It enforces an "evidence-first" pipeline: retrieving, verifying, and citing sources before generating any final report, which provides traceable evidence and reduces unsupported generation.

## Architecture

```
Upload PDF/TXT or Ingest Web URL → Parse & Chunk → Store Metadata (SQLite) → Embed & Index (ChromaDB)
                                                                            ↓
User Question → Decompose → Vector Search ──┐
                            BM25 Search ────┤→ RRF Fusion → CrossEncoder Rerank
                                            ↓
                        Claim Extraction → Verification (SUPPORT/CONTRADICT/NEUTRAL)
                                            ↓
                        Confidence Scoring → Report Generation → SSE Stream → React UI
```

### Retrieval Pipeline
1. **Hybrid RAG**: Dense vector search (ChromaDB) + sparse lexical search (BM25).
2. **Reciprocal Rank Fusion (RRF)**: Merges results without score normalization.
3. **CrossEncoder Reranking**: Re-evaluates candidates using `ms-marco-MiniLM-L-6-v2`.

### Claim Verification
1. **Extraction Agent**: Extracts factual claims from retrieved evidence.
2. **Verification Agent**: Cross-references each claim against all passages, labeling as `SUPPORT`, `CONTRADICT`, or `NEUTRAL`.
3. **Confidence Scoring**: Heuristic algorithm based on support count, reranker relevance scores, and contradiction penalties.

## Features
- **ChatGPT-Style Workspaces**: Seamlessly switch between different research chats. Each workspace acts as an isolated knowledge base.
- **Dynamic Chat Naming**: Chats automatically rename themselves based on the first question asked using an intelligent fallback splitting strategy.
- **Isolated Document Contexts**: Documents uploaded to Chat A do not pollute the retrieval context of Chat B.
- **Collapsible Sidebar UI**: Sleek, responsive React sidebar that toggles off-screen to maximize reading space for complex research reports.
- **Deep Web Ingestion**: Securely scrape public URLs (with SSRF protection against internal/private IPs) to expand your knowledge base on the fly.
- **Evidence Graph visualization**: A node-based interactive graph (via React Flow) linking generated claims directly to their source text chunks.

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy, SQLite, ChromaDB, Sentence-Transformers, Google Gemini API
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Framer Motion, React Flow

## Quickstart

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install sentence-transformers torch
```

Create `backend/.env`:
```
GEMINI_API_KEY=your_key_here
```

Run:
```bash
cd ..  # from repo root
uvicorn backend.app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Testing

```bash
# From repo root
PYTHONPATH=. pytest backend/tests/ -v
```

Test coverage includes:
- Retrieval: RRF fusion, BM25 cache invalidation, empty results
- Claims: extraction, verification (SUPPORT/CONTRADICT/NEUTRAL), confidence scoring
- Pipeline: insufficient evidence, LLM failure, malformed responses
- Citations: valid/invalid/missing citation detection

## Evaluation

```bash
cd backend
python -m scripts.evaluate_retrieval
```

Evaluates four retrieval configurations: Vector-only, BM25-only, Hybrid RRF, and Hybrid+Reranker. Reports Recall@5, Precision@5, and MRR. Results saved to `retrieval_evaluation.json`.

## Limitations

- **No hallucination guarantee**: The system reduces but cannot fully eliminate LLM hallucination. Claims are verified against retrieved evidence, but verification itself uses an LLM.
- **Web Ingestion Scope**: The URL parser uses BeautifulSoup for static HTML. It does not execute JavaScript or support dynamic SPAs. Private network isolation prevents SSRF, but scraping is limited to text-heavy public sites.
- **Evaluation scale**: The curated eval dataset is small. Production systems require larger, domain-specific benchmarks.
- **Single-model dependency**: All LLM calls go to Gemini. API failures will cascade.
- **No authentication**: This is a portfolio project, not a multi-tenant production service.

---
*Built as an AI/ML Engineering portfolio project demonstrating RAG, hybrid retrieval, cross-encoder reranking, and multi-agent claim verification.*
