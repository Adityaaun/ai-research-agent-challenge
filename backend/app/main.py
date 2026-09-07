from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Veritas RAG API",
    description="Evidence-First AI Research Intelligence Platform",
    version="1.0.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual origins
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
from backend.app.api import documents, research
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(research.router, prefix="/api/v1/research", tags=["research"])
