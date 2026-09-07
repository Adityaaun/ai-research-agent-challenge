import json
import asyncio
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from backend.app.llm import gemini
from backend.app.retrieval import hybrid

async def decompose_question(question: str) -> list[str]:
    """Decompose a complex research question into smaller sub-questions."""
    prompt = f"""You are a research planner. Break down the following complex research question into 3-4 specific, searchable sub-questions.
Return ONLY a JSON array of strings. No markdown formatting, no explanations.

Question: {question}
"""
    try:
        response = gemini.generate_with_gemini(prompt)
        # Strip markdown if model added it
        response = response.strip('`').removeprefix('json').strip()
        sub_questions = json.loads(response)
        if not isinstance(sub_questions, list):
            return [question]
        return sub_questions
    except Exception:
        # Fallback if parsing fails
        return [question]

async def run_deep_research(question: str, workspace_id: str, db: Session) -> AsyncGenerator[str, None]:
    """Orchestrate the deep research pipeline and yield SSE progress events."""
    
    # Step 1: Planning
    yield json.dumps({"status": "progress", "step": "Planning", "message": "Decomposing research question..."})
    sub_questions = await decompose_question(question)
    
    yield json.dumps({
        "status": "progress", 
        "step": "Planning", 
        "message": f"Generated {len(sub_questions)} sub-questions.",
        "data": sub_questions
    })
    
    await asyncio.sleep(1) # simulate work for UI
    
    # Step 2: Retrieving Evidence
    yield json.dumps({"status": "progress", "step": "Retrieving evidence", "message": "Querying hybrid search across sources..."})
    
    all_evidence = []
    for sq in sub_questions:
        results = hybrid.hybrid_search(sq, db, workspace_id, top_k=3)
        all_evidence.extend(results)
    
    # Deduplicate based on id
    unique_evidence = {f"{item['metadata']['source']}_{item['metadata']['chunk_index']}": item for item in all_evidence}
    evidence_list = list(unique_evidence.values())
    
    yield json.dumps({
        "status": "progress", 
        "step": "Retrieving evidence", 
        "message": f"Retrieved {len(evidence_list)} unique passages."
    })
    
    await asyncio.sleep(1)
    
    # Step 3: Reranking (Placeholder for actual reranker logic in later phase)
    yield json.dumps({"status": "progress", "step": "Reranking", "message": "Ranking evidence by relevance..."})
    await asyncio.sleep(1)
    
    from backend.app.research import claims
    
    # Step 4: Extracting Claims
    yield json.dumps({"status": "progress", "step": "Extracting claims", "message": "Extracting grounded claims from evidence..."})
    extracted_claims = claims.extract_claims(question, evidence_list)
    
    yield json.dumps({
        "status": "progress", 
        "step": "Extracting claims", 
        "message": f"Extracted {len(extracted_claims)} factual claims."
    })
    
    # Step 5 & 6: Checking Contradictions & Calculating Confidence
    yield json.dumps({"status": "progress", "step": "Checking contradictions", "message": "Scoring evidence strength..."})
    
    scored_claims = []
    for claim in extracted_claims:
        claim["confidence"] = claims.calculate_confidence(claim)
        scored_claims.append(claim)
    
    await asyncio.sleep(1)
    
    # Step 7: Writing Report
    yield json.dumps({"status": "progress", "step": "Writing report", "message": "Synthesizing final research report..."})
    
    # Build a structured payload containing the report, the raw evidence, and the structured claims.
    context = "\n\n".join([f"--- SOURCE: {item['metadata']['source']} ---\n{item['document']}" for item in evidence_list])
    
    prompt = f"""You are an Evidence-First Research Assistant for RESEARCHOS.
Answer the user's question using ONLY the provided evidence.

Question: {question}

Evidence:
{context}

Provide a highly structured, professional Markdown report. Do not invent information. Every factual claim must cite a source filename.

You MUST format your response with the following exact sections:
# Executive Summary
(A brief high-level summary of the answer)

# Key Findings
(Detailed bullet points covering the specifics, citing source files)

# Limitations & Contradictions
(Note any conflicting evidence or gaps in the provided sources)
"""
    try:
        report = gemini.generate_with_gemini(prompt)
    except Exception as e:
        report = f"Failed to generate report: {str(e)}"
        
    # Save to Database
    from backend.app.database import models
    session_record = models.ResearchSession(
        workspace_id=workspace_id,
        question=question,
        report=report,
        claims_data=json.dumps({"claims": scored_claims, "evidence": evidence_list})
    )
    db.add(session_record)
    db.commit()
    db.refresh(session_record)
        
    yield json.dumps({
        "status": "complete",
        "step": "Done",
        "report": report,
        "claims": scored_claims,
        "evidence": evidence_list,
        "session_id": session_record.id
    })
