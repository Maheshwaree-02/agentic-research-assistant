"""ResearchPilot AI — Agentic Research Assistant.

Main Streamlit application with dark theme, Human-in-the-Loop plan approval,
per-agent progress indicators, inline citations, and professional UI.
"""
import streamlit as st
from dotenv import load_dotenv
import os
import hashlib
import logging

from core.llm import get_llm_client
from core.state import AgentState
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.writer import WriterAgent
from agents.reviewer import ReviewerAgent
from database.connection import init_db, get_db
from database.schema import Research
from core.history import save_to_history, load_history
from frontend.styles import get_custom_css
from frontend.components.progress import (
    render_pipeline, render_plan_preview,
    render_findings_preview, render_sources_panel
)
from frontend.components.sidebar import render_sidebar
from frontend.components.report_viewer import render_report, render_review, render_export_section

# ====================== INITIALIZATION ======================
load_dotenv()
init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="ResearchPilot AI",
    layout="wide",
    page_icon="🔬",
    initial_sidebar_state="expanded"
)

# Inject custom CSS
st.markdown(get_custom_css(), unsafe_allow_html=True)

# ====================== SESSION STATE ======================
defaults = {
    "research_cache": {},
    "current_research": None,
    "view_mode": "new",
    "pipeline_step": "idle",
    "current_plan": None,
    "plan_approved": False,
    "current_state": None,
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ====================== SIDEBAR ======================
render_sidebar()

# ====================== MAIN CONTENT ======================

# Header
st.markdown(
    '<div class="main-header">'
    '<h1>🔬 ResearchPilot AI</h1>'
    '<p>Multi-Agent Research System with Citations, RAG Memory & Human-in-the-Loop</p>'
    '</div>',
    unsafe_allow_html=True
)

# ====================== HISTORY VIEW ======================
if st.session_state.get("view_mode") == "history" and st.session_state.get("selected_report"):
    try:
        with get_db() as db:
            report = db.query(Research).filter(
                Research.id == st.session_state.selected_report
            ).first()

            if report:
                render_report(report.topic, report.draft, getattr(report, 'sources', None))

                st.caption(f"📅 Generated: {report.timestamp} | 🎯 Depth: {getattr(report, 'depth', 'Medium')}")

                # Source panel for historical reports
                if hasattr(report, 'sources') and report.sources:
                    render_sources_panel(report.sources)

                st.divider()
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 Markdown",
                        report.draft,
                        f"{report.topic.replace(' ', '_')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                with col2:
                    if st.button("🔄 Research Again", use_container_width=True):
                        st.session_state.topic_to_continue = report.topic
                        st.session_state.goals_to_continue = report.goals or ""
                        st.session_state.view_mode = "new"
                        st.rerun()
                with col3:
                    render_export_section(report.topic, report.draft)
            else:
                st.error("Report not found.")
    except Exception as e:
        st.error(f"Error loading report: {e}")

# ====================== NEW RESEARCH VIEW ======================
else:
    # Input section
    st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "🔍 Research Topic",
            value=st.session_state.get("topic_to_continue", ""),
            placeholder="e.g., Agentic AI with LangGraph in 2026..."
        )
    with col2:
        depth = st.selectbox("📊 Depth", ["Quick", "Medium", "Deep"], index=1)

    goals = st.text_area(
        "🎯 Goals & Questions",
        value=st.session_state.get("goals_to_continue", ""),
        height=100,
        placeholder="What specific aspects do you want to explore? e.g., Architecture, benchmarks, enterprise adoption..."
    )

    st.markdown('</div>', unsafe_allow_html=True)

    # ====================== RESEARCH PIPELINE ======================

    # Show pipeline visualization
    render_pipeline(st.session_state.get("pipeline_step", "idle"))

    # Start Research button
    if st.button("🚀 Start Research", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Please enter a research topic.")
        else:
            # Reset state for new research
            st.session_state.pipeline_step = "planning"
            st.session_state.plan_approved = False
            st.session_state.current_plan = None
            st.session_state.current_research = None

            cache_key = hashlib.md5((topic + (goals or "") + depth).encode()).hexdigest()

            if cache_key in st.session_state.research_cache:
                st.success("✅ Loaded from cache!")
                st.session_state.current_research = st.session_state.research_cache[cache_key]
                st.session_state.pipeline_step = "complete"
                st.rerun()
            else:
                try:
                    client = get_llm_client()
                    state = AgentState(
                        topic=topic.strip(),
                        goals=goals or "Comprehensive technical research",
                        depth=depth
                    )

                    # Phase 1: Planner
                    with st.spinner("📋 Creating research plan..."):
                        planner = PlannerAgent(client)
                        state = planner.run(state)

                    # Store plan for approval
                    st.session_state.current_state = state
                    st.session_state.current_plan = state.plan
                    st.session_state.pipeline_step = "plan_review"
                    st.session_state._client = client
                    st.session_state._cache_key = cache_key
                    st.rerun()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    logger.error(f"Pipeline error: {e}")

    # ====================== PLAN APPROVAL (Human-in-the-Loop) ======================
    if st.session_state.get("pipeline_step") == "plan_review" and st.session_state.get("current_plan"):
        st.markdown('<div class="glass-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 📋 Research Plan — Review & Approve")
        st.caption("Review the AI-generated research plan. Edit questions if needed, then approve to proceed.")

        plan = st.session_state.current_plan

        # Editable plan
        edited_plan = []
        for i, question in enumerate(plan):
            edited_q = st.text_input(f"Question {i+1}", value=question, key=f"plan_q_{i}")
            edited_plan.append(edited_q)

        # Add new question
        new_q = st.text_input("➕ Add a question (optional)", key="new_plan_q", placeholder="Additional research question...")
        if new_q.strip():
            edited_plan.append(new_q.strip())

        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve & Start Research", type="primary", use_container_width=True):
                state = st.session_state.current_state
                state.plan = [q for q in edited_plan if q.strip()]
                client = st.session_state._client

                st.session_state.pipeline_step = "researching"

                # Phase 2: Researcher
                progress_bar = st.progress(0, text="🔍 Starting research...")
                status_container = st.empty()

                def research_progress(status, progress, detail):
                    progress_bar.progress(progress, text=detail)

                researcher = ResearchAgent(client)
                state = researcher.run(state, progress_callback=research_progress)

                st.session_state.pipeline_step = "writing"
                progress_bar.progress(0.7, text="✍️ Generating report...")

                # Phase 3: Writer
                def writer_progress(status, progress, detail):
                    adjusted = 0.7 + progress * 0.3
                    progress_bar.progress(min(adjusted, 1.0), text=detail)

                writer = WriterAgent(client)
                state = writer.run(state, progress_callback=writer_progress)

                progress_bar.progress(1.0, text="✅ Research Complete!")
                st.session_state.pipeline_step = "complete"

                # Store results
                final_data = {
                    "topic": state.topic,
                    "draft": state.draft,
                    "final_state": state,
                    "sources": state.sources,
                    "findings": state.findings,
                    "depth": state.depth
                }
                st.session_state.current_research = final_data
                st.session_state.research_cache[st.session_state._cache_key] = final_data

                # Save to history
                try:
                    with get_db() as db:
                        save_to_history(db, state, state.topic, "sequential")
                except Exception as e:
                    logger.warning(f"Failed to save to history: {e}")

                st.rerun()

        with col2:
            if st.button("🔄 Regenerate Plan", use_container_width=True):
                st.session_state.pipeline_step = "idle"
                st.session_state.current_plan = None
                st.rerun()

    # ====================== DISPLAY RESULTS ======================
    if st.session_state.get("current_research"):
        research = st.session_state.current_research
        state = research.get("final_state")

        st.divider()

        # Findings preview
        if research.get("findings"):
            render_findings_preview(research["findings"])

        # Sources panel
        if research.get("sources"):
            render_sources_panel(research["sources"])

        # Report display
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        
        # Tabs for view/edit
        tab_view, tab_edit = st.tabs(["📖 View Report", "✏️ Edit Report"])
        
        with tab_view:
            render_report(research["topic"], research["draft"], research.get("sources"))

        with tab_edit:
            edited_draft = st.text_area(
                "Edit Report",
                value=research["draft"],
                height=500,
                key="draft_editor"
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ====================== ACTIONS ======================
        st.divider()
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔍 Run Reviewer", use_container_width=True):
                with st.spinner("Reviewing report quality..."):
                    client = get_llm_client()
                    reviewer = ReviewerAgent(client)
                    
                    current_draft = st.session_state.get("draft_editor", research["draft"])
                    temp_state = AgentState(topic=research["topic"], draft=current_draft)
                    temp_state = reviewer.run(temp_state)

                    st.session_state.review_result = temp_state.review

        with col2:
            if st.button("✅ Approve & Save", type="primary", use_container_width=True):
                current_draft = st.session_state.get("draft_editor", research["draft"])
                if state:
                    state.draft = current_draft
                    try:
                        with get_db() as db:
                            save_to_history(db, state, research["topic"], "sequential")
                        st.success("✅ Saved to history!")
                    except Exception as e:
                        st.error(f"Save failed: {e}")

        with col3:
            if st.button("🔄 Regenerate", use_container_width=True):
                st.session_state.current_research = None
                st.session_state.pipeline_step = "idle"
                st.rerun()

        # Show review if available
        if st.session_state.get("review_result"):
            st.divider()
            render_review(st.session_state.review_result)

        # Export section
        st.divider()
        current_draft = st.session_state.get("draft_editor", research["draft"])
        render_export_section(research["topic"], current_draft)