# 🚀 ResearchPilot AI

**LangGraph-Powered Agentic Research & Technical Documentation Assistant**

ResearchPilot AI is an intelligent multi-agent system that autonomously conducts deep research, leverages Retrieval-Augmented Generation (RAG) for knowledge retention, incorporates human oversight, and generates high-quality technical reports.

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-FF6F00?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?style=for-the-badge\&logo=postgresql\&logoColor=white)
![ChromaDB](https://img.shields.io/badge/ChromaDB-6B46C0?style=for-the-badge)

---

## 📌 Overview

ResearchPilot AI is a production-inspired research assistant that combines Agentic AI, LangGraph workflows, RAG, and Human-in-the-Loop validation to automate technical research and documentation generation.

The platform enables users to generate structured research reports while maintaining quality, transparency, and user control throughout the workflow.

---

## ✨ Key Features

### 🤖 Multi-Agent Architecture

* **Planner Agent** – Creates structured research plans
* **Researcher Agent** – Performs web research and information synthesis
* **Writer Agent** – Generates professional reports
* **Reviewer Agent** – Critiques and scores report quality
* **LangGraph Workflow** – Orchestrates agent interactions

### 🧠 AI & Knowledge Management

* Retrieval-Augmented Generation (RAG)
* Persistent knowledge retention using ChromaDB
* Query-aware contextual retrieval
* Research history and memory management

### 👨‍💻 Human-in-the-Loop

* Research plan approval
* Draft review and editing
* Final report approval
* Improved reliability and transparency

### 📄 Report Generation

* Markdown Export
* PDF Export
* DOCX Export
* Research History Tracking

---

## 🏗️ System Architecture

![ResearchPilot Architecture](docs/architecture.png)

### Workflow

```text
User Query
    │
    ▼
Planner Agent
    │
    ▼
Human Approval
    │
    ▼
Research Agent
    │
    ├── Web Search
    └── RAG Retrieval
    │
    ▼
Writer Agent
    │
    ▼
Reviewer Agent
    │
    ▼
Human Review
    │
    ▼
Final Report Generation
```

---

## 📁 Project Structure

```text
researchpilot-ai/
│
├── agents/
│   ├── base_agent.py
│   ├── planner.py
│   ├── researcher.py
│   ├── reviewer.py
│   ├── writer.py
│   └── langgraph_workflow.py
│
├── core/
│   ├── llm.py
│   ├── prompts.py
│   ├── state.py
│   └── history.py
│
├── tools/
│   ├── search.py
│   └── document.py
│
├── rag/
│   └── vectorstore.py
│
├── database/
│   ├── connection.py
│   └── schema.py
│
├── config/
│   └── settings.py
│
├── frontend/
│
├── output/
│
├── main.py
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Category            | Technology                |
| ------------------- | ------------------------- |
| Frontend            | Streamlit                 |
| Agent Framework     | LangGraph                 |
| LLMs                | Gemini 2.5 Flash, Groq    |
| Vector Database     | ChromaDB                  |
| Database            | PostgreSQL, SQLAlchemy    |
| Research Engine     | DuckDuckGo, BeautifulSoup |
| Document Generation | ReportLab, python-docx    |
| Language            | Python                    |

---

## ⚙️ Installation

### Clone Repository

```bash
git clone https://github.com/Maheshwaree-02/agentic-research-assistant.git

cd agentic-research-assistant
```

### Create Virtual Environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/researchpilot
```

---

## ▶️ Running the Application

```bash
streamlit run main.py
```

---

## 🔄 End-to-End Workflow

1. User submits research topic
2. Planner Agent generates research plan
3. User approves plan
4. Research Agent gathers information
5. RAG retrieves relevant context
6. Writer Agent drafts report
7. Reviewer Agent evaluates quality
8. User reviews final draft
9. Report exported as PDF/DOCX/Markdown

---

## 🎯 Why This Project Stands Out

### AI Engineering

* Multi-Agent AI Architecture
* LangGraph Workflow Orchestration
* Human-in-the-Loop AI Systems
* Retrieval-Augmented Generation

### Data Engineering

* PostgreSQL Integration
* Vector Database Architecture
* Persistent Research History
* Modular Pipeline Design

### Software Engineering

* Clean Project Structure
* Extensible Agent Framework
* Production-Oriented Design
* Export & Persistence Layers

---

## 🗺️ Roadmap

### Phase 1 ✅

* Multi-Agent Workflow
* LangGraph Integration
* PostgreSQL Persistence
* ChromaDB RAG
* Streamlit Dashboard

### Phase 2 ✅

* Human-in-the-Loop Approvals
* Reviewer Agent
* Advanced Retrieval
* Research Caching

### Phase 3 🚧

* Docker Deployment
* LLM-as-a-Judge Evaluation
* Monitoring & Logging
* Versioned Research Sessions

### Phase 4 🔮

* FastAPI Backend
* React Frontend
* Authentication
* Multi-User Support
* Knowledge Graph Integration
* GitHub & ArXiv Connectors

---

## 📊 Future Enhancements

* Agent Evaluation Framework
* Multi-LLM Routing
* Cost Optimization Layer
* Research Benchmarking
* Automated Citation Validation

---

## 👩‍💻 Author

**Maheshwaree Talekar**

B.Tech Information Technology (2027)
CGPA: 9.57

Interests:

* AI Engineering
* Agentic AI Systems
* Data Engineering
* Machine Learning
* Software Development

---

## 📜 License

MIT License
