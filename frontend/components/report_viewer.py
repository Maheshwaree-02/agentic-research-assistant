"""Report viewer component with citation display."""
import streamlit as st
import json


def render_report(topic: str, draft: str, sources: list = None):
    """Render the final report with styled display.
    
    Args:
        topic: Research topic.
        draft: Markdown draft content.
        sources: List of source dicts.
    """
    st.markdown(f"### 📄 {topic}")
    
    # Render report as markdown
    st.markdown(draft)


def render_review(review_text: str):
    """Render structured reviewer feedback.
    
    Args:
        review_text: Formatted review text from ReviewerAgent.
    """
    if not review_text:
        return

    st.markdown("### 🔍 Reviewer Feedback")
    
    # Try to render as structured data
    try:
        if review_text.strip().startswith("{"):
            data = json.loads(review_text)
            _render_structured_review(data)
            return
    except (json.JSONDecodeError, ValueError):
        pass

    # Render as markdown (already formatted by ReviewerAgent)
    st.markdown(review_text)


def _render_structured_review(data: dict):
    """Render structured review with score cards."""
    overall = data.get("overall_score", "N/A")
    
    # Overall score
    st.markdown(f"**Overall Score: {overall} / 10**")
    
    # Sub-scores as columns
    scores = data.get("scores", {})
    if scores:
        cols = st.columns(len(scores))
        for col, (key, val) in zip(cols, scores.items()):
            with col:
                st.markdown(
                    f'<div class="score-item">'
                    f'<div class="score-value">{val}</div>'
                    f'<div class="score-label">{key}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
    
    # Sections
    for section, title, emoji in [
        ("strengths", "Strengths", "✅"),
        ("weaknesses", "Weaknesses", "⚠️"),
        ("suggestions", "Suggestions", "💡"),
        ("missing_aspects", "Missing", "❌"),
    ]:
        items = data.get(section, [])
        if items:
            st.markdown(f"**{emoji} {title}:**")
            for item in items:
                st.markdown(f"- {item}")
    
    rec = data.get("recommendation", "N/A")
    emoji = {"Approve": "✅", "Minor Revision": "🟡", "Major Revision": "🟠", "Reject": "🔴"}.get(rec, "📋")
    st.markdown(f"**Recommendation:** {emoji} {rec}")


def render_export_section(topic: str, draft: str):
    """Render export buttons for the report.
    
    Args:
        topic: Research topic (for filenames).
        draft: Report content to export.
    """
    import os

    st.markdown("#### 📦 Export Report")
    
    safe_topic = topic.replace(' ', '_').replace('/', '_')[:50]
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.download_button(
            "📝 Markdown",
            draft,
            f"{safe_topic}_report.md",
            mime="text/markdown",
            use_container_width=True
        )
    
    with c2:
        try:
            from tools.document import save_as_pdf
            pdf_path = f"output/{safe_topic}_report.pdf"
            os.makedirs("output", exist_ok=True)
            save_as_pdf(draft, pdf_path)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    "📕 PDF",
                    f,
                    f"{safe_topic}_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"PDF error: {e}")
    
    with c3:
        try:
            from tools.document import save_as_docx
            docx_path = f"output/{safe_topic}_report.docx"
            os.makedirs("output", exist_ok=True)
            save_as_docx(draft, docx_path)
            with open(docx_path, "rb") as f:
                st.download_button(
                    "📘 DOCX",
                    f,
                    f"{safe_topic}_report.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"DOCX error: {e}")
