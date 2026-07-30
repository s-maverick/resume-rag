from __future__ import annotations

import json
from dataclasses import dataclass

from google import genai
from google.genai import types
from supabase import Client, create_client

from app.config import Settings, get_settings


@dataclass
class SearchResult:
    source_file: str
    chunk_index: int
    content: str
    similarity: float


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(str(v) for v in values) + "]"


class ResumeRAG:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.gemini = genai.Client(api_key=self.settings.gemini_api_key)
        self.db: Client = create_client(
            self.settings.supabase_url, self.settings.supabase_service_role_key
        )

    def embed(self, text: str, purpose: str) -> list[float]:
        # Embedding 2 uses an instruction in the input instead of task_type.
        instruction = (
            "task: search result | " if purpose == "query" else "title: resume | text: "
        )
        response = self.gemini.models.embed_content(
            model=self.settings.embedding_model,
            contents=f"{instruction}{text}",
            config=types.EmbedContentConfig(
                output_dimensionality=self.settings.embedding_dimensions
            ),
        )
        return list(response.embeddings[0].values)

    def replace_resume(self, source_file: str, chunks: list[str]) -> int:
        self.db.table("resume_chunks").delete().eq("source_file", source_file).execute()
        rows = []
        for index, chunk in enumerate(chunks):
            rows.append(
                {
                    "source_file": source_file,
                    "chunk_index": index,
                    "content": chunk,
                    "metadata": {"source_file": source_file},
                    "embedding": vector_literal(self.embed(chunk, "document")),
                }
            )
        if rows:
            self.db.table("resume_chunks").insert(rows).execute()
        return len(rows)

    def search(self, job_description: str, match_count: int | None = None) -> list[SearchResult]:
        response = self.db.rpc(
            "match_resume_chunks",
            {
                "query_embedding": vector_literal(self.embed(job_description, "query")),
                "match_count": match_count or self.settings.retrieval_match_count,
            },
        ).execute()
        return [
            SearchResult(
                source_file=row["source_file"], chunk_index=row["chunk_index"],
                content=row["content"], similarity=float(row["similarity"]),
            )
            for row in response.data
        ]

    def answer(self, job_description: str) -> tuple[str, list[SearchResult]]:
        matches = self.search(job_description)
        context = "\n\n".join(
            f"[Resume: {m.source_file}; chunk {m.chunk_index}; relevance {m.similarity:.3f}]\n{m.content}"
            for m in matches
        )
        prompt = f"""You are a precise career-assistant. Compare the job description with ONLY the resume evidence below. 
        Return: (1) strongest matching experience/skills as concise bullets, 
        (2) gaps or claims that are not supported by the resumes, and 
        (3) a short tailored summary. Never invent experience, numbers, employers, dates, or credentials. Cite each claim using [resume filename].

JOB DESCRIPTION:
{job_description}

RESUME EVIDENCE:
{context}"""
        response = self.gemini.models.generate_content(
            model=self.settings.generation_model,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2),
        )
        return response.text or "No answer was generated.", matches

