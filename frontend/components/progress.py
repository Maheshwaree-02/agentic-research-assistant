"""Progress visualization components for the research pipeline."""
import streamlit as st


def render_pipeline(active_step: str = "idle"):
    """Render the agent pipeline visualization.
    
    Args:
        active_step: One of 'idle', 'planning', 'plan_review', 'researching', 'writing', 'reviewing', 'complete'
    """
    steps = [
        ("📋", "Planner", "planning"),
        ("✅", "Approve", "plan_review"),
        ("🔍", "Researcher", "researching"),
        ("✍️", "Writer", "writing"),
        ("📄", "Complete", "complete"),
    ]

    step_order = ["planning", "plan_review", "researching", "writing", "complete"]
    active_idx = step_order.index(active_step) if active_step in step_order else -1

    html_parts = ['<div class="pipeline-container">']
    
    for i, (emoji, label, step_id) in enumerate(steps):
        if active_idx >= 0 and step_order.index(step_id) < active_idx:
            css_class = "done"
            icon = "✅"
        elif active_step == step_id:
            css_class = "active"
            icon = emoji
        else:
            css_class = "waiting"
            icon = emoji

        html_parts.append(
            f'<div class="pipeline-step {css_class}">{icon} {label}</div>'
        )
        if i < len(steps) - 1:
            html_parts.append('<div class="pipeline-arrow">→</div>')

    html_parts.append('</div>')
    st.markdown("".join(html_parts), unsafe_allow_html=True)


def render_plan_preview(plan: list):
    """Render the research plan for approval.
    
    Args:
        plan: List of research questions/steps.
    """
    st.markdown("#### 📋 Research Plan")
    
    for i, question in enumerate(plan, 1):
        st.markdown(
            f'<div class="plan-item">'
            f'<div class="plan-number">{i}</div>'
            f'<span>{question}</span>'
            f'</div>',
            unsafe_allow_html=True
        )


def render_findings_preview(findings: list):
    """Render intermediate research findings.
    
    Args:
        findings: List of finding dicts with question, content, sources.
    """
    if not findings:
        return

    with st.expander(f"🔍 Research Findings ({len(findings)} questions explored)", expanded=False):
        for f in findings:
            question = f.get("question", "Unknown")
            content = f.get("content", "No content")
            sources = f.get("sources", [])

            st.markdown(
                f'<div class="finding-card">'
                f'<h4>❓ {question}</h4>'
                f'</div>',
                unsafe_allow_html=True
            )
            
            # Show truncated content
            if len(content) > 500:
                st.markdown(content[:500] + "...")
            else:
                st.markdown(content)

            # Show source badges
            if sources:
                badges_html = " ".join(
                    f'<a href="{s.get("link", "#")}" target="_blank" class="source-badge">'
                    f'🔗 {s.get("title", "Source")[:40]}</a>'
                    for s in sources if s.get("link")
                )
                if badges_html:
                    st.markdown(badges_html, unsafe_allow_html=True)

            st.divider()


def render_sources_panel(sources: list):
    """Render a panel showing all collected sources.
    
    Args:
        sources: List of source dicts from CitationManager.
    """
    if not sources:
        return

    with st.expander(f"📚 Sources & References ({len(sources)} sources)", expanded=False):
        for src in sources:
            ref_num = src.get("ref_num", "?")
            title = src.get("title", "Unknown")
            url = src.get("url", "")
            domain = src.get("domain", "")
            date = src.get("accessed_date", "")

            col1, col2 = st.columns([4, 1])
            with col1:
                st.markdown(f"**[{ref_num}]** {title}")
                if domain:
                    st.caption(f"📌 {domain} • Accessed: {date}")
            with col2:
                if url:
                    st.markdown(f"[🔗 Open]({url})")
