import re
from backend.app.retrieval.chroma import validate_citations


class TestValidateCitations:
    """Tests for citation validation logic."""

    def test_valid_citation_accepted(self):
        retrieved = [
            {"metadata": {"source": "quantum_computing.txt"}},
            {"metadata": {"source": "mars_exploration.txt"}},
        ]
        answer = "Qubits use superposition. [Source: quantum_computing.txt]"
        assert validate_citations(answer, retrieved) is True

    def test_multiple_valid_citations(self):
        retrieved = [
            {"metadata": {"source": "doc_a.pdf"}},
            {"metadata": {"source": "doc_b.pdf"}},
        ]
        answer = "Fact A. [Source: doc_a.pdf] Fact B. [Source: doc_b.pdf]"
        assert validate_citations(answer, retrieved) is True

    def test_invalid_citation_rejected(self):
        retrieved = [{"metadata": {"source": "quantum_computing.txt"}}]
        answer = "Apollo 11 landed in 1969. [Source: apollo11.txt]"
        assert validate_citations(answer, retrieved) is False

    def test_missing_citation_rejected(self):
        retrieved = [{"metadata": {"source": "quantum_computing.txt"}}]
        answer = "Qubits use superposition but no citation here."
        assert validate_citations(answer, retrieved) is False

    def test_empty_retrieved_list(self):
        answer = "Some answer. [Source: file.txt]"
        assert validate_citations(answer, []) is False

    def test_partial_invalid_citation_rejected(self):
        retrieved = [{"metadata": {"source": "real.txt"}}]
        answer = "Fact. [Source: real.txt] Fake. [Source: fake.txt]"
        assert validate_citations(answer, retrieved) is False
