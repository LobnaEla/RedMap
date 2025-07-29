from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import warnings
import sys
import os

# Suppress warnings
if not sys.warnoptions:
    warnings.simplefilter("ignore")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from embeddings import HuggingFaceEmbedder
from vectorstore import WeaviateVectorStore, WeaviateSchema
from rag import RAGEngine
from config import Config
from fastapi.middleware.cors import CORSMiddleware

# FastAPI app
app = FastAPI(title="MITRE Technique RAG API")

# Allow all origins for development (⚠️ adjust for prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global objects
config = Config()
embedder = HuggingFaceEmbedder()
store = WeaviateVectorStore()
engine = RAGEngine(embedder=embedder, vector_store=store)

# Ensure schema exists
WeaviateSchema.get_mitre_technique_schema()

class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

class TechniqueResult(BaseModel):
    technique_id: str
    name: str
    description: str
    score: float

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/query", response_model=List[TechniqueResult])
def query_techniques(request: QueryRequest):
    try:
        results = engine.retrieve_techniques(request.query, top_k=request.top_k)
        return [
            TechniqueResult(
                technique_id=result.metadata.get("technique_id", result.metadata.get("id", "")),
                name=result.metadata.get("name", ""),
                description=result.metadata.get("description", ""),
                score=getattr(result, "score", 0.0)
            ) for result in results
        ] if results else []
    except Exception as e:
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
