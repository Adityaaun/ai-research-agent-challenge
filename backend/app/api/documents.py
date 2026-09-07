from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
import hashlib
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse
from backend.app.database import session, models
from backend.app.schemas import schemas
from backend.app.ingestion import parser
from backend.app.retrieval import chroma

router = APIRouter()

def normalize_url(url_str: str) -> str:
    parsed = urlparse(url_str)
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    path = parsed.path
    if path.endswith('/') and len(path) > 1:
        path = path[:-1]
    query = parsed.query
    return urlunparse((scheme, netloc, path, '', query, ''))

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

@router.post("/ingest-url", response_model=schemas.Document)
async def ingest_url(
    req: schemas.URLIngestRequest,
    db: Session = Depends(session.get_db)
):
    """Fetch, parse, chunk, and index a web URL."""
    workspace = None
    if req.workspace_id:
        workspace = db.query(models.Workspace).filter(models.Workspace.id == req.workspace_id).first()
    
    if not workspace:
        workspace = models.Workspace(name="Default Workspace")
        db.add(workspace)
        db.commit()
        db.refresh(workspace)
        
    normalized = normalize_url(req.url)
    
    # Check duplicate
    existing = db.query(models.Document).filter(
        models.Document.workspace_id == workspace.id,
        models.Document.filename == normalized
    ).first()
    
    if existing:
        raise HTTPException(status_code=409, detail="URL already ingested in this workspace.")
        
    try:
        parsed_data = await parser.parse_url(normalized)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
        
    chunks = parsed_data["chunks"]
    title = parsed_data["title"]
    domain = parsed_data["domain"]
    final_url = parsed_data["url"]
        
    db_doc = models.Document(
        workspace_id=workspace.id,
        filename=normalized,
        file_type="url",
        status="indexing"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    documents_to_index = []
    metadatas_to_index = []
    ids_to_index = []
    
    retrieved_at = datetime.now(timezone.utc).isoformat()
    
    for i, chunk in enumerate(chunks):
        db_chunk = models.DocumentChunk(
            document_id=db_doc.id,
            chunk_index=i,
            page_number=chunk.get("page"),
            text_content=chunk.get("text")
        )
        db.add(db_chunk)
        
        documents_to_index.append(chunk.get("text"))
        metadatas_to_index.append({
            "source_type": "web",
            "source": normalized, 
            "url": final_url,
            "title": title,
            "domain": domain,
            "retrieved_at": retrieved_at,
            "chunk_index": i,
            "page_number": chunk.get("page", 1),
            "document_id": db_doc.id,
            "workspace_id": workspace.id
        })
        ids_to_index.append(_stable_id(normalized, i))
        
    db.commit()
    
    try:
        chroma.collection.add(
            documents=documents_to_index,
            metadatas=metadatas_to_index,
            ids=ids_to_index
        )
        db_doc.status = "indexed"
        db.commit()
        
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

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(session.get_db)):
    """Delete a document and its chunks from DB and Chroma."""
    doc = db.query(models.Document).filter(models.Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    workspace_id = doc.workspace_id
    
    # Delete from ChromaDB
    try:
        chroma.collection.delete(where={"document_id": document_id})
    except Exception as e:
        print(f"Error deleting from Chroma: {e}")
        
    # Delete chunks from relational DB
    db.query(models.DocumentChunk).filter(models.DocumentChunk.document_id == document_id).delete()
    
    # Delete document from relational DB
    db.delete(doc)
    db.commit()
    
    # Invalidate BM25 cache
    from backend.app.retrieval.hybrid import invalidate_bm25_cache
    invalidate_bm25_cache(workspace_id)
    
    return {"message": "Document deleted successfully"}
