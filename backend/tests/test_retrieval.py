import pytest
from backend.app.research.claims import calculate_confidence
from backend.app.retrieval.hybrid import reciprocal_rank_fusion, invalidate_bm25_cache, _bm25_cache


class TestReciprocalRankFusion:
    def test_basic_fusion(self):
        vec_results = [
            {"metadata": {"source": "doc1", "chunk_index": 1}, "distance": 0.5},
            {"metadata": {"source": "doc2", "chunk_index": 2}, "distance": 0.4}
        ]
        bm25_results = [
            {"id": "doc2_2", "metadata": {"source": "doc2", "chunk_index": 2}, "retrieval_score": 10.5},
            {"id": "doc3_3", "metadata": {"source": "doc3", "chunk_index": 3}, "retrieval_score": 8.0}
        ]
        fused = reciprocal_rank_fusion(vec_results, bm25_results, k=1)
        assert len(fused) == 3
        assert fused[0]["id"] == "doc2_2"
        assert "rrf_score" in fused[0]

    def test_empty_vector_results(self):
        bm25_results = [{"id": "doc1_0", "metadata": {"source": "doc1", "chunk_index": 0}, "retrieval_score": 5.0}]
        fused = reciprocal_rank_fusion([], bm25_results)
        assert len(fused) == 1
        assert fused[0]["id"] == "doc1_0"

    def test_empty_bm25_results(self):
        vec_results = [{"metadata": {"source": "doc1", "chunk_index": 0}, "distance": 0.3}]
        fused = reciprocal_rank_fusion(vec_results, [])
        assert len(fused) == 1

    def test_both_empty(self):
        fused = reciprocal_rank_fusion([], [])
        assert fused == []


class TestBM25CacheInvalidation:
    def test_invalidate_specific_workspace(self):
        _bm25_cache["ws_1"] = {"bm25": "dummy", "chunks": []}
        _bm25_cache["ws_2"] = {"bm25": "dummy", "chunks": []}
        invalidate_bm25_cache("ws_1")
        assert "ws_1" not in _bm25_cache
        assert "ws_2" in _bm25_cache

    def test_invalidate_all(self):
        _bm25_cache["ws_1"] = {"bm25": "dummy", "chunks": []}
        _bm25_cache["ws_2"] = {"bm25": "dummy", "chunks": []}
        invalidate_bm25_cache(None)
        assert len(_bm25_cache) == 0

    def test_invalidate_clears_global(self):
        _bm25_cache["global"] = {"bm25": "dummy", "chunks": []}
        _bm25_cache["ws_1"] = {"bm25": "dummy", "chunks": []}
        invalidate_bm25_cache("ws_1")
        assert "global" not in _bm25_cache

    def test_invalidate_nonexistent_workspace(self):
        _bm25_cache.clear()
        invalidate_bm25_cache("nonexistent")  # Should not raise


class TestCalculateConfidence:
    def test_no_support(self):
        claim = {"claim": "A", "supporting_source_ids": [], "contradicting_source_ids": []}
        res = calculate_confidence(claim, {})
        assert res["confidence"] == 0
        assert res["confidence_level"] == "low"

    def test_high_confidence(self):
        claim = {"claim": "B", "supporting_source_ids": ["1", "2", "3"], "contradicting_source_ids": []}
        ev_map = {"1": {"reranker_score": 5.0}, "2": {"reranker_score": 4.5}, "3": {"reranker_score": 6.0}}
        res = calculate_confidence(claim, ev_map)
        assert res["confidence"] >= 80
        assert res["confidence_level"] == "high"

    def test_contradiction_penalty(self):
        claim = {"claim": "C", "supporting_source_ids": ["1"], "contradicting_source_ids": ["4", "5"]}
        ev_map = {"1": {"reranker_score": 5.0}}
        res = calculate_confidence(claim, ev_map)
        assert res["confidence"] < 50
        assert res["confidence_level"] == "low"
