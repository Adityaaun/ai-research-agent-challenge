import json
from typing import List, Dict, Any
from backend.app.llm import gemini
import logging

logger = logging.getLogger(__name__)

async def extract_claims(question: str, evidence_list: List[Dict]) -> List[Dict]:
    """Extract factual claims from the evidence related to the question."""
    
    context = "\n\n".join([f"--- SOURCE ID: {item['id']} | {item['metadata']['source']} ---\n{item['document']}" for item in evidence_list])
    
    prompt = f"""You are a precise claim extraction engine.
Given the following research question and retrieved evidence passages, extract the core factual claims that answer the question.

Rules:
1. Extract 1 to 5 distinct, important claims.
2. Output ONLY a valid JSON array of objects. Do not use markdown blocks.

JSON Format:
[
  {{
    "claim": "Text of the factual claim."
  }}
]

Question: {question}

Evidence Passages:
{context}
"""
    try:
        response = await gemini.generate_with_gemini(prompt)
        response = response.strip('`').removeprefix('json').strip()
        claims = json.loads(response)
        # Ensure we return valid format even if LLM slightly hallucinates schema
        return [{"claim": c.get("claim", str(c))} for c in claims] if isinstance(claims, list) else []
    except Exception as e:
        logger.error(f"Claim extraction failed: {e}")
        return []

async def verify_claim(claim: Dict, evidence_list: List[Dict]) -> Dict:
    """Run a dedicated verification pass to check each piece of evidence against the claim."""
    
    context = "\n\n".join([f"--- EVIDENCE ID: {item['id']} ---\n{item['document']}" for item in evidence_list])
    
    prompt = f"""You are an expert fact-checker. 
Evaluate how each piece of evidence relates to the given claim.

Claim: {claim['claim']}

Evidence:
{context}

For EACH Evidence ID provided, classify the relationship as "SUPPORT", "CONTRADICT", or "NEUTRAL".
Return ONLY a JSON array of objects matching this exact schema, with no markdown:
[
  {{
    "evidence_id": "...",
    "relationship": "SUPPORT" | "CONTRADICT" | "NEUTRAL",
    "reasoning": "brief explanation"
  }}
]
"""
    supporting = []
    contradicting = []
    
    try:
        response = await gemini.generate_with_gemini(prompt)
        response = response.strip('`').removeprefix('json').strip()
        verifications = json.loads(response)
        
        for v in verifications:
            if v.get("relationship") == "SUPPORT":
                supporting.append(v.get("evidence_id"))
            elif v.get("relationship") == "CONTRADICT":
                contradicting.append(v.get("evidence_id"))
                
    except Exception as e:
        logger.error(f"Claim verification failed: {e}")
        
    claim["supporting_source_ids"] = supporting
    claim["contradicting_source_ids"] = contradicting
    return claim

def calculate_confidence(claim: Dict, evidence_map: Dict[str, Dict]) -> Dict:
    """Advanced heuristic scoring for claim confidence based on verified relationships and reranker scores."""
    support_ids = claim.get("supporting_source_ids", [])
    contradict_ids = claim.get("contradicting_source_ids", [])
    
    reasons = []
    
    if not support_ids:
        claim["confidence"] = 0
        claim["confidence_level"] = "low"
        claim["reasons"] = ["No direct supporting evidence found."]
        return claim
        
    score = 50 # Base score for having any support
    
    # 1. Number of independent supporting passages
    if len(support_ids) >= 3:
        score += 20
        reasons.append(f"Strong support from {len(support_ids)} independent passages.")
    elif len(support_ids) == 2:
        score += 10
        reasons.append("Supported by 2 passages.")
    else:
        reasons.append("Supported by only 1 passage.")
        
    # 2. Reranker/Retrieval strength of supporting evidence
    avg_reranker = 0
    valid_scores = 0
    for sid in support_ids:
        if sid in evidence_map and "reranker_score" in evidence_map[sid]:
            avg_reranker += evidence_map[sid]["reranker_score"]
            valid_scores += 1
            
    if valid_scores > 0:
        avg = avg_reranker / valid_scores
        # CrossEncoder scores generally range from -10 to 10.
        if avg > 3.0:
            score += 15
            reasons.append("Evidence has very high semantic relevance.")
        elif avg > 0:
            score += 5
            reasons.append("Evidence has moderate semantic relevance.")
            
    # 3. Contradiction Penalty
    if contradict_ids:
        penalty = len(contradict_ids) * 25
        score -= penalty
        reasons.append(f"Major penalty due to {len(contradict_ids)} contradicting passages.")
    else:
        score += 15
        reasons.append("No contradicting evidence found.")
        
    # Clamp and classify
    final_score = max(min(score, 100), 5)
    claim["confidence"] = final_score
    
    if final_score >= 80:
        claim["confidence_level"] = "high"
    elif final_score >= 50:
        claim["confidence_level"] = "medium"
    else:
        claim["confidence_level"] = "low"
        
    claim["reasons"] = reasons
    return claim
