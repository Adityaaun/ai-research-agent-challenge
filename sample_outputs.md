# Sample / Expected Outputs — Research Agent (with Citations)

This file documents the expected behavior of the agent for the supplied challenge questions. After running `python src/agent.py` locally, compare the generated answers with these examples.

---

## Question 1 — Quantum Computing

**Question:** What is the fundamental unit of information in a quantum computer, and what special state allows it to perform simultaneous calculations?

**Expected behavior:** Answer from `quantum_computing.txt` and cite it.

**Example answer:**

The fundamental unit of information in a quantum computer is the quantum bit, or qubit [Source: quantum_computing.txt]. Qubits can exist in a multidimensional state known as superposition, which allows them to perform many calculations simultaneously [Source: quantum_computing.txt].

---

## Question 2 — Mars Exploration

**Question:** Which rover is currently searching for signs of ancient life on Mars, and where did it land?

**Expected behavior:** Answer from `mars_exploration.txt` and cite it.

**Example answer:**

NASA's Perseverance rover is currently searching for signs of ancient microbial life and landed in Jezero Crater [Source: mars_exploration.txt].

---

## Question 3 — Hallucination Test

**Question:** When did the Apollo 11 mission land on the moon?

**Expected behavior:** The supplied sources do not contain this information, so the agent should refuse rather than use outside knowledge.

**Expected answer:**

The provided sources do not contain the answer to this question.

---

## Evaluation Summary

| # | Test | Expected behavior |
|---|---|---|
| 1 | Relevant retrieval + citation | Cite `quantum_computing.txt` |
| 2 | Different source + citation | Cite `mars_exploration.txt` |
| 3 | Unsupported question | Refuse to answer |

> Note: These are reference/expected outputs, not a claim that they were generated in the current repository state. Run the agent locally to produce fresh outputs for your environment.
