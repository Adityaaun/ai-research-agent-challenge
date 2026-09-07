import pytest
from backend.app.research.claims import calculate_confidence
from backend.app.retrieval.hybrid import reciprocal_rank_fusion

def test_reciprocal_rank_fusion():
    vec_results = [
        {"metadata": {"source": "doc1", "chunk_index": 1}, "distance": 0.5},
        {"metadata": {"source": "doc2", "chunk_index": 2}, "distance": 0.4}
    ]
    bm25_results = [
        {"id": "doc2_2", "metadata": {"source": "doc2", "chunk_index": 2}, "score": 10.5},
        {"id": "doc3_3", "metadata": {"source": "doc3", "chunk_index": 3}, "score": 8.0}
    ]
    
    fused = reciprocal_rank_fusion(vec_results, bm25_results, k=1)
    
    # Expected ordering: doc2_2 (rank 2 vec, rank 1 bm25), doc1_1 (rank 1 vec), doc3_3 (rank 2 bm25)
    # doc2_2 score: 1/(1+2) + 1/(1+1) = 1/3 + 1/2 = 0.833
    # doc1_1 score: 1/(1+1) = 0.5
    # doc3_3 score: 1/(1+2) = 0.333
    assert len(fused) == 3
    assert fused[0]["id"] == "doc2_2"
    assert fused[1]["id"] == "doc1_1"
    assert fused[2]["id"] == "doc3_3"
    assert "rrf_score" in fused[0]

def test_calculate_confidence():
    # 1. No support
    claim1 = {"claim": "A", "supporting_source_ids": [], "contradicting_source_ids": []}
    res1 = calculate_confidence(claim1, {})
    assert res1["confidence"] == 0
    assert res1["confidence_level"] == "low"
    
    # 2. Strong support, no contradictions, high reranker scores
    claim2 = {"claim": "B", "supporting_source_ids": ["1", "2", "3"]}
    ev_map = {
        "1": {"reranker_score": 5.0},
        "2": {"reranker_score": 4.5},
        "3": {"reranker_score": 6.0}
    }
    res2 = calculate_confidence(claim2, ev_map)
    assert res2["confidence"] >= 95
    assert res2["confidence_level"] == "high"
    
    # 3. Contradictions applied
    claim3 = {"claim": "C", "supporting_source_ids": ["1"], "contradicting_source_ids": ["4", "5"]}
    res3 = calculate_confidence(claim3, ev_map)
    assert res3["confidence"] < 50
    assert res3["confidence_level"] == "low"
