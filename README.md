# 🚀 ResearchPilot AI

**LangGraph-Powered Agentic Research & Technical Documentation Assistant**

An intelligent multi-agent system that autonomously conducts deep research, leverages RAG for knowledge retention, incorporates human oversight, and produces high-quality technical reports.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge&logo=postgresql&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-6B46C0?style=for-the-badge)

---

## ✨ Key Features

### Agentic Architecture
- **LangGraph** orchestrated multi-agent workflow
- **Planner Agent** — Breaks down topics into structured research plans
- **Researcher Agent** — Performs real-time web research and synthesis
- **Writer Agent** — Generates professional, well-structured reports
- **Reviewer Agent** — Provides critical feedback and quality scoring

### Core Capabilities
- **Human-in-the-Loop** approvals for research plans and final drafts
- **Retrieval-Augmented Generation (RAG)** with ChromaDB for knowledge retention across sessions
- Real-time web research using DuckDuckGo + page browsing
- Persistent research history with PostgreSQL
- Professional document generation (Markdown, PDF, DOCX)

### User Experience
- Modern, intuitive Streamlit interface
- Interactive workflow with progress tracking
- Research history dashboard with quick access to past reports
- One-click exports and report regeneration

---

## Architecture
![alt text](<Screenshot 2026-06-11 130856.png>)

📁 Project Structure
Bashresearchpilot-ai/
├── main.py                          # Streamlit UI + Orchestration
├── config/
│   └── settings.py
├── agents/
│   ├── base_agent.py
│   ├── planner.py
│   ├── researcher.py
│   ├── writer.py
│   ├── reviewer.py
│   └── langgraph_workflow.py
├── tools/
│   ├── search.py
│   └── document.py
├── core/
│   ├── llm.py
│   ├── prompts.py
│   └── state.py
├── rag/
│   └── vectorstore.py
├── database/
│   ├── connection.py
│   └── schema.py
├── output/                          # Generated reports
├── chroma_db/                       # ChromaDB persistence
├── .env.example
├── requirements.txt
└── README.md

🛠️ Tech Stack









































CategoryTechnologyFrontendStreamlitAgent FrameworkLangGraphLLMsGemini 2.5 Flash + Groq (Fallback)Vector StoreChromaDB (RAG)DatabasePostgreSQL + SQLAlchemyWeb ResearchDuckDuckGo + BeautifulSoupDocument ExportReportLab + python-docxCachingSession State + Hash-based

⚙️ Installation & Setup
Bashgit clone https://github.com/yourusername/researchpilot-ai.git
cd researchpilot-ai

# Create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
Configure .env:
envGEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
DATABASE_URL=postgresql://postgres:password@localhost:5432/researchpilot
Then run:
Bashstreamlit run main.py

🔄 Workflow

User submits topic and goals
Planner Agent creates structured plan → Human Approval
Researcher Agent gathers information from web + RAG
Writer Agent synthesizes findings into report
Reviewer Agent provides critical feedback and scoring
User reviews/edits draft → Final Approval
Report saved to history + exported as PDF/DOCX/Markdown


🎯 What Makes This Project Stand Out

Real multi-agent orchestration using LangGraph
Human-in-the-Loop design for reliability and control
Persistent RAG across research sessions
Professional reviewer agent for quality control
Clean architecture with modular design
Strong blend of AI Engineering and Data Engineering


🗺️ Roadmap
Phase 1 — Completed ✅

Multi-Agent LangGraph Workflow
PostgreSQL + ChromaDB RAG
Streamlit Dashboard + History
PDF/DOCX Export

Phase 2 — Completed ✅

Human-in-the-Loop Approvals
Reviewer/Critic Agent
Advanced RAG (Query Expansion + Reranking)
Research Caching Layer

Phase 3 — In Progress / Next

Docker + docker-compose deployment
LLM-as-Judge automated evaluation
Advanced observability & logging
Research versioning and comparison

Phase 4 — Future

FastAPI Backend + Authentication
Multi-user & Collaboration
Knowledge Graph
ArXiv & GitHub integration


👩‍💻 Author
Your Name
B.Tech Information Technology | CGPA: 9.57
Aspiring AI & Software Development Engineer

License: MIT