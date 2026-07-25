"""Index every supported resume under resumes/. Run after adding or changing a resume."""
from pathlib import Path

from app.services import ResumeRAG
from app.text import SUPPORTED_EXTENSIONS, chunk_text, extract_text

RESUMES_DIR = Path(__file__).parent / "resumes"


def main() -> None:
    files = sorted(p for p in RESUMES_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS)
    if not files:
        raise SystemExit("No .pdf, .docx, .txt, or .md resumes found in resumes/.")
    rag = ResumeRAG()
    total = 0
    for path in files:
        text = extract_text(path)
        chunks = chunk_text(text)
        if not chunks:
            print(f"Skipped {path.name}: no extractable text")
            continue
        count = rag.replace_resume(path.name, chunks)
        total += count
        print(f"Indexed {path.name}: {count} chunks")
    print(f"Done. Indexed {total} chunks from {len(files)} resume file(s).")


if __name__ == "__main__":
    main()

