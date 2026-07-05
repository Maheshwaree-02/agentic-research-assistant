"""Semantic text chunking for RAG storage."""
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Splits research content into semantically meaningful chunks for RAG.
    
    Preserves document structure by splitting on Markdown headings first,
    then paragraphs, with configurable chunk size and overlap.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        """Initialize chunker.
        
        Args:
            chunk_size: Target chunk size in characters.
            overlap: Number of characters to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Split text into chunks preserving section context.
        
        Args:
            text: The full text to chunk.
            metadata: Base metadata to include with each chunk.
            
        Returns:
            List of dicts with 'text' and 'metadata' keys.
        """
        if not text or not text.strip():
            return []

        base_metadata = metadata or {}
        sections = self._split_by_sections(text)
        chunks = []

        for section_title, section_content in sections:
            if not section_content.strip():
                continue

            section_meta = {**base_metadata, "section": section_title}

            if len(section_content) <= self.chunk_size:
                chunks.append({
                    "text": section_content.strip(),
                    "metadata": {**section_meta, "chunk_index": len(chunks)}
                })
            else:
                # Split long sections into paragraphs, then merge into chunks
                paragraphs = self._split_by_paragraphs(section_content)
                para_chunks = self._merge_paragraphs(paragraphs)

                for para_chunk in para_chunks:
                    chunks.append({
                        "text": para_chunk.strip(),
                        "metadata": {**section_meta, "chunk_index": len(chunks)}
                    })

        logger.info(f"Chunked text into {len(chunks)} chunks (avg {sum(len(c['text']) for c in chunks) // max(len(chunks), 1)} chars)")
        return chunks

    def _split_by_sections(self, text: str) -> List[tuple]:
        """Split text by Markdown headings into (title, content) pairs."""
        # Match ## or ### headings
        pattern = r'^(#{1,3}\s+.+)$'
        parts = re.split(pattern, text, flags=re.MULTILINE)

        sections = []
        current_title = "Introduction"
        current_content = ""

        for part in parts:
            if re.match(r'^#{1,3}\s+', part.strip()):
                # Save previous section
                if current_content.strip():
                    sections.append((current_title, current_content))
                current_title = part.strip().lstrip('#').strip()
                current_content = ""
            else:
                current_content += part

        # Save last section
        if current_content.strip():
            sections.append((current_title, current_content))

        # If no sections found, return entire text as one section
        if not sections:
            sections = [("Full Content", text)]

        return sections

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs (by double newline or single newline with content)."""
        paragraphs = re.split(r'\n\s*\n', text)
        result = []
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 20:  # Skip tiny fragments
                result.append(para)
        return result if result else [text.strip()]

    def _merge_paragraphs(self, paragraphs: List[str]) -> List[str]:
        """Merge small paragraphs into chunks of target size."""
        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk += ("\n\n" + para) if current_chunk else para
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If single paragraph exceeds chunk size, add it as-is
                if len(para) > self.chunk_size:
                    chunks.append(para[:self.chunk_size])
                    # Add remainder with overlap
                    if len(para) > self.chunk_size - self.overlap:
                        current_chunk = para[self.chunk_size - self.overlap:]
                    else:
                        current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunks.append(current_chunk)

        return chunks
