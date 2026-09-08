import pytest
from unittest.mock import patch, MagicMock
from backend.app.research.claims import extract_claims, verify_claim, calculate_confidence


class TestExtractClaims:
    """Tests for claim extraction with mocked Gemini."""

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_extract_claims_valid_response(self, mock_gemini):
        mock_gemini.return_value = '[{"claim": "The sky is blue."}]'
        evidence = [{"id": "doc_1", "metadata": {"source": "test.pdf"}, "document": "The sky is blue."}]
        result = await extract_claims("What color is the sky?", evidence)
        assert len(result) == 1
        assert result[0]["claim"] == "The sky is blue."

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_extract_claims_malformed_json(self, mock_gemini):
        mock_gemini.return_value = "This is not valid JSON at all {{{}"
        evidence = [{"id": "doc_1", "metadata": {"source": "test.pdf"}, "document": "text"}]
        result = await extract_claims("question?", evidence)
        assert result == []

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_extract_claims_markdown_wrapped_json(self, mock_gemini):
        mock_gemini.return_value = '```json\n[{"claim": "Water is H2O."}]\n```'
        evidence = [{"id": "doc_1", "metadata": {"source": "test.pdf"}, "document": "Water is H2O."}]
        result = await extract_claims("What is water?", evidence)
        assert len(result) == 1
        assert result[0]["claim"] == "Water is H2O."

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_extract_claims_empty_array(self, mock_gemini):
        mock_gemini.return_value = "[]"
        evidence = [{"id": "doc_1", "metadata": {"source": "test.pdf"}, "document": "text"}]
        result = await extract_claims("question?", evidence)
        assert result == []

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_extract_claims_gemini_exception(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("API down")
        evidence = [{"id": "doc_1", "metadata": {"source": "test.pdf"}, "document": "text"}]
        result = await extract_claims("question?", evidence)
        assert result == []


class TestVerifyClaim:
    """Tests for claim verification with mocked Gemini."""

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_verify_claim_support(self, mock_gemini):
        mock_gemini.return_value = '[{"evidence_id": "doc_1", "relationship": "SUPPORT", "reasoning": "directly states it"}]'
        claim = {"claim": "The sky is blue."}
        evidence = [{"id": "doc_1", "document": "The sky is blue."}]
        result = await verify_claim(claim, evidence)
        assert "doc_1" in result["supporting_source_ids"]
        assert result["contradicting_source_ids"] == []

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_verify_claim_contradict(self, mock_gemini):
        mock_gemini.return_value = '[{"evidence_id": "doc_1", "relationship": "CONTRADICT", "reasoning": "says opposite"}]'
        claim = {"claim": "The sky is green."}
        evidence = [{"id": "doc_1", "document": "The sky is blue."}]
        result = await verify_claim(claim, evidence)
        assert result["supporting_source_ids"] == []
        assert "doc_1" in result["contradicting_source_ids"]

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_verify_claim_neutral(self, mock_gemini):
        mock_gemini.return_value = '[{"evidence_id": "doc_1", "relationship": "NEUTRAL", "reasoning": "unrelated"}]'
        claim = {"claim": "Water is wet."}
        evidence = [{"id": "doc_1", "document": "The sky is blue."}]
        result = await verify_claim(claim, evidence)
        assert result["supporting_source_ids"] == []
        assert result["contradicting_source_ids"] == []

    @pytest.mark.asyncio
    @patch("backend.app.research.claims.gemini.generate_with_gemini")
    async def test_verify_claim_gemini_failure(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("API error")
        claim = {"claim": "Something."}
        evidence = [{"id": "doc_1", "document": "text"}]
        result = await verify_claim(claim, evidence)
        assert result["supporting_source_ids"] == []
        assert result["contradicting_source_ids"] == []


class TestCalculateConfidence:
    """Tests for the heuristic confidence scoring algorithm."""

    def test_no_support(self):
        claim = {"claim": "A", "supporting_source_ids": [], "contradicting_source_ids": []}
        result = calculate_confidence(claim, {})
        assert result["confidence"] == 0
        assert result["confidence_level"] == "low"

    def test_high_confidence(self):
        claim = {"claim": "B", "supporting_source_ids": ["1", "2", "3"], "contradicting_source_ids": []}
        ev_map = {
            "1": {"reranker_score": 5.0},
            "2": {"reranker_score": 4.5},
            "3": {"reranker_score": 6.0},
        }
        result = calculate_confidence(claim, ev_map)
        assert result["confidence"] >= 80
        assert result["confidence_level"] == "high"

    def test_contradiction_penalty(self):
        claim = {"claim": "C", "supporting_source_ids": ["1"], "contradicting_source_ids": ["4", "5"]}
        ev_map = {"1": {"reranker_score": 5.0}}
        result = calculate_confidence(claim, ev_map)
        assert result["confidence"] < 50
        assert result["confidence_level"] == "low"

    def test_medium_confidence(self):
        claim = {"claim": "D", "supporting_source_ids": ["1", "2"], "contradicting_source_ids": []}
        ev_map = {"1": {"reranker_score": -1.0}, "2": {"reranker_score": -1.0}}
        result = calculate_confidence(claim, ev_map)
        assert 50 <= result["confidence"] < 80
        assert result["confidence_level"] == "medium"

    def test_confidence_never_exceeds_100(self):
        claim = {"claim": "E", "supporting_source_ids": ["1","2","3","4","5"], "contradicting_source_ids": []}
        ev_map = {str(i): {"reranker_score": 9.0} for i in range(1, 6)}
        result = calculate_confidence(claim, ev_map)
        assert result["confidence"] <= 100

    def test_confidence_never_below_5_with_support(self):
        claim = {"claim": "F", "supporting_source_ids": ["1"], "contradicting_source_ids": ["2","3","4","5","6"]}
        result = calculate_confidence(claim, {})
        assert result["confidence"] >= 5
