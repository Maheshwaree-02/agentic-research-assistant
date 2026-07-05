# ResearchPilot AI

![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)

ResearchPilot AI is a production-inspired, multi-agent AI research assistant. It autonomously conducts deep-dive technical research, synthesizes findings into professional reports with inline citations, and retains past knowledge using Retrieval-Augmented Generation (RAG).

## 🚀 Key Features

*   **Multi-Agent Architecture**: Specialized agents for Planning, Researching, Writing, and Reviewing.
*   **Human-in-the-Loop (HITL)**: Users can review, edit, and approve the AI-generated research plan before execution.
*   **Advanced RAG Memory**: Utilizes ChromaDB and semantic chunking to recall past research for context.
*   **Citation Management**: Automatically tracks sources, generates inline citations `[1]`, and builds a bibliography.
*   **LLM-as-a-Judge**: A Reviewer agent objectively scores the final report across multiple dimensions (Depth, Accuracy, Clarity, etc.).
*   **Dynamic LLM Routing**: Primary Gemini 2.5 Flash models with fallback to Groq LLaMA 3.3 70B and built-in rate-limit handling.
*   **Beautiful UI**: A polished Streamlit interface featuring a dark theme, glassmorphism, agent progress visualization, and rich export options (Markdown, PDF, DOCX).

## 📋 Prerequisites

*   Python 3.10+
*   PostgreSQL running locally or remotely
*   API Keys for Gemini (Google AI Studio) and optionally Groq.

## 🛠️ Setup & Installation

1.  **Clone the repository**
    ```bash
    git clone https://github.com/yourusername/researchpilot-ai.git
    cd researchpilot-ai
    ```

2.  **Set up a virtual environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory:
    ```ini
    DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/researchpilot
    GEMINI_API_KEY=your_gemini_api_key_here
    GROQ_API_KEY=your_groq_api_key_here
    LOG_LEVEL=INFO
    ```

5.  **Initialize the Database**
    Run this command to create the necessary PostgreSQL tables:
    ```bash
    python -c "from database.connection import init_db; init_db()"
    ```

6.  **Run the Application**
    ```bash
    streamlit run main.py
    ```

## 🧠 How It Works

1.  **Input**: You provide a research topic, optional goals, and select a depth level (Quick, Medium, Deep).
2.  **Planning**: The **PlannerAgent** generates a set of targeted research questions.
3.  **Approval**: You review and modify the questions in the UI.
4.  **Researching**: The **ResearchAgent** queries the web, browses pages, and synthesizes answers for each question, tracking sources via the `CitationManager`.
5.  **Writing**: The **WriterAgent** pulls past knowledge from the RAG vectorstore, combines it with current findings, and drafts a comprehensive report with inline citations and a bibliography.
6.  **Reviewing**: The **ReviewerAgent** evaluates the draft, providing a structured score and actionable feedback.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
