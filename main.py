import streamlit as st
from dotenv import load_dotenv
import os
import hashlib
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

from core.llm import get_llm_client
from core.state import AgentState
from agents.langgraph_workflow import create_research_graph
from tools.document import save_as_pdf, save_as_docx
from database.connection import init_db, get_db
from database.schema import Research
from core.history import save_to_history, load_history

load_dotenv()

init_db()

st.set_page_config(page_title="ResearchPilot AI", layout="wide", page_icon="🔬")

# ====================== SESSION STATE ======================
if "research_cache" not in st.session_state:
    st.session_state.research_cache = {}
if "current_research" not in st.session_state:
    st.session_state.current_research = None
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "new"

# ====================== SIDEBAR ======================
with st.sidebar:
    st.title("📖 ResearchPilot AI")
    st.caption("Agentic Research Assistant")
    
    st.divider()
    st.subheader("📜 Research History")
    
    try:
        db = next(get_db())
        history = load_history(db, limit=15)
        for entry in history:
            if st.button(f"📌 {entry.topic[:45]}...", key=f"hist_{entry.id}"):
                st.session_state.selected_report = entry.id
                st.session_state.view_mode = "history"
    except:
        st.warning("Database not connected")

    st.divider()
    if st.button("🆕 New Research", use_container_width=True):
        st.session_state.view_mode = "new"
        st.session_state.current_research = None

    st.info("🗄️ PostgreSQL • ChromaDB RAG\nGemini + Groq")

# ====================== MAIN AREA ======================
st.title("🔬 ResearchPilot AI")
st.markdown("**LangGraph Multi-Agent Research System with Human-in-the-Loop & Reviewer**")

# ====================== HISTORY VIEW ======================
if st.session_state.get("view_mode") == "history" and st.session_state.get("selected_report"):
    try:
        db = next(get_db())
        report = db.query(Research).filter(Research.id == st.session_state.selected_report).first()
        if report:
            st.subheader(f"📄 {report.topic}")
            st.caption(f"Generated: {report.timestamp}")
            st.markdown(report.draft)
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Markdown", report.draft, 
                                 f"{report.topic.replace(' ', '_')}.md", mime="text/markdown")
            with col2:
                if st.button("🔄 Research Again on this Topic"):
                    st.session_state.topic_to_continue = report.topic
                    st.session_state.goals_to_continue = report.goals
                    st.session_state.view_mode = "new"
                    st.rerun()
        else:
            st.error("Report not found.")
    except Exception as e:
        st.error(f"Error loading report: {e}")

else:
    # ====================== NEW RESEARCH ======================
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input("Research Topic", 
                            value=st.session_state.get("topic_to_continue", ""),
                            placeholder="Agentic AI with LangGraph...")
    with col2:
        depth = st.selectbox("Research Depth", ["Quick", "Medium", "Deep"], index=1)

    goals = st.text_area("Specific Goals / Questions", 
                       value=st.session_state.get("goals_to_continue", ""),
                       height=130,
                       placeholder="Architecture, pros & cons, code examples...")

    if st.button("🚀 Start LangGraph Research", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a research topic")
        else:
            cache_key = hashlib.md5((topic + (goals or "")).encode()).hexdigest()

            if cache_key in st.session_state.research_cache:
                st.success("✅ Loaded from Cache!")
                final_state = st.session_state.research_cache[cache_key]
            else:
                try:
                    graph = create_research_graph()
                    state = {
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

                    status_text.text("📋 Phase 1: Generating Research Plan...")
                    result = graph.invoke(state)
                    plan = result.get("plan", [])

                    st.subheader("📋 Generated Research Plan")
                    for i, p in enumerate(plan, 1):
                        st.write(f"{i}. {p}")

                    if not st.checkbox("✅ Approve Plan & Continue", value=True):
                        st.warning("Research paused. Approve to continue.")
                        st.stop()

                    progress_bar.progress(35)

                    status_text.text("🔍 Phase 2: Conducting Research...")
                    state["plan"] = plan
                    result = graph.invoke(state)
                    findings = result.get("findings", [])

                    progress_bar.progress(70)

                    status_text.text("✍️ Phase 3: Generating Final Report...")
                    state["findings"] = findings
                    result = graph.invoke(state)
                    draft = result.get("draft", "")

                    progress_bar.progress(100)
                    status_text.success("✅ Research Completed!")

                    final_state = AgentState(
                        topic=topic.strip(),
                        goals=goals,
                        plan=plan,
                        findings=findings,
                        draft=draft
                    )

                    st.session_state.research_cache[cache_key] = final_state

                    db = next(get_db())
                    save_to_history(db, final_state, topic, "langgraph")

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

            st.session_state.current_research = {
                "topic": topic.strip(),
                "draft": final_state.draft,
                "final_state": final_state
            }

    # ====================== CURRENT RESEARCH DISPLAY ======================
    if st.session_state.get("current_research"):
        research = st.session_state.current_research
        st.divider()
        st.subheader(f"📄 Final Report: {research['topic']}")

        edited_draft = st.text_area("Review & Edit Report (Optional)", 
                                  value=research['draft'], 
                                  height=500,
                                  key="draft_editor")

        # Reviewer Agent
        if st.button("🔍 Run Reviewer / Critic Agent", type="secondary"):
            with st.spinner("Expert Reviewer Analyzing Report..."):
                from agents.reviewer import ReviewerAgent
                reviewer = ReviewerAgent(get_llm_client())
                temp_state = AgentState(topic=research['topic'], draft=edited_draft)
                review = reviewer.run(temp_state)
                st.subheader("🔍 Expert Reviewer Feedback")
                st.markdown(review)

        # Final Actions
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Save Final Report", type="primary"):
                final_state = research['final_state']
                final_state.draft = edited_draft
                db = next(get_db())
                save_to_history(db, final_state, research['topic'], "langgraph")
                st.success("✅ Report Approved & Saved Successfully!")
        with col2:
            if st.button("🔄 Regenerate Full Report"):
                if "current_research" in st.session_state:
                    del st.session_state.current_research
                st.rerun()

        # Downloads
        st.divider()
        st.subheader("📤 Export Report")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("📥 Markdown", edited_draft, 
                             f"{research['topic'].replace(' ', '_')}_report.md", mime="text/markdown")
        with c2:
            pdf_path = f"output/{research['topic'].replace(' ', '_')}_report.pdf"
            os.makedirs("output", exist_ok=True)
            save_as_pdf(edited_draft, pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button("📕 PDF", f, f"{research['topic'].replace(' ', '_')}_report.pdf", mime="application/pdf")
        with c3:
            docx_path = f"output/{research['topic'].replace(' ', '_')}_report.docx"
            save_as_docx(edited_draft, docx_path)
            with open(docx_path, "rb") as f:
                st.download_button("📘 DOCX", f, f"{research['topic'].replace(' ', '_')}_report.docx", 
                                 mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")