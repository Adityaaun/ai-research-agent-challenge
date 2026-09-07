import re
from typing import List, Dict, Any
from pypdf import PdfReader
from io import BytesIO
import httpx
from bs4 import BeautifulSoup

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

import socket
import ipaddress
from urllib.parse import urlparse

def is_safe_url(url_str: str) -> bool:
    try:
        parsed = urlparse(str(url_str))
        if parsed.scheme not in ("http", "https"):
            return False
            
        hostname = parsed.hostname
        if not hostname:
            return False
            
        if hostname.lower() in ("localhost", "127.0.0.1", "0.0.0.0"):
            return False
            
        ip_addr = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(ip_addr)
        
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            return False
            
        return True
    except Exception:
        return False

async def verify_request(request: httpx.Request):
    if not is_safe_url(str(request.url)):
        raise ValueError("URL points to a private or internal network address.")

async def parse_url(url: str) -> Dict[str, Any]:
    """Parse text from a web URL asynchronously."""
    if not is_safe_url(url):
        raise ValueError("URL points to a private or internal network address.")
        
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, event_hooks={'request': [verify_request]}) as client:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        response = await client.get(url, headers=headers)
        response.raise_for_status()
    
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract title
    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
        
    # Remove unwanted tags
    for element in soup(["script", "style", "noscript", "nav", "footer", "header", "aside", "form", "iframe"]):
        element.decompose()
        
    # Get main content
    text_content = []
    main_containers = soup.find_all(["article", "main", "section"])
    if main_containers:
        for container in main_containers:
            text_content.append(container.get_text(separator="\n", strip=True))
    else:
        # Fallback
        text_content.append(soup.get_text(separator="\n", strip=True))
        
    final_text = "\n".join(text_content).strip()
    if not final_text:
        raise ValueError("No meaningful text could be extracted from the URL.")
        
    chunks = chunk_text_with_metadata(final_text, page_num=1)
    
    parsed = urlparse(str(response.url))
    domain = parsed.hostname if parsed.hostname else url
    
    return {
        "chunks": chunks,
        "title": title if title else domain,
        "domain": domain,
        "url": str(response.url)
    }
