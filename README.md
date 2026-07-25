# Resume RAG (Gemini + Supabase)

Give this application a job description and it finds the most relevant evidence across all your resumes, then asks Gemini to produce an evidence-grounded match summary. It supports PDF, DOCX, TXT, and Markdown resumes.

## Architecture

`resumes/` → text extraction and chunking → Gemini embeddings → Supabase pgvector → similarity search → Gemini answer with resume citations

The API returns both a grounded answer and the files/chunks retrieved for it. Resume content and embeddings remain in your Supabase project; they are sent to Gemini while indexing and answering.

## Local setup

1. Create a Supabase project. In **SQL Editor**, run [supabase/schema.sql](supabase/schema.sql). This creates the `resume_chunks` table, an HNSW vector index, and the `match_resume_chunks` search function.

2. Create a Gemini API key in Google AI Studio. Copy environment values (optional):

   ```bash
   cp .env .env
   ```

   Fill in `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`. Get the **Project URL** (for example, `https://PROJECT_REF.supabase.co`, without `/rest/v1`) and **service_role** key from Project Settings → API. Keep this key only in `.env` or your deployment secrets—never a frontend.

3. Create a Python environment and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

4. Put all ~8 resumes into `resumes/` (PDF, DOCX, TXT, or MD). If a scanned PDF gives no text, OCR it first. Index them:

   ```bash
   python ingest.py
   ```

   Re-run this command after replacing a resume. It removes and recreates chunks only for files that are currently indexed.

5. Ask from the terminal:

   ```bash
   python query.py "Paste the full job description here"
   ```

   Or run the HTTP API:

   ```bash
   uvicorn main:app --reload
   curl -X POST http://127.0.0.1:8000/query \
     -H 'Content-Type: application/json' \
     -d '{"job_description":"Paste the job description here"}'
   ```

## Deploy the API

This container works on Google Cloud Run, Render, Railway, Fly.io, or any Docker host.

1. Create a new service from this repository and use the included `Dockerfile`.
2. Set these deployment secrets (not build-time variables): `GEMINI_API_KEY`, `SUPABASE_URL`, and `SUPABASE_SERVICE_ROLE_KEY`. Optionally set the model variables from `.env.example`.
3. Set the service port to `8080` (the Dockerfile also honors a platform-provided `PORT`).
4. Deploy, then verify `GET https://YOUR-SERVICE/health` and send a `POST /query` request as above.
5. Keep resume ingestion on your trusted laptop/CI runner: add a resume, run `python ingest.py`, then use the deployed service to query it. The deployed API needs no resume files after indexing.

For a public-facing app, put authentication in front of `/query` (for example, Supabase Auth or your platform's access control) and rate-limit it. The supplied API deliberately never accepts the Supabase service key from callers.

## Important configuration

The SQL schema and `.env` both use **1536** embedding dimensions. If you change `EMBEDDING_DIMENSIONS`, recreate the table and search function with the same dimension and re-index every resume. Do not mix vector dimensions or embedding models in one collection.

The default embedding model is `gemini-embedding-2`; its embedding space is incompatible with older Gemini embedding models. Changing it requires deleting/re-indexing all vectors.

The default answer model is `gemini-3.5-flash`. Gemini can restrict older models for new API projects, so if Google retires or restricts a model, change only `GEMINI_GENERATION_MODEL` in `.env`; re-indexing is not needed.

## Troubleshooting

- `No extractable text`: the PDF is likely scanned; OCR it, or use a DOCX/TXT export.
- Database function error: confirm that `supabase/schema.sql` completed and the vector dimension matches `.env`.
- Poor retrieval: include the full job description, re-index after updating resumes, and inspect the returned `sources` to see the exact evidence used.
