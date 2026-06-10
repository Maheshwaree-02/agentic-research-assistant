# ResearchPilot AI

**Agentic Research & Technical Documentation Assistant**  
Built with LangGraph, Gemini + Groq, PostgreSQL & PGVector

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge)

## ✨ Features

- **Multi-Agent System** powered by **LangGraph**
- Planner → Researcher → Writer workflow
- Real-time web research with DuckDuckGo
- PostgreSQL + PGVector (RAG)
- Professional report generation (Markdown, PDF, DOCX)
- Research history dashboard
- Gemini (Primary) + Groq (Backup)

## Tech Stack

- **Frontend**: Streamlit
- **Agent Framework**: LangGraph
- **LLMs**: Gemini 2.5 + Groq (Llama 3.1)
- **Database**: PostgreSQL + PGVector
- **ORM**: SQLAlchemy
- **RAG**: LangChain + HuggingFace Embeddings
- **Export**: ReportLab + python-docx

## Screenshots

*(Add screenshots here after running the app)*

## How to Run

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd researchpilot-ai

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env
# Add your GEMINI_API_KEY and GROQ_API_KEY

# 4. Setup PostgreSQL
# Create database 'researchpilot' and run the app (it will init tables)

# 5. Run
streamlit run main.py
