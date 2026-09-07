import re
import chromadb
from typing import Any, List, Dict
from backend.app.core.config import settings

chroma_client = chromadb.PersistentClient(path=str(settings.CHROMA_DIR))
collection = chroma_client.get_or_create_collection(name=settings.COLLECTION_NAME)
MAX_RESULTS = 4

def retrieve(query: str, n_results: int = MAX_RESULTS, where: dict = None) -> List[Dict[str, Any]]:
    """Retrieve the most relevant source passages for a question."""
    if collection.count() == 0:
        return []
    
    query_params = {
        "query_texts": [query],
        "n_results": min(n_results, collection.count()),
        "include": ["documents", "metadatas", "distances"]
    }
    if where:
        query_params["where"] = where
        
    result = collection.query(**query_params)
    
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]
    
    return [
        {"document": document, "metadata": metadata or {}, "distance": distance}
        for document, metadata, distance in zip(documents, metadatas, distances)
    ]

def build_context(retrieved: List[Dict[str, Any]]) -> str:
    """Format retrieved passages with explicit source boundaries."""
    sections: List[str] = []
    for index, item in enumerate(retrieved, start=1):
        source = item["metadata"].get("source", "unknown")
        chunk_index = item["metadata"].get("chunk_index", 0)
        sections.append(
            f"--- SOURCE_{index} | {source} | passage {chunk_index} ---\n"
            f"{item['document']}\n"
            f"--- END SOURCE_{index} ---"
        )
    return "\n\n".join(sections)

def validate_citations(answer: str, retrieved: List[Dict[str, Any]]) -> bool:
    """Ensure an answer has citations and every cited filename was retrieved."""
    cited_files = set(re.findall(r"\[Source:\s*([^\]]+)\]", answer))
    valid_files = {
        item["metadata"].get("source")
        for item in retrieved
        if item["metadata"].get("source")
    }
    return bool(cited_files) and cited_files.issubset(valid_files)
