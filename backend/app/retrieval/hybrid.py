from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database import models
from backend.app.retrieval import chroma

def get_bm25_results(query: str, db: Session, workspace_id: str = None, top_k: int = 10) -> List[Dict[str, Any]]:
    """Retrieve top results using BM25 lexical search."""
    # Fetch chunks from DB
    query_obj = db.query(models.DocumentChunk).join(models.Document)
    if workspace_id:
        query_obj = query_obj.filter(models.Document.workspace_id == workspace_id)
    
    chunks = query_obj.all()
    if not chunks:
        return []
        
    corpus = [chunk.text_content for chunk in chunks]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    
    bm25 = BM25Okapi(tokenized_corpus)
    tokenized_query = query.lower().split()
    
    doc_scores = bm25.get_scores(tokenized_query)
    
    # Sort and get top k
    scored_chunks = sorted(zip(chunks, doc_scores), key=lambda x: x[1], reverse=True)[:top_k]
    
    results = []
    for chunk, score in scored_chunks:
        if score > 0:
            results.append({
                "document": chunk.text_content,
                "metadata": {
                    "source": chunk.document.filename,
                    "chunk_index": chunk.chunk_index,
                    "page_number": chunk.page_number,
                    "document_id": chunk.document_id
                },
                "score": score,
                "id": f"{chunk.document.filename}_{chunk.chunk_index}"
            })
            
    return results

def reciprocal_rank_fusion(vector_results: List[Dict], bm25_results: List[Dict], k: int = 60) -> List[Dict]:
    """Fuse results using Reciprocal Rank Fusion (RRF)."""
    rrf_scores = {}
    
    # Assign RRF scores for vector results
    for rank, item in enumerate(vector_results, 1):
        # We need a stable ID to match
        doc_id = f"{item['metadata'].get('source')}_{item['metadata'].get('chunk_index')}"
        item['id'] = doc_id
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = {"item": item, "score": 0.0}
        rrf_scores[doc_id]["score"] += 1.0 / (k + rank)
        
    # Assign RRF scores for BM25 results
    for rank, item in enumerate(bm25_results, 1):
        doc_id = item["id"]
        if doc_id not in rrf_scores:
            # We don't have this item from vector search, just use it
            rrf_scores[doc_id] = {"item": item, "score": 0.0}
        rrf_scores[doc_id]["score"] += 1.0 / (k + rank)
        
    # Sort by RRF score
    sorted_fused = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
    return [entry["item"] for entry in sorted_fused]

def hybrid_search(query: str, db: Session, workspace_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform hybrid search (Vector + BM25 + Rank Fusion)."""
    # 1. Vector Search
    vector_results = chroma.retrieve(query, n_results=10)
    
    # Filter vector results by workspace if provided (Chroma query allows where clause but we filter post-retrieval for simplicity here)
    if workspace_id:
        vector_results = [r for r in vector_results if r["metadata"].get("workspace_id") == workspace_id]
        
    # 2. BM25 Search
    bm25_results = get_bm25_results(query, db, workspace_id, top_k=10)
    
    # 3. Rank Fusion
    fused_results = reciprocal_rank_fusion(vector_results, bm25_results)
    
    # Return top K
    return fused_results[:top_k]
