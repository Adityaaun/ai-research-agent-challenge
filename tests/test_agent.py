from src.agent import chunk_text, validate_citations


def test_chunk_text_creates_passages():
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = chunk_text(text, max_words=3)
    assert chunks
    assert all(chunk.strip() for chunk in chunks)
    assert "First paragraph." in chunks[0]


def test_valid_citation_is_accepted():
    retrieved = [
        {"metadata": {"source": "quantum_computing.txt"}},
        {"metadata": {"source": "mars_exploration.txt"}},
    ]
    answer = "Qubits can exist in superposition. [Source: quantum_computing.txt]"
    assert validate_citations(answer, retrieved)


def test_unknown_citation_is_rejected():
    retrieved = [{"metadata": {"source": "quantum_computing.txt"}}]
    answer = "Apollo 11 landed in 1969. [Source: apollo11.txt]"
    assert not validate_citations(answer, retrieved)
