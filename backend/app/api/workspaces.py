from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from backend.app.database import session, models
from backend.app.retrieval import chroma
from pydantic import BaseModel

router = APIRouter()

class WorkspaceCreate(BaseModel):
    name: str = "New Research Chat"

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    created_at: str

@router.get("/", response_model=List[WorkspaceResponse])
def list_workspaces(db: Session = Depends(session.get_db)):
    """List all workspaces."""
    workspaces = db.query(models.Workspace).order_by(models.Workspace.created_at.desc()).all()
    return [{"id": w.id, "name": w.name, "created_at": w.created_at.isoformat()} for w in workspaces]

@router.post("/", response_model=WorkspaceResponse)
def create_workspace(req: WorkspaceCreate, db: Session = Depends(session.get_db)):
    """Create a new workspace."""
    workspace = models.Workspace(name=req.name)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return {"id": workspace.id, "name": workspace.name, "created_at": workspace.created_at.isoformat()}

@router.delete("/{workspace_id}")
def delete_workspace(workspace_id: str, db: Session = Depends(session.get_db)):
    """Delete a workspace and all its data."""
    workspace = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    # Delete from ChromaDB
    try:
        chroma.collection.delete(where={"workspace_id": workspace_id})
    except Exception as e:
        print(f"Error deleting workspace from Chroma: {e}")
        
    # Relational deletes
    # Delete chunks
    docs = db.query(models.Document).filter(models.Document.workspace_id == workspace_id).all()
    doc_ids = [doc.id for doc in docs]
    if doc_ids:
        db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
        
    # Delete docs
    db.query(models.Document).filter(models.Document.workspace_id == workspace_id).delete(synchronize_session=False)
    
    # Delete research sessions
    db.query(models.ResearchSession).filter(models.ResearchSession.workspace_id == workspace_id).delete(synchronize_session=False)
    
    # Delete workspace
    db.delete(workspace)
    db.commit()
    
    # Invalidate BM25 cache
    from backend.app.retrieval.hybrid import invalidate_bm25_cache
    invalidate_bm25_cache(workspace_id)
    
    return {"message": "Workspace deleted successfully"}
