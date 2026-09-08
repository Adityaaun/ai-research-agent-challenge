import asyncio
import json
import re
import logging
from typing import AsyncGenerator
from sqlalchemy.orm import Session
from backend.app.llm import gemini
from backend.app.retrieval import hybrid
from backend.app.research import claims
from backend.app.database import models

logger = logging.getLogger(__name__)

async def decompose_question(question: str) -> list[str]:
    """Decompose a complex research question into smaller sub-questions."""
    prompt = f"""You are a research planner. Break down the following complex research question into 3-4 specific, searchable sub-questions.
Return ONLY a JSON array of strings. No markdown formatting, no explanations.

Question: {question}
"""
    try:
        response = await gemini.generate_with_gemini(prompt)
        response = response.strip('`').removeprefix('json').strip()
        sub_questions = json.loads(response)
        if not isinstance(sub_questions, list):
            return [question]
        return sub_questions
    except Exception as e:
        logger.warning(f"Decomposition failed, using fallback split. Error: {e}")
        # Naive split for multi-part questions if API is down
        parts = [p.strip() for p in re.split(r'\band\b', question, flags=re.IGNORECASE) if p.strip()]
        if len(parts) > 1:
            return parts
        return [question]

async def run_deep_research(question: str, workspace_id: str, db: Session) -> AsyncGenerator[str, None]:
    """Orchestrate the deep research pipeline and yield SSE progress events."""
    session_record = None
    
    try:
        logger.info(f"Starting research session for workspace: {workspace_id}")
        
        # Dynamically rename workspace if it's the first question
        if workspace_id:
            workspace = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
            if workspace and workspace.name == "New Research Chat":
                # Create a concise title from the question
                title = question[:35] + ("..." if len(question) > 35 else "")
                workspace.name = title
                db.commit()
        
        # Step 1: Planning
        yield json.dumps({"status": "progress", "step": "Planning", "message": "Decomposing research question..."})
        sub_questions = await decompose_question(question)
        
        yield json.dumps({
            "status": "progress", 
            "step": "Planning", 
            "message": f"Generated {len(sub_questions)} sub-questions.",
            "data": sub_questions
        })
        
        # Step 2: Retrieving Evidence
        yield json.dumps({"status": "progress", "step": "Retrieving evidence", "message": "Querying hybrid search across sources..."})
        
        all_evidence = []
        for sq in sub_questions:
            results = await asyncio.to_thread(hybrid.hybrid_search, sq, db, workspace_id, 20)
            all_evidence.extend(results)
            
        if not all_evidence:
            logger.warning("No evidence retrieved across any sub-questions.")
            yield json.dumps({
                "status": "complete",
                "step": "Insufficient Evidence",
                "report": "Insufficient evidence found to answer this question. Please upload more relevant documents to the knowledge base.",
                "claims": [],
                "evidence": []
            })
            return
        
        # Deduplicate based on id
        unique_evidence = {item['id']: item for item in all_evidence}
        evidence_list = list(unique_evidence.values())
        
        # Re-sort deduplicated evidence by reranker score (or RRF score)
        evidence_list = sorted(evidence_list, key=lambda x: x.get("reranker_score", x.get("rrf_score", 0)), reverse=True)[:15]
        
        yield json.dumps({
            "status": "progress", 
            "step": "Retrieving evidence", 
            "message": f"Retrieved and reranked {len(evidence_list)} unique passages."
        })
        
        # Step 3: Extracting Claims
        yield json.dumps({"status": "progress", "step": "Extracting claims", "message": "Extracting grounded claims from evidence..."})
        extracted_claims = await claims.extract_claims(question, evidence_list)
        
        if not extracted_claims:
            logger.warning("Failed to extract any claims from the evidence.")
            
        yield json.dumps({
            "status": "progress", 
            "step": "Extracting claims", 
            "message": f"Extracted {len(extracted_claims)} factual claims."
        })
        
        # Step 4: Verification & Confidence
        yield json.dumps({"status": "progress", "step": "Checking contradictions", "message": "Verifying evidence and scoring confidence..."})
        
        scored_claims = []
        evidence_map = {item['id']: item for item in evidence_list}
        
        for claim in extracted_claims:
            # 1. Ask LLM to explicitly verify relationships
            verified_claim = await claims.verify_claim(claim, evidence_list)
            # 2. Calculate weighted confidence
            scored_claim = claims.calculate_confidence(verified_claim, evidence_map)
            scored_claims.append(scored_claim)
            
        # Step 5: Writing Report
        yield json.dumps({"status": "progress", "step": "Writing report", "message": "Synthesizing final research report..."})
        
        context = "\n\n".join([f"--- SOURCE ID: {item['id']} | {item['metadata']['source']} ---\n{item['document']}" for item in evidence_list])
        
        prompt = f"""You are an Evidence-First Research Assistant for Veritas RAG.
Your task is to write a comprehensive, factual response to the user's question based ONLY on the verified claims.

Question: {question}

Evidence:
{context}

Provide a highly structured, professional Markdown report. Do not invent information. 
Every factual claim must cite a Source ID using the format [doc_name, chunk_index] when referencing the source ID. For example, if Source ID is "Resume.pdf_12", write [Resume.pdf, chunk 12].

You MUST format your response with the following exact sections:
# Executive Summary
(A brief high-level summary of the answer)

# Key Findings
(Detailed bullet points covering the specifics, with explicit citations)

# Limitations & Contradictions
(Note any conflicting evidence or gaps in the provided sources)
"""
        try:
            report = await gemini.generate_with_gemini(prompt)
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
            report = f"Failed to generate report: {str(e)}"
            
        # Save to Database
        try:
            session_record = models.ResearchSession(
                workspace_id=workspace_id,
                question=question,
                report=report,
                claims_data=json.dumps({"claims": scored_claims, "evidence": evidence_list})
            )
            db.add(session_record)
            db.commit()
            db.refresh(session_record)
        except Exception as e:
            logger.error(f"Database error while saving session: {e}")
            db.rollback()
            
        yield json.dumps({
            "status": "complete",
            "step": "Done",
            "report": report,
            "claims": scored_claims,
            "evidence": evidence_list,
            "session_id": session_record.id if session_record else "error"
        })
        
    except Exception as e:
        logger.exception(f"Unhandled error in research pipeline: {e}")
        yield json.dumps({
            "status": "error",
            "message": f"Research pipeline failed: {str(e)}"
        })
