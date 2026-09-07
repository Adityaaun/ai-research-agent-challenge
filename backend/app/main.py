from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Veritas RAG API",
    description="Evidence-First AI Research Intelligence Platform",
    version="1.0.0",
)

from backend.app.core.config import settings

# Set up CORS
origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Welcome to Veritas RAG API"}

from backend.app.api import endpoints
from backend.app.database.session import engine
from backend.app.database import models

# Create tables
models.Base.metadata.create_all(bind=engine)

app.include_router(endpoints.router, prefix="/api/v1")
from backend.app.api import documents, research, workspaces
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(research.router, prefix="/api/v1/research", tags=["research"])
app.include_router(workspaces.router, prefix="/api/v1/workspaces", tags=["workspaces"])
