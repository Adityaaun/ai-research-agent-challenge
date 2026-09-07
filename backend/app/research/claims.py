import json
from typing import List, Dict, Any
from backend.app.llm import gemini

def extract_claims(question: str, evidence_list: List[Dict]) -> List[Dict]:
    """Extract factual claims from the evidence related to the question."""
    
    context = "\n\n".join([f"--- SOURCE ID: {item['id']} | {item['metadata']['source']} ---\n{item['document']}" for item in evidence_list])
    
    prompt = f"""You are a precise claim extraction engine.
Given the following research question and retrieved evidence passages, extract the core factual claims that answer the question.

Rules:
1. Extract 1 to 5 distinct, important claims.
2. For each claim, list the 'Source IDs' of the evidence passages that explicitly support it.
3. If a passage explicitly contradicts the claim, list its 'Source ID' under contradictions.
4. Output ONLY a valid JSON array of objects. Do not use markdown blocks.

JSON Format:
[
  {{
    "claim": "Text of the factual claim.",
    "supporting_source_ids": ["doc_abc123", ...],
    "contradicting_source_ids": []
  }}
]

Question: {question}

Evidence Passages:
{context}
"""
    try:
        response = gemini.generate_with_gemini(prompt)
        response = response.strip('`').removeprefix('json').strip()
        claims = json.loads(response)
        return claims if isinstance(claims, list) else []
    except Exception:
        return []

def calculate_confidence(claim: Dict) -> int:
    """Heuristic scoring for claim confidence."""
    support_count = len(claim.get("supporting_source_ids", []))
    contradict_count = len(claim.get("contradicting_source_ids", []))
    
    if support_count == 0:
        return 0
        
    # Base confidence from having support
    score = min(70 + (support_count * 10), 95)
    
    # Penalize for contradictions
    if contradict_count > 0:
        score -= (contradict_count * 20)
        
    return max(min(score, 100), 10)  # Clamp between 10% and 100%
