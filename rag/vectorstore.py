"""ChromaDB-based RAG for storing and retrieving past research."""
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL
from rag.chunker import SemanticChunker
import os
import logging
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

logger = logging.getLogger(__name__)

# Lazy-loaded singleton instances
_embeddings = None
_vectorstore = None
_chunker = SemanticChunker(chunk_size=500, overlap=50)


def _get_embeddings():
    """Get or create singleton embeddings model."""
    global _embeddings
    if _embeddings is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={'device': 'cpu'}
        )
    return _embeddings


def get_vectorstore():
    """Get or create singleton Chroma vectorstore."""
    global _vectorstore
    if _vectorstore is None:
        os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        _vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=_get_embeddings(),
            collection_name="researchpilot_docs"
        )
    return _vectorstore


def add_research_to_rag(text: str, metadata: dict):
    """Store research content in RAG with semantic chunking.
    
    Args:
        text: Full research text to store (up to 5000 chars used).
        metadata: Metadata dict with topic, timestamp, etc.
    """
    try:
        vectorstore = get_vectorstore()
        
        # Chunk the content semantically
        chunks = _chunker.chunk_text(text[:5000], metadata)
        
        if not chunks:
            # Fallback: store as single document
            vectorstore.add_texts(
                texts=[text[:2000]],
                metadatas=[metadata]
            )
            logger.info(f"RAG stored (single doc): {metadata.get('topic', 'Unknown')}")
            return
        
        texts = [c["text"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        vectorstore.add_texts(texts=texts, metadatas=metadatas)
        logger.info(f"RAG stored {len(chunks)} chunks: {metadata.get('topic', 'Unknown')}")
        
    except Exception as e:
        logger.warning(f"RAG storage failed: {e}")


def retrieve_context(query: str, k: int = 3, score_threshold: float = 0.3) -> str:
    """Retrieve relevant past research from RAG.
    
    Args:
        query: Search query (typically the research topic).
        k: Number of results to retrieve.
        score_threshold: Minimum similarity score (0-1, lower = more similar for L2).
        
    Returns:
        Formatted context string for the Writer prompt.
    """
    try:
        vectorstore = get_vectorstore()
        
        # Use similarity_search_with_score for relevance filtering
        results = vectorstore.similarity_search_with_score(query, k=k)
        
        if not results:
            return ""
        
        # Filter by relevance (lower score = more similar for L2 distance)
        relevant_docs = [(doc, score) for doc, score in results if score < 1.5]
        
        if not relevant_docs:
            logger.info("RAG: No sufficiently relevant documents found")
            return ""
        
        logger.info(f"RAG: Retrieved {len(relevant_docs)} relevant documents")
        
        context = "\n\n**RELEVANT PAST RESEARCH**\n"
        for i, (doc, score) in enumerate(relevant_docs, 1):
            topic = doc.metadata.get('topic', 'Previous Research')
            section = doc.metadata.get('section', '')
            section_str = f" ({section})" if section else ""
            context += f"\n**{i}. {topic}{section_str}** (relevance: {1 - score/2:.0%})\n"
            context += doc.page_content[:1000] + "\n\n"
        
        return context
        
    except Exception as e:
        logger.warning(f"RAG retrieval failed: {e}")
        return ""