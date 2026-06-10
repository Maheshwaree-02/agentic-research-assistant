import os
from dotenv import load_dotenv

load_dotenv()

# ====================== LLM CONFIG ======================
PRIMARY_LLM = "gemini"                    # Change to "groq" if you prefer
GEMINI_MODEL = "gemini-2.5-flash-lite"    # Good for free tier
GROQ_MODEL = "llama-3.1-70b-versatile"

# ====================== DATABASE CONFIG ======================
DATABASE_URL = os.getenv("DATABASE_URL")

# Fallback if not set in .env
if not DATABASE_URL:
    DATABASE_URL = "postgresql://postgres:password@localhost:5432/researchpilot"
    print("⚠️  DATABASE_URL not found in .env → Using fallback")

# RAG Configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
VECTOR_COLLECTION_NAME = "researchpilot_documents"

USE_MOCK = False         # ← Set this to True for now