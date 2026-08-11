from __future__ import annotations

import argparse
import glob
import hashlib
import os
import re
from pathlib import Path
from typing import Any

import chromadb
from dotenv import load_dotenv
from google import genai

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = PROJECT_ROOT / "chroma_db"
COLLECTION_NAME = "research_docs"
MODEL_NAME = "gemini-3.5-flash"
MAX_RESULTS = 4
MAX_CHUNK_WORDS = 220
REFUSAL = "The provided sources do not contain the answer to this question."

load_dotenv(PROJECT_ROOT / ".env")

# Chroma uses its local default embedding function (all-MiniLM-L6-v2).
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)


def get_gemini_client() -> genai.Client:
    """Create the Gemini client only when an answer is requested."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise ValueError(
            "Valid GEMINI_API_KEY not found. Copy .env.example to .env and add your API key."
        )
    return genai.Client(api_key=api_key)


def chunk_text(text: str, max_words: int = MAX_CHUNK_WORDS) -> list[str]:
    """Split source text into small passages while preserving paragraph boundaries."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) > max_words:
            if current:
                chunks.append(" ".join(current))
                current = []
                current_words = 0
            for start in range(0, len(words), max_words):
                chunks.append(" ".join(words[start : start + max_words]))
            continue

        if current and current_words + len(words) > max_words:
            chunks.append(" ".join(current))
            current = []
            current_words = 0

        current.append(paragraph)
        current_words += len(words)

    if current:
        chunks.append(" ".join(current))

    return chunks


def _stable_id(filename: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{filename}:{chunk_index}".encode()).hexdigest()[:16]
    return f"doc_{digest}"


def load_documents(data_dir: str | Path = DATA_DIR):
    """Load .txt sources into Chroma using passage-level chunks."""
    global collection
    data_path = Path(data_dir)
    file_paths = sorted(glob.glob(str(data_path / "*.txt")))

    if not file_paths:
        raise FileNotFoundError(f"No .txt source documents found in {data_path}")

    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except ValueError:
        pass
    collection = chroma_client.create_collection(name=COLLECTION_NAME)

    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []
    ids: list[str] = []

    for file_path in file_paths:
        path = Path(file_path)
        content = path.read_text(encoding="utf-8").strip()
        for chunk_index, chunk in enumerate(chunk_text(content)):
            documents.append(chunk)
            metadatas.append({"source": path.name, "chunk_index": chunk_index})
            ids.append(_stable_id(path.name, chunk_index))

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Loaded {len(documents)} passages from {len(file_paths)} source files.")
    return collection


def retrieve(query: str, n_results: int = MAX_RESULTS) -> list[dict[str, Any]]:
    """Retrieve the most relevant source passages for a question."""
    if collection.count() == 0:
        raise RuntimeError("No documents are indexed. Run load_documents() first.")

    result = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    return [
        {"document": document, "metadata": metadata or {}, "distance": distance}
        for document, metadata, distance in zip(documents, metadatas, distances)
    ]


def build_context(retrieved: list[dict[str, Any]]) -> str:
    """Format retrieved passages with explicit source boundaries."""
    sections: list[str] = []
    for index, item in enumerate(retrieved, start=1):
        source = item["metadata"].get("source", "unknown")
        chunk_index = item["metadata"].get("chunk_index", 0)
        sections.append(
            f"--- SOURCE_{index} | {source} | passage {chunk_index} ---\n"
            f"{item['document']}\n"
            f"--- END SOURCE_{index} ---"
        )
    return "\n\n".join(sections)


def validate_citations(answer: str, retrieved: list[dict[str, Any]]) -> bool:
    """Ensure an answer has citations and every cited filename was retrieved."""
    cited_files = set(re.findall(r"\[Source:\s*([^\]]+)\]", answer))
    valid_files = {
        item["metadata"].get("source")
        for item in retrieved
        if item["metadata"].get("source")
    }
    return bool(cited_files) and cited_files.issubset(valid_files)


def ask_agent(query: str) -> str:
    """Retrieve source passages and synthesize a cited answer using Gemini."""
    retrieved = retrieve(query)
    context = build_context(retrieved)

    prompt = f"""You are a strict research assistant.
Answer the user's question using ONLY the source passages below.

Rules:
1. Do not use outside knowledge or assumptions.
2. If the sources do not contain enough information to answer the question, reply EXACTLY:
{REFUSAL}
3. Every factual claim must end with a citation in this exact format: [Source: filename.txt]
4. Only cite filenames that appear in the provided source passages.
5. Do not invent source names, facts, dates, or details.
6. Keep the answer concise and directly answer the question.

SOURCE PASSAGES:
{context}

USER QUESTION: {query}
"""

    response = get_gemini_client().models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )
    answer = (response.text or "").strip()

    if not answer:
        raise RuntimeError("Gemini returned an empty response.")

    if answer == REFUSAL:
        return answer

    if not validate_citations(answer, retrieved):
        raise RuntimeError(
            "Gemini returned an answer without valid citations from the retrieved sources."
        )

    return answer


def run_demo() -> None:
    """Run the three challenge questions."""
    questions = [
        "What is the fundamental unit of information in a quantum computer, and what special state allows it to perform simultaneous calculations?",
        "Which rover is currently searching for signs of ancient life on Mars, and where did it land?",
        "When did the Apollo 11 mission land on the moon?",
    ]

    print("\n" + "=" * 70)
    print("Research Agent (with Citations)")
    print("=" * 70)
    for question in questions:
        print(f"\n[Question] {question}")
        print("[Answer]")
        print(ask_agent(question))
        print("-" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Agent with source citations")
    parser.add_argument(
        "--question",
        help="Ask a custom question using only the supplied source documents.",
    )
    parser.add_argument(
        "--data-dir",
        default=str(DATA_DIR),
        help="Directory containing the .txt source documents (default: data).",
    )
    args = parser.parse_args()

    load_documents(args.data_dir)
    if args.question:
        print(ask_agent(args.question))
    else:
        run_demo()


if __name__ == "__main__":
    main()
