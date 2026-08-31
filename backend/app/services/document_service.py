import pymupdf
from typing import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class PageChunk:
    page_number: int
    chapter: str | None
    section: str | None
    content: str


class DocumentService:
    """Service for parsing and chunking PDF documents."""

    def parse_pdf(self, file_path: str) -> Iterator[PageChunk]:
        """Parse PDF and yield chunks for each page."""
        doc = pymupdf.open(file_path)

        current_chapter = None
        current_section = None

        for page_num, page in enumerate(doc, start=1):
            text = page.get_text()

            lines = text.split("\n")
            clean_lines = [l.strip() for l in lines if l.strip()]

            if clean_lines:
                first_line = clean_lines[0]
                if len(first_line) < 100 and first_line.isupper():
                    current_chapter = first_line

                content = "\n".join(clean_lines[1:]) if len(clean_lines) > 1 else text

            yield PageChunk(
                page_number=page_num,
                chapter=current_chapter,
                section=current_section,
                content="\n".join(clean_lines[1:]) if len(clean_lines) > 1 else text,
            )

        doc.close()

    def chunk_text(self, text: str, max_chars: int = 2000) -> list[str]:
        """Split text into smaller chunks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) < max_chars:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks


def get_document_service() -> DocumentService:
    return DocumentService()
