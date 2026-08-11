# Sample Inputs and Outputs

This file demonstrates the expected capabilities of the Research Agent.

### Run Configuration
- **Model**: `gemini-1.5-flash`
- **Retrieval Engine**: `chromadb` (local sentence-transformers)
- **Loaded Documents**: 
  - `quantum_computing.txt`
  - `mars_exploration.txt`

---

## 🟢 Test 1: Standard Retrieval & Citation
**User Input (Question):**
> What is the fundamental unit of information in a quantum computer, and what special state allows it to perform simultaneous calculations?

**Agent Output:**
> The fundamental unit of information in a quantum computer is the quantum bit, or qubit [Source: quantum_computing.txt]. Qubits can exist in a multidimensional state known as superposition, which allows them to perform many calculations simultaneously [Source: quantum_computing.txt].

---

## 🟢 Test 2: Standard Retrieval & Citation
**User Input (Question):**
> Which rover is currently searching for signs of ancient life on Mars, and where did it land?

**Agent Output:**
> NASA's Perseverance rover is currently searching for signs of ancient microbial life [Source: mars_exploration.txt]. It landed in Jezero Crater in 2021 [Source: mars_exploration.txt].

---

## 🔴 Test 3: Hallucination Prevention (Out of Scope Question)
**User Input (Question):**
> When did the Apollo 11 mission land on the moon?

**Agent Output:**
> The provided sources do not contain the answer to this question.

*(Note: The agent successfully followed its system prompt and refused to guess or use its outside knowledge, strictly adhering to the provided documents).*
