import streamlit as st
from dotenv import load_dotenv
import os

from core.llm import get_llm_client
from core.state import AgentState
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.writer import WriterAgent
from agents.langgraph_workflow import create_research_graph   # ← New Import
from tools.document import save_as_pdf, save_as_docx
from database.connection import init_db, get_db
from core.history import save_to_history, load_history

load_dotenv()

# Initialize Database
init_db()

st.set_page_config(page_title="ResearchPilot AI", layout="wide", page_icon="🔬")

# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("📖 ResearchPilot AI")
    st.caption("Agentic Research Assistant")
    
    st.divider()
    st.subheader("📜 Recent Researches")
    
    try:
        db = next(get_db())
        history = load_history(db, limit=8)
        for entry in history:
            if st.button(f"📌 {entry.topic[:45]}...", key=f"hist_{entry.id}"):
                st.session_state.selected_report = entry.id
    except:
        st.warning("Database not connected")

    st.divider()
    st.info("🗄️ PostgreSQL Connected\nLangGraph + Gemini | Groq Backup")

# ====================== MAIN UI ======================
st.title("🔬 ResearchPilot AI")
st.markdown("**LangGraph-Powered Multi-Agent Research System**")

tab1, tab2 = st.tabs(["🚀 New Research", "📚 History"])

with tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Research Topic", placeholder="Agentic AI with LangGraph and Multi-Agent Systems")
    with col2:
        depth = st.selectbox("Research Depth", ["Quick", "Medium", "Deep"], index=1)

    goals = st.text_area("Specific Goals / Questions", height=130,
                         placeholder="Architecture, pros & cons, code examples, latest developments...")

    if st.button("🚀 Start LangGraph Research", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a research topic")
        else:
            try:
                with st.spinner("🚀 Initializing LangGraph Workflow..."):
                    graph = create_research_graph()
                    
                    initial_state = {
                        "topic": topic.strip(),
                        "goals": goals or "Comprehensive technical research",
                        "plan": None,
                        "findings": [],
                        "draft": None,
                        "messages": [],
                        "next": "planner"
                    }

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    # Run the LangGraph
                    result = graph.invoke(initial_state)

                    progress_bar.progress(100)
                    status_text.success("✅ LangGraph Workflow Completed Successfully!")

                    # Convert to AgentState
                    state = AgentState(
                        topic=result["topic"],
                        goals=result.get("goals"),
                        plan=result.get("plan"),
                        findings=result.get("findings", []),
                        draft=result.get("draft")
                    )

                    # Save to PostgreSQL
                    db = next(get_db())
                    save_to_history(db, state, topic, "langgraph")

                    # ====================== DISPLAY REPORT ======================
                    st.divider()
                    st.subheader(f"📄 Final Report: {topic}")
                    
                    if state.draft:
                        st.markdown(state.draft)
                    else:
                        st.warning("Draft generation failed. Please try again.")

                    # ====================== DOWNLOADS ======================
                    st.divider()
                    st.subheader("📤 Export Report")
                    col_dl1, col_dl2, col_dl3 = st.columns(3)

                    with col_dl1:
                        st.download_button(
                            "📥 Markdown", 
                            state.draft or "# No content generated",
                            f"{topic.replace(' ', '_')}_report.md", 
                            mime="text/markdown"
                        )

                    with col_dl2:
                        pdf_path = f"output/{topic.replace(' ', '_')}_report.pdf"
                        os.makedirs("output", exist_ok=True)
                        save_as_pdf(state.draft or "# Empty Report", pdf_path)
                        with open(pdf_path, "rb") as f:
                            st.download_button("📕 PDF", f, 
                                             f"{topic.replace(' ', '_')}_report.pdf", 
                                             mime="application/pdf")

                    with col_dl3:
                        docx_path = f"output/{topic.replace(' ', '_')}_report.docx"
                        save_as_docx(state.draft or "# Empty Report", docx_path)
                        with open(docx_path, "rb") as f:
                            st.download_button("📘 DOCX", f, 
                                             f"{topic.replace(' ', '_')}_report.docx", 
                                             mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

                    # Sources
                    if state.findings:
                        with st.expander("📚 Sources Used"):
                            for finding in state.findings:
                                st.markdown(f"**{finding.get('question', 'N/A')}**")
                                if finding.get("sources"):
                                    for src in finding["sources"][:3]:
                                        st.caption(f"• [{src.get('title', 'Source')}]({src.get('link', '#')})")

            except Exception as e:
                st.error(f"❌ Error during LangGraph execution: {str(e)}")
                st.info("💡 Make sure `agents/langgraph_workflow.py` exists and all dependencies are installed.")

# ====================== HISTORY TAB ======================
with tab2:
    st.subheader("📚 All Previous Researches")
    try:
        db = next(get_db())
        all_history = load_history(db, limit=20)
        
        if all_history:
            for entry in all_history:
                with st.expander(f"📅 {entry.timestamp.strftime('%Y-%m-%d %H:%M')} — {entry.topic}"):
                    st.write((entry.draft[:800] + "...") if entry.draft else "No content available")
                    st.caption(f"LLM Used: {entry.llm_used} | Findings: {len(entry.findings)}")
        else:
            st.info("No researches found yet. Start your first research!")
    except Exception as e:
        st.error("Could not load history from database.")

st.sidebar.info("LangGraph Enabled • Built for AI & Software Engineering Internship")