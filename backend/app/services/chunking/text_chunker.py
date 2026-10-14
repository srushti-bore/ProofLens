"""
Configurable semantic chunking service.
Splits document pages into semantically cohesive chunks while preserving exact page provenance.
"""

import re
from dataclasses import dataclass
from typing import Any, List


@dataclass
class ChunkData:
    page_number: int  # 1-indexed source page
    chunk_index: int  # Sequential index within document
    content: str
    char_count: int


def split_text_into_chunks(
    text: str,
    page_number: int,
    start_chunk_idx: int,
    max_chunk_chars: int = 2400,  # ~600 tokens
    overlap_chars: int = 400,      # ~100 tokens
) -> List[ChunkData]:
    """
    Split text of a single page into overlapping chunks respecting paragraph boundaries.
    """
    text = text.strip()
    if not text:
        return []

    # If text is small enough, return as single chunk
    if len(text) <= max_chunk_chars:
        return [
            ChunkData(
                page_number=page_number,
                chunk_index=start_chunk_idx,
                content=text,
                char_count=len(text),
            )
        ]

    # Split by double newline (paragraphs) or single newline
    paragraphs = re.split(r"(\n\s*\n)", text)
    chunks: List[ChunkData] = []
    current_text = ""
    current_idx = start_chunk_idx

    for segment in paragraphs:
        if not segment.strip():
            continue

        if len(current_text) + len(segment) <= max_chunk_chars:
            current_text += ("\n\n" if current_text else "") + segment.strip()
        else:
            if current_text:
                chunks.append(
                    ChunkData(
                        page_number=page_number,
                        chunk_index=current_idx,
                        content=current_text,
                        char_count=len(current_text),
                    )
                )
                current_idx += 1
                # Retain overlap from end of previous chunk
                if len(current_text) > overlap_chars:
                    current_text = current_text[-overlap_chars:].strip() + "\n\n" + segment.strip()
                else:
                    current_text = segment.strip()
            else:
                # Segment itself is larger than max_chunk_chars: split by sentence
                sentences = re.split(r"(?<=[.!?])\s+", segment)
                for s in sentences:
                    if len(current_text) + len(s) <= max_chunk_chars:
                        current_text += (" " if current_text else "") + s.strip()
                    else:
                        if current_text:
                            chunks.append(
                                ChunkData(
                                    page_number=page_number,
                                    chunk_index=current_idx,
                                    content=current_text,
                                    char_count=len(current_text),
                                )
                            )
                            current_idx += 1
                        current_text = s.strip()

    if current_text.strip():
        chunks.append(
            ChunkData(
                page_number=page_number,
                chunk_index=current_idx,
                content=current_text.strip(),
                char_count=len(current_text.strip()),
            )
        )

    return chunks


def chunk_document_pages(
    pages: List[Any],
    max_chunk_chars: int = 2400,
    overlap_chars: int = 400,
) -> List[ChunkData]:
    """
    Process all pages of a document and return an ordered list of chunks with global index.
    """
    all_chunks: List[ChunkData] = []
    current_chunk_idx = 0

    for page in pages:
        page_num = getattr(page, "page_number", None) or page["page_number"]
        page_text = getattr(page, "text_content", None) or page.get("text_content", "")

        page_chunks = split_text_into_chunks(
            text=page_text,
            page_number=page_num,
            start_chunk_idx=current_chunk_idx,
            max_chunk_chars=max_chunk_chars,
            overlap_chars=overlap_chars,
        )
        all_chunks.extend(page_chunks)
        current_chunk_idx += len(page_chunks)

    return all_chunks
