from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class WorkspaceBase(BaseModel):
    name: str

class WorkspaceCreate(WorkspaceBase):
    pass

class Workspace(WorkspaceBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class DocumentBase(BaseModel):
    filename: str
    file_type: str

class Document(DocumentBase):
    id: str
    workspace_id: str
    uploaded_at: datetime
    status: str
    
    class Config:
        from_attributes = True

class AskRequest(BaseModel):
    question: str
    workspace_id: Optional[str] = None

class AskResponse(BaseModel):
    answer: str
    sources: List[dict]

class Citation(BaseModel):
    source: str
    page_number: Optional[int] = None
    chunk_index: int
    document_id: str

class VerificationResult(BaseModel):
    evidence_id: str
    relationship: str
    reasoning: str

class Claim(BaseModel):
    claim: str
    supporting_source_ids: List[str]
    contradicting_source_ids: List[str]

class ScoredClaim(Claim):
    confidence: int
    confidence_level: str
    reasons: List[str]
