import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from backend.app.research.orchestrator import decompose_question, run_deep_research


class TestDecomposeQuestion:
    """Tests for question decomposition with mocked Gemini."""

    @pytest.mark.asyncio
    @patch("backend.app.research.orchestrator.gemini.generate_with_gemini")
    async def test_valid_decomposition(self, mock_gemini):
        mock_gemini.return_value = '["Sub Q1?", "Sub Q2?", "Sub Q3?"]'
        result = await decompose_question("What is quantum computing?")
        assert len(result) == 3
        assert result[0] == "Sub Q1?"

    @pytest.mark.asyncio
    @patch("backend.app.research.orchestrator.gemini.generate_with_gemini")
    async def test_malformed_decomposition_falls_back(self, mock_gemini):
        mock_gemini.return_value = "This is not JSON at all"
        result = await decompose_question("What is quantum computing?")
        assert result == ["What is quantum computing?"]

    @pytest.mark.asyncio
    @patch("backend.app.research.orchestrator.gemini.generate_with_gemini")
    async def test_gemini_failure_falls_back(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("API error")
        result = await decompose_question("What is quantum computing?")
        assert result == ["What is quantum computing?"]

    @pytest.mark.asyncio
    @patch("backend.app.research.orchestrator.gemini.generate_with_gemini")
    async def test_non_list_response_falls_back(self, mock_gemini):
        mock_gemini.return_value = '{"not": "a list"}'
        result = await decompose_question("What is quantum computing?")
        assert result == ["What is quantum computing?"]


class TestRunDeepResearch:
    """Tests for the research pipeline error paths."""

    @pytest.mark.asyncio
    @patch("backend.app.research.orchestrator.hybrid.hybrid_search")
    @patch("backend.app.research.orchestrator.gemini.generate_with_gemini")
    async def test_insufficient_evidence(self, mock_gemini, mock_search):
        """When no evidence is found, pipeline should return insufficient-evidence state."""
        mock_gemini.return_value = '["Sub Q1?"]'
        mock_search.return_value = []  # No evidence found

        db = MagicMock()
        events = []
        async for event in run_deep_research("test?", "ws_1", db):
            events.append(json.loads(event))

        final = events[-1]
        assert final["status"] == "complete"
        assert "Insufficient evidence" in final["report"]
        assert final["claims"] == []

    @pytest.mark.asyncio
    @patch("backend.app.research.orchestrator.claims.calculate_confidence")
    @patch("backend.app.research.orchestrator.claims.verify_claim")
    @patch("backend.app.research.orchestrator.claims.extract_claims")
    @patch("backend.app.research.orchestrator.hybrid.hybrid_search")
    @patch("backend.app.research.orchestrator.gemini.generate_with_gemini")
    async def test_report_generation_failure(self, mock_gemini, mock_search, mock_extract, mock_verify, mock_confidence):
        """When report generation fails, error is captured gracefully."""
        # First call: decomposition succeeds
        # Second call: report generation fails
        mock_gemini.side_effect = ['["Sub Q1?"]', RuntimeError("LLM down")]
        mock_search.return_value = [
            {"id": "doc_1", "document": "text", "metadata": {"source": "f.pdf", "chunk_index": 0, "page_number": 1, "document_id": "d1"}, "reranker_score": 5.0}
        ]
        mock_extract.return_value = [{"claim": "Test claim"}]
        mock_verify.return_value = {"claim": "Test claim", "supporting_source_ids": ["doc_1"], "contradicting_source_ids": []}
        mock_confidence.return_value = {"claim": "Test claim", "confidence": 80, "confidence_level": "high", "reasons": [], "supporting_source_ids": ["doc_1"], "contradicting_source_ids": []}

        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.refresh = MagicMock()

        events = []
        async for event in run_deep_research("test?", "ws_1", db):
            events.append(json.loads(event))

        final = events[-1]
        assert final["status"] == "complete"
        assert "Failed to generate report" in final["report"]
