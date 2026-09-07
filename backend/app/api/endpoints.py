from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from backend.app.schemas import schemas
from backend.app.database import session, models
from backend.app.retrieval import chroma, hybrid
from backend.app.llm import gemini

router = APIRouter()
REFUSAL = "The provided sources do not contain the answer to this question."

@router.post("/ask", response_model=schemas.AskResponse)
def ask_question(request: schemas.AskRequest, db: Session = Depends(session.get_db)):
    """Ask a question and get a grounded response with citations."""
    # Use hybrid retrieval (Vector + BM25 + RRF)
    retrieved = hybrid.hybrid_search(request.question, db, workspace_id=request.workspace_id)
    
    if not retrieved:
        return schemas.AskResponse(answer=REFUSAL, sources=[])
        
    context = chroma.build_context(retrieved)
    
    prompt = f"""You are a strict research assistant.
Answer the user's question using ONLY the source passages below.

Rules:
1. Do not use outside knowledge or assumptions.
2. If the sources do not contain enough information to answer the question, reply EXACTLY:
{REFUSAL}
3. Every factual claim must end with a citation in this exact format: [Source: filename.txt]
4. Only cite filenames that appear in the provided source passages.
5. Do not invent source names, facts, dates, or details.
6. Keep the answer concise and directly answer the question.

SOURCE PASSAGES:
{context}

USER QUESTION: {request.question}
"""

    try:
        answer = gemini.generate_with_gemini(prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if not answer:
        raise HTTPException(status_code=500, detail="Gemini returned an empty response.")
        
    if answer == REFUSAL:
        return schemas.AskResponse(answer=answer, sources=[])
        
    if not chroma.validate_citations(answer, retrieved):
        raise HTTPException(
            status_code=400, 
            detail="Gemini returned an answer without valid citations from the retrieved sources."
        )
        
    return schemas.AskResponse(answer=answer, sources=retrieved)
