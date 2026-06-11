# 🚀 ResearchPilot AI

## LangGraph-Powered Agentic Research & Technical Documentation Assistant

ResearchPilot AI is an intelligent multi-agent research system that autonomously conducts web-based research, synthesizes information, leverages Retrieval-Augmented Generation (RAG), and generates professional technical reports in multiple formats.

Built using **LangGraph**, **Streamlit**, **PostgreSQL**, and **ChromaDB**, the project demonstrates modern Agentic AI workflows including planning, research, knowledge retrieval, report generation, persistence, and document export.

---

## ✨ Key Features

### Multi-Agent Architecture

* Planner Agent for research strategy generation
* Researcher Agent for web exploration and information gathering
* Writer Agent for report synthesis and document generation
* LangGraph-based orchestration for agent coordination

### Research & Knowledge Retrieval

* Real-time web research using DuckDuckGo
* Intelligent webpage content extraction and summarization
* Retrieval-Augmented Generation (RAG) using ChromaDB
* Knowledge persistence and retrieval across research sessions

### Document Generation

* Professional Markdown report generation
* PDF export support
* DOCX export support
* Structured technical documentation output

### Persistence & Tracking

* PostgreSQL-backed research history
* Metadata storage and tracking
* Research session management
* Historical report retrieval

### Reliability & LLM Management

* Gemini 2.5 Flash as primary model
* Groq-powered fallback mechanism
* Fault-tolerant LLM routing
* Configurable model providers

### User Experience

* Modern Streamlit interface
* Research dashboard
* History management
* Interactive workflow execution

---

# 🏗️ Architecture

<img width="1058" height="628" alt="image" src="https://github.com/user-attachments/assets/90ac013b-7a88-4401-816a-7728855a4195" />



---

# 📁 Project Structure

```bash
researchpilot-ai/
│
├── main.py
│
├── config/
│   └── settings.py
│
├── agents/
│   ├── base_agent.py
│   ├── planner.py
│   ├── researcher.py
│   ├── writer.py
│   └── langgraph_workflow.py
│
├── tools/
│   ├── search.py
│   └── document.py
│
├── core/
│   ├── llm.py
│   ├── prompts.py
│   └── state.py
│
├── rag/
│   └── vectorstore.py
│
├── database/
│   ├── connection.py
│   └── schema.py
│
├── output/
│
├── chroma_db/
│
├── .env.example
├── requirements.txt
└── README.md
```

---

# 🛠️ Tech Stack

| Category        | Technology                |
| --------------- | ------------------------- |
| Frontend        | Streamlit                 |
| Agent Framework | LangGraph                 |
| LLMs            | Gemini 2.5 Flash, Groq    |
| Vector Database | ChromaDB                  |
| Database        | PostgreSQL                |
| ORM             | SQLAlchemy                |
| Web Research    | DuckDuckGo, BeautifulSoup |
| PDF Export      | ReportLab                 |
| DOCX Export     | python-docx               |
| Language        | Python                    |

---

# ⚙️ Installation & Setup

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/researchpilot-ai.git

cd researchpilot-ai
```

## 2. Create Virtual Environment

```bash
python -m venv venv
```

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key

GROQ_API_KEY=your_groq_api_key

DATABASE_URL=postgresql://username:password@localhost:5432/researchpilot
```

## 5. Run PostgreSQL

Ensure PostgreSQL is running locally and the database has been created.

```sql
CREATE DATABASE researchpilot;
```

## 6. Launch the Application

```bash
streamlit run main.py
```

---

# 🔄 Workflow

1. User submits a research topic and objectives.
2. Planner Agent creates a structured research strategy.
3. Researcher Agent gathers information from web sources.
4. Research findings are stored and indexed.
5. Writer Agent retrieves relevant context from ChromaDB.
6. Writer Agent generates a comprehensive report.
7. Research history is persisted in PostgreSQL.
8. Final output is exported as Markdown, PDF, or DOCX.

---

# 🎯 Use Cases

* Technical research automation
* AI and technology trend analysis
* Academic literature exploration
* Industry and market research
* Documentation generation
* Knowledge management systems
* Agentic AI experimentation

---

# 🗺️ Roadmap

## Phase 1 — Completed ✅

* Multi-Agent LangGraph Workflow
* Planner, Researcher, Writer Agents
* PostgreSQL Integration
* ChromaDB RAG
* PDF Export
* DOCX Export
* Streamlit Dashboard
* Research History Tracking

## Phase 2 — In Progress 🚧

* Human-in-the-Loop Approvals
* Reviewer/Critic Agent
* Advanced RAG Pipeline
* Query Expansion
* Reranking
* Research Caching Layer

## Phase 3 — Future Enhancements 🔮

* Docker Deployment
* Docker Compose
* FastAPI Backend
* LangSmith Observability
* OpenTelemetry Tracing
* User Authentication
* Multi-User Support
* GitHub Integration
* ArXiv Integration
* Automated Evaluation Metrics
* LLM-as-a-Judge Framework

---

# 🌟 What Makes This Project Stand Out

* Demonstrates real-world Agentic AI architecture
* Implements LangGraph orchestration patterns
* Combines AI Engineering and Data Engineering
* Includes Retrieval-Augmented Generation (RAG)
* Uses persistent storage with PostgreSQL
* Supports production-style report generation
* Features modular and scalable architecture
* Showcases end-to-end AI application development

---

# 👩‍💻 Author

**Maheshwaree Talekar**

Aspiring AI Engineer | Machine Learning Enthusiast | Generative AI Developer

* LinkedIn: https://www.linkedin.com/in/maheshwaree-talekar-88862b307
* GitHub: https://github.com/Maheshwaree-02

---

## License

This project is licensed under the MIT License.

Feel free to fork, modify, and build upon this work for educational and research purposes.
