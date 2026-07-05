import os
from dotenv import load_dotenv

load_dotenv()

# ====================== LLM CONFIG ======================
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_MODEL_QUALITY = "gemini-2.5-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

USE_MOCK = False

# ====================== DEPTH CONFIG ======================
RESEARCH_DEPTH_CONFIG = {
    "Quick": {"max_questions": 3, "max_search_results": 3, "max_browse_pages": 1, "max_tokens": 3000},
    "Medium": {"max_questions": 5, "max_search_results": 4, "max_browse_pages": 2, "max_tokens": 5000},
    "Deep": {"max_questions": 8, "max_search_results": 5, "max_browse_pages": 3, "max_tokens": 8000},
}

# ====================== DATABASE CONFIG ======================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/researchpilot"
    print("⚠️  DATABASE_URL not found in .env → Using fallback")

# ====================== RAG CONFIG ======================
CHROMA_PERSIST_DIRECTORY = "./chroma_db"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# ====================== LOGGING ======================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")