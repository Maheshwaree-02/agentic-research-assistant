"""Sidebar component for ResearchPilot AI."""
import streamlit as st
from database.connection import get_db
from database.schema import Research
from core.history import load_history


def render_sidebar():
    """Render the sidebar with history, settings, and info."""
    with st.sidebar:
        # Header
        st.markdown(
            '<div class="sidebar-header">'
            '<h2>🔬 ResearchPilot AI</h2>'
            '<p>Agentic Research Assistant</p>'
            '</div>',
            unsafe_allow_html=True
        )

        # New Research button
        if st.button("🆕 New Research", use_container_width=True, type="primary"):
            st.session_state.view_mode = "new"
            st.session_state.current_research = None
            st.session_state.pipeline_step = "idle"
            if "topic_to_continue" in st.session_state:
                del st.session_state["topic_to_continue"]
            if "goals_to_continue" in st.session_state:
                del st.session_state["goals_to_continue"]
            st.rerun()

        st.divider()

        # Research History
        st.markdown("#### 📜 Research History")
        
        try:
            with get_db() as db:
                history = load_history(db, limit=15)
                
                if not history:
                    st.caption("No research history yet. Start your first research!")
                else:
                    seen = set()
                    for entry in history:
                        if entry.topic not in seen:
                            seen.add(entry.topic)
                            # Truncate long topics
                            display_topic = entry.topic[:42] + "..." if len(entry.topic) > 42 else entry.topic
                            depth_emoji = {"Quick": "⚡", "Medium": "📊", "Deep": "🔬"}.get(
                                getattr(entry, 'depth', 'Medium'), "📊"
                            )
                            
                            if st.button(
                                f"{depth_emoji} {display_topic}",
                                key=f"hist_{entry.id}",
                                use_container_width=True
                            ):
                                st.session_state.selected_report = entry.id
                                st.session_state.view_mode = "history"
                                st.rerun()
        except Exception:
            st.caption("📴 Database not connected")

        st.divider()

        # Settings
        with st.expander("⚙️ Settings", expanded=False):
            mock_mode = st.toggle("🧪 Mock Mode", value=False, help="Use mock LLM for testing")
            if mock_mode:
                st.caption("Using mock responses (no API calls)")
            
            st.caption("**LLM Stack:**")
            st.caption("Primary: Gemini 2.5 Flash")
            st.caption("Quality: Gemini 2.5 Flash (Full)")
            st.caption("Fallback: Groq LLaMA 3.3 70B")

        # Tech Stack Info
        st.markdown(
            '<div class="tech-stack">'
            '🗄️ PostgreSQL • 🧠 ChromaDB RAG<br>'
            '🤖 Gemini + Groq • 📊 LangGraph'
            '</div>',
            unsafe_allow_html=True
        )
