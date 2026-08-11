# Research Agent (with Citations)

This project is a functioning AI Research Agent that takes a question, retrieves relevant context from a set of source documents, and synthesizes a precise answer. Crucially, it forces the AI to **cite its sources** and prevents hallucination by strictly stating when an answer cannot be found in the provided texts.

Built in 24 hours for the ROOMAN AI CHALLENGE.

## 🚀 Features
- **Retrieval-Augmented Generation (RAG):** Uses local semantic search to find relevant information.
- **Strict Citations:** The model is prompted to cite the exact filename for every claim.
- **Hallucination Prevention:** The agent refuses to answer if the context is missing.
- **100% Local Embeddings:** Uses `chromadb` with local sentence-transformers, meaning no API costs for document embedding.
- **Gemini Powered:** Uses the fast and powerful `gemini-1.5-flash` model for synthesis.

## 🛠️ Setup Instructions (Foolproof)

### Prerequisites
- Python 3.9+
- A Google Gemini API Key (Get one for free at [Google AI Studio](https://aistudio.google.com/))

### Installation
1. **Clone the repository** (or download the files).
2. **Create a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment Variables:**
   - Rename `.env.example` to `.env`
   - Open `.env` and add your Gemini API Key:
     ```
     GEMINI_API_KEY=your_actual_key_here
     ```

### Running the Agent
Run the main script to ingest the sample data and answer the predefined test questions:
```bash
python src/agent.py
```
The script will automatically read the `.txt` files in the `data/` folder, embed them into the local vector database, and print out the cited answers in your terminal.

## 📁 Project Structure
- `/data`: Contains the sample source documents (`.txt`).
- `/src/agent.py`: The core agent logic (Document Loader + Vector DB + Gemini integration).
- `requirements.txt`: Pinned dependencies for reproducibility.
- `questions.md`: The test questions used to evaluate the agent.
- `sample_outputs.md`: A transcript of the agent running successfully.

## ⚖️ Tradeoff Notes & Design Choices
- **Why ChromaDB?** I chose Chroma for this 24-hour challenge because it comes with an out-of-the-box local embedding model (`all-MiniLM-L6-v2`). This makes setup foolproof for reviewers (no extra embedding API keys required) and keeps the architecture lightweight.
- **Why Gemini 1.5 Flash?** It is incredibly fast, offers a generous free tier, and follows strict system prompts (like citation rules) very well.
- **Limitations:** Currently, the document loader treats entire `.txt` files as single chunks. This is perfectly fine for short articles, but for large enterprise PDFs, I would implement a recursive character text splitter to maintain context without exceeding token limits. 
- **What I'd do with more time:** Add a beautiful UI using Streamlit, implement PyMuPDF to extract text from complex PDFs, and add conversation history to the prompt so the user can ask follow-up questions.
