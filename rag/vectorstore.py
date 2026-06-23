# rag/vectorstore.py
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL
import os
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="transformers")

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs={'device': 'cpu'}
)

def get_vectorstore():
    os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
    return Chroma(
        persist_directory=CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="researchpilot_docs"
    )


def add_research_to_rag(text: str, metadata: dict):
    try:
        vectorstore = get_vectorstore()
        vectorstore.add_texts(
            texts=[text[:2500]],   # Further reduced
            metadatas=[metadata]
        )
        print(f"✅ RAG Stored: {metadata.get('topic', 'Unknown')}")
    except Exception as e:
        print(f"⚠️ RAG storage failed: {e}")


def retrieve_context(query: str, k: int = 2):   # Reduced to 2
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=k)
        
        if not docs:
            return ""
            
        print(f"✅ RAG: Retrieved {len(docs)} documents")
        
        context = "\n\n**RELEVANT PAST RESEARCH (Context Compressed)**\n"
        for i, doc in enumerate(docs, 1):
            topic = doc.metadata.get('topic', 'Previous Research')
            context += f"\n**{i}. {topic}**\n"
            context += doc.page_content[:600] + "\n\n"   # Strongly reduced
        return context
    except Exception as e:
        print(f"⚠️ RAG retrieval failed: {e}")
        return ""