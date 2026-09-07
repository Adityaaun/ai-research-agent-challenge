import re
from typing import List, Dict, Any
from pypdf import PdfReader
from io import BytesIO

MAX_CHUNK_WORDS = 220

def chunk_text_with_metadata(text: str, page_num: int = None, max_words: int = MAX_CHUNK_WORDS) -> List[Dict[str, Any]]:
    """Split text into chunks, preserving paragraph boundaries and adding page numbers."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = []
    current_words = 0
    
    for paragraph in paragraphs:
        words = paragraph.split()
        if len(words) > max_words:
            if current:
                chunks.append({"text": " ".join(current), "page": page_num})
                current, current_words = [], 0
            for start in range(0, len(words), max_words):
                chunks.append({"text": " ".join(words[start : start + max_words]), "page": page_num})
            continue
            
        if current and current_words + len(words) > max_words:
            chunks.append({"text": " ".join(current), "page": page_num})
            current, current_words = [], 0
            
        current.append(paragraph)
        current_words += len(words)
        
    if current:
        chunks.append({"text": " ".join(current), "page": page_num})
        
    return chunks

def parse_txt(content: bytes) -> List[Dict[str, Any]]:
    """Parse TXT files."""
    text = content.decode("utf-8")
    return chunk_text_with_metadata(text, page_num=1)

def parse_pdf(content: bytes) -> List[Dict[str, Any]]:
    """Parse PDF files and extract page numbers."""
    reader = PdfReader(BytesIO(content))
    chunks = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            # page numbering is 1-indexed for citations
            chunks.extend(chunk_text_with_metadata(text, page_num=i + 1))
    return chunks

def parse_document(filename: str, content: bytes) -> List[Dict[str, Any]]:
    """Route document to appropriate parser based on extension."""
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return parse_pdf(content)
    elif filename.endswith(".txt") or filename.endswith(".md") or filename.endswith(".csv"):
        return parse_txt(content)
    else:
        raise ValueError(f"Unsupported file format: {filename}")
