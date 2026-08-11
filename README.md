# Research Agent (with Citations)

A small, reproducible Retrieval-Augmented Generation (RAG) research agent built for the ROOMAN AI Challenge. It accepts a question, retrieves relevant passages from the provided source documents, and asks Gemini to synthesize an answer with source citations.

The agent is intentionally simple: local ChromaDB handles semantic retrieval and Gemini handles answer synthesis. It does **not** use outside knowledge when answering from the provided sources.

## 🚀 Features

- **RAG:** Semantic retrieval over the supplied `.txt` source documents.
- **Passage-level retrieval:** Source files are split into small passages before indexing.
- **Grounded citations:** The prompt requires every factual claim to cite a retrieved filename.
- **Citation validation:** Generated filename citations are checked against the sources actually retrieved.
- **Hallucination test:** An out-of-scope question demonstrates the required refusal behavior.
- **Local embeddings:** ChromaDB uses its local default embedding function, so no separate embedding API key is required.
- **Gemini synthesis:** Uses `gemini-3.5-flash` for the final answer.

## 🧱 Architecture

```text
Question
   │
   ▼
ChromaDB semantic retrieval
   │
   ▼
Top relevant source passages
   │
   ▼
Grounded Gemini prompt
   │
   ▼
Cited answer / source-not-found refusal
```

## 🛠️ Setup

### Prerequisites

- Python **3.10+**
- A Google Gemini API key

### Installation

```bash
git clone https://github.com/Adityaaun/ai-research-agent-challenge.git
cd ai-research-agent-challenge

python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Windows Command Prompt:

```cmd
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install the pinned dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configure the API key

Copy `.env.example` to `.env` and replace the placeholder:

```text
GEMINI_API_KEY=your_actual_key_here
```

**Never commit `.env` or a real API key.** `.env` is excluded by `.gitignore`.

## ▶️ Run

From the repository root:

```bash
python src/agent.py
```

The script loads the sample documents, indexes their passages, and runs the three challenge questions in `questions.md`.

## 🧪 Challenge Deliverables

- **Question set:** [`questions.md`](questions.md)
- **Source documents:** [`data/`](data/)
- **Sample cited answers:** [`sample_outputs.md`](sample_outputs.md)
- **Core implementation:** [`src/agent.py`](src/agent.py)
- **Environment template:** [`.env.example`](.env.example)

The three included questions test:

1. Relevant retrieval + citation.
2. Retrieval across a different source + citation.
3. A question not answered by the provided sources, where the agent must refuse rather than use outside knowledge.

## 🔎 Retrieval and Tool Approach

1. Every `.txt` file in `data/` is read as a source document.
2. Each document is split into small passages while preserving paragraph boundaries.
3. ChromaDB creates local embeddings and stores the passages with filename metadata.
4. A user question is embedded and the most relevant passages are retrieved.
5. The retrieved passages are inserted into a strict Gemini prompt with explicit source boundaries.
6. Gemini must answer only from those passages and cite the source filename for factual claims.
7. The application validates that generated filename citations belong to the retrieved sources.

This is deliberately lightweight for a 24-hour challenge. It avoids adding a separate orchestration framework when a small Python pipeline is sufficient.

## ⚖️ Design Tradeoffs and Limitations

- **Why ChromaDB?** It provides a local vector database and local embedding path with minimal application code and no separate embedding API key.
- **Why Gemini?** It provides the synthesis step while the retrieval context constrains the answer to the supplied sources.
- **Why passage chunks?** The original implementation indexed one entire file as one chunk. Passage-level chunks make retrieval more precise while keeping the implementation small.
- **Why filename citations?** They are easy for a reviewer to verify against the supplied source documents. The application also validates that cited filenames were actually retrieved.
- **Current scope:** The loader supports `.txt` files only. PDF extraction, web search, reranking, and conversational memory are intentionally outside the challenge scope.
- **Refusal behavior:** If the retrieved evidence is insufficient, the model is instructed to return the exact source-not-found message. Because this is LLM-based, the project keeps the retrieved context explicit and validates citations to reduce unsupported claims.

## 📌 Reproducibility

Dependencies are pinned in `requirements.txt`. The repository includes sample source documents, questions, expected behavior, and sample outputs so a reviewer can reproduce the demonstration quickly.
