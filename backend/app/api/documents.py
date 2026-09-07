from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import hashlib
from backend.app.database import session, models
from backend.app.schemas import schemas
from backend.app.ingestion import parser
from backend.app.retrieval import chroma

router = APIRouter()

def _stable_id(filename: str, chunk_index: int) -> str:
    digest = hashlib.sha1(f"{filename}:{chunk_index}".encode()).hexdigest()[:16]
    return f"doc_{digest}"

@router.post("/upload", response_model=schemas.Document)
async def upload_document(
    file: UploadFile = File(...),
    workspace_id: str = None,
    db: Session = Depends(session.get_db)
):
    """Upload, parse, chunk, and index a document."""
    
    # Check workspace (or create default if none provided for now)
    workspace = None
    if workspace_id:
        workspace = db.query(models.Workspace).filter(models.Workspace.id == workspace_id).first()
    
    if not workspace:
        workspace = models.Workspace(name="Default Workspace")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        
    try:
        content = await file.read()
        chunks = parser.parse_document(file.filename, content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    # Create DB entry for Document
    db_doc = models.Document(
        workspace_id=workspace.id,
        filename=file.filename,
        file_type=file.filename.split('.')[-1],
        status="indexing"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    # Index in Chroma and add chunks to DB
    documents_to_index = []
    metadatas_to_index = []
    ids_to_index = []
    
    for i, chunk in enumerate(chunks):
        # Save to relational DB
        db_chunk = models.DocumentChunk(
            document_id=db_doc.id,
            chunk_index=i,
            page_number=chunk.get("page"),
            text_content=chunk.get("text")
        )
        db.add(db_chunk)
        
        # Prepare for Vector DB
        documents_to_index.append(chunk.get("text"))
        metadatas_to_index.append({
            "source": file.filename, 
            "chunk_index": i,
            "page_number": chunk.get("page", 1),
            "document_id": db_doc.id,
            "workspace_id": workspace.id
        })
        ids_to_index.append(_stable_id(file.filename, i))
        
    db.commit()
    
    # Add to ChromaDB collection
    try:
        chroma.collection.add(
            documents=documents_to_index,
            metadatas=metadatas_to_index,
            ids=ids_to_index
        )
        db_doc.status = "indexed"
        db.commit()
        
        # Invalidate BM25 cache for this workspace since corpus changed
        from backend.app.retrieval.hybrid import invalidate_bm25_cache
        invalidate_bm25_cache(workspace.id)
    except Exception as e:
        db_doc.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to index vectors: {e}")
        
    return db_doc

@router.get("/", response_model=List[schemas.Document])
def list_documents(workspace_id: str = None, db: Session = Depends(session.get_db)):
    query = db.query(models.Document)
    if workspace_id:
        query = query.filter(models.Document.workspace_id == workspace_id)
    return query.all()
