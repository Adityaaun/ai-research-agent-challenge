from rank_bm25 import BM25Okapi
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.database import models
from backend.app.retrieval import chroma
import logging

logger = logging.getLogger(__name__)

# BM25 Cache: workspace_id -> BM25Okapi instance
# In a real distributed system this would be Redis/Memcached.
_bm25_cache = {}

def invalidate_bm25_cache(workspace_id: str = None):
    """Invalidate the BM25 cache when the searchable corpus changes.
    
    Call this after document upload, chunk addition, or document deletion.
    If workspace_id is None, clears the entire cache.
    """
    global _bm25_cache
    if workspace_id is None:
        _bm25_cache.clear()
        logger.info("BM25 cache fully invalidated.")
    else:
        removed = _bm25_cache.pop(workspace_id, None)
        # Also clear the "global" key since global queries include all workspaces
        _bm25_cache.pop("global", None)
        if removed:
            logger.info(f"BM25 cache invalidated for workspace: {workspace_id}")


# Lazy loaded reranker
_reranker = None

def get_reranker():
    global _reranker
    if _reranker is None:
        try:
            from sentence_transformers import CrossEncoder
            logger.info("Loading CrossEncoder model...")
            # We use a lightweight model suitable for CPU
            _reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
            logger.info("CrossEncoder model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load CrossEncoder: {e}")
            _reranker = False # Mark as failed to avoid repeated loading attempts
    return _reranker

def get_bm25_results(query: str, db: Session, workspace_id: str = None, top_k: int = 10) -> List[Dict[str, Any]]:
    """Retrieve top results using BM25 lexical search with caching."""
    global _bm25_cache
    
    cache_key = workspace_id or "global"
    
    # Simple cache invalidation could be added here based on document counts
    if cache_key not in _bm25_cache:
        query_obj = db.query(models.DocumentChunk).join(models.Document)
        if workspace_id:
            query_obj = query_obj.filter(models.Document.workspace_id == workspace_id)
        
        chunks = query_obj.all()
        if not chunks:
            return []
            
        corpus = [chunk.text_content for chunk in chunks]
        tokenized_corpus = [doc.lower().split() for doc in corpus]
        
        # Cache plain dictionaries instead of ORM objects to prevent DetachedInstanceError
        cached_chunks = []
        for chunk in chunks:
            cached_chunks.append({
                "text_content": chunk.text_content,
                "document_filename": chunk.document.filename,
                "chunk_index": chunk.chunk_index,
                "page_number": chunk.page_number,
                "document_id": chunk.document_id
            })
        
        # Build index and cache it with the chunks to map back scores
        bm25 = BM25Okapi(tokenized_corpus)
        _bm25_cache[cache_key] = {"bm25": bm25, "chunks": cached_chunks}
    
    cached = _bm25_cache[cache_key]
    bm25 = cached["bm25"]
    chunks = cached["chunks"]
    
    tokenized_query = query.lower().split()
    doc_scores = bm25.get_scores(tokenized_query)
    
    # Sort and get top k
    scored_chunks = sorted(zip(chunks, doc_scores), key=lambda x: x[1], reverse=True)[:top_k]
    
    results = []
    for chunk, score in scored_chunks:
        if score > 0:
            results.append({
                "document": chunk["text_content"],
                "metadata": {
                    "source": chunk["document_filename"],
                    "chunk_index": chunk["chunk_index"],
                    "page_number": chunk["page_number"],
                    "document_id": chunk["document_id"]
                },
                "retrieval_score": float(score),
                "id": f"{chunk['document_filename']}_{chunk['chunk_index']}"
            })
            
    return results

def reciprocal_rank_fusion(vector_results: List[Dict], bm25_results: List[Dict], k: int = 60) -> List[Dict]:
    """Fuse results using Reciprocal Rank Fusion (RRF)."""
    rrf_scores = {}
    
    # Assign RRF scores for vector results
    for rank, item in enumerate(vector_results, 1):
        doc_id = f"{item['metadata'].get('source')}_{item['metadata'].get('chunk_index')}"
        item['id'] = doc_id
        item['retrieval_score'] = float(item.get('distance', 0)) # store distance as score
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = {"item": item, "score": 0.0}
        rrf_scores[doc_id]["score"] += 1.0 / (k + rank)
        
    # Assign RRF scores for BM25 results
    for rank, item in enumerate(bm25_results, 1):
        doc_id = item["id"]
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = {"item": item, "score": 0.0}
        rrf_scores[doc_id]["score"] += 1.0 / (k + rank)
        
    # Store the RRF score in the items and sort
    for doc_id, data in rrf_scores.items():
        data["item"]["rrf_score"] = float(data["score"])
        
    sorted_fused = sorted(rrf_scores.values(), key=lambda x: x["score"], reverse=True)
    return [entry["item"] for entry in sorted_fused]

def cross_encoder_rerank(query: str, results: List[Dict], top_k: int = 5) -> List[Dict]:
    """Rerank hybrid search results using a CrossEncoder model."""
    reranker = get_reranker()
    if not reranker or not results:
        return results[:top_k]
        
    # Prepare query-document pairs
    pairs = [[query, item["document"]] for item in results]
    
    try:
        # Get scores
        scores = reranker.predict(pairs)
        
        # Attach scores and sort
        for item, score in zip(results, scores):
            item["reranker_score"] = float(score)
            
        # Sort by reranker score
        reranked = sorted(results, key=lambda x: x.get("reranker_score", 0), reverse=True)
        return reranked[:top_k]
    except Exception as e:
        logger.error(f"Reranking failed: {e}")
        return results[:top_k]

def hybrid_search(query: str, db: Session, workspace_id: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
    """Perform hybrid search (Vector + BM25 + Rank Fusion + Reranking)."""
    # 1. Vector Search with native filtering
    where_clause = {"workspace_id": workspace_id} if workspace_id else None
    vector_results = chroma.retrieve(query, n_results=100, where=where_clause)
        
    # 2. BM25 Search
    bm25_results = get_bm25_results(query, db, workspace_id, top_k=100)
    
    # 3. Rank Fusion
    fused_results = reciprocal_rank_fusion(vector_results, bm25_results)
    
    # 4. Reranking (Disabled to prevent OOM on Render free tier)
    # reranked_results = cross_encoder_rerank(query, fused_results, top_k=top_k)
    
    return fused_results[:top_k]
