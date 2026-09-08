from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.app.database import session
from backend.app.schemas import schemas
from backend.app.research import orchestrator

router = APIRouter()

@router.get("/start")
async def start_research(question: str, workspace_id: str = None, db: Session = Depends(session.get_db)):
    """Stream deep research progress using Server-Sent Events (SSE)."""
    
    async def event_generator():
        async for event_data in orchestrator.run_deep_research(question, workspace_id, db):
            # SSE format: "data: {json}\n\n"
            yield f"data: {event_data}\n\n"
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/sessions")
def list_sessions(workspace_id: str = None, db: Session = Depends(session.get_db)):
    """List historical research sessions."""
    from backend.app.database import models
    query = db.query(models.ResearchSession).order_by(models.ResearchSession.created_at.desc())
    if workspace_id:
        query = query.filter(models.ResearchSession.workspace_id == workspace_id)
        
    sessions = query.all()
    return [{
        "id": s.id,
        "question": s.question,
        "report": s.report,
        "claims_data": s.claims_data,
        "created_at": s.created_at
    } for s in sessions]
