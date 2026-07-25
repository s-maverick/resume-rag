import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
    elif suffix == ".docx":
        text = "\n".join(p.text for p in Document(str(path)).paragraphs)
    elif suffix in {".txt", ".md"}:
        text = path.read_text(encoding="utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported resume type: {path.suffix}")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def chunk_text(text: str, chunk_size: int = 1200, overlap: int = 200) -> list[str]:
    """Split on whitespace while keeping useful overlap between adjacent chunks."""
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    current: list[str] = []
    current_length = 0
    for word in words:
        next_length = current_length + len(word) + (1 if current else 0)
        if current and next_length > chunk_size:
            chunks.append(" ".join(current))
            overlap_words: list[str] = []
            overlap_length = 0
            for item in reversed(current):
                if overlap_length + len(item) + 1 > overlap:
                    break
                overlap_words.insert(0, item)
                overlap_length += len(item) + 1
            current, current_length = overlap_words, sum(len(x) + 1 for x in overlap_words)
        current.append(word)
        current_length += len(word) + (1 if len(current) > 1 else 0)
    if current:
        chunks.append(" ".join(current))
    return chunks

