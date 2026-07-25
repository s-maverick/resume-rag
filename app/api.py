from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app.services import ResumeRAG

app = FastAPI(title="Resume RAG API", version="1.0.0")


class QueryRequest(BaseModel):
    job_description: str = Field(min_length=20, max_length=30_000)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query")
def query(request: QueryRequest) -> dict:
    try:
        answer, sources = ResumeRAG().answer(request.job_description)
        return {
            "answer": answer,
            "sources": [
                {"file": item.source_file, "chunk": item.chunk_index,
                 "similarity": round(item.similarity, 4)}
                for item in sources
            ],
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Query failed. Check server logs and configuration.") from exc

