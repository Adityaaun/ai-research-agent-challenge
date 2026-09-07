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
