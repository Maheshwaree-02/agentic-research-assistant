"""Writer agent: generates professional cited research reports."""
import logging
from typing import Optional, Callable
from datetime import datetime
from agents.base_agent import BaseAgent
from core.prompts import WRITER_PROMPT
from core.state import AgentState
from core.citation_manager import CitationManager
from rag.vectorstore import retrieve_context, add_research_to_rag
from config.settings import RESEARCH_DEPTH_CONFIG

logger = logging.getLogger(__name__)


class WriterAgent(BaseAgent):
    """Generates professional research reports with inline citations."""

    def run(self, state: AgentState, progress_callback: Optional[Callable] = None) -> AgentState:
        """Generate the final report with citations.
        
        Args:
            state: Current agent state with findings and sources.
            progress_callback: Optional callback for UI progress updates.
        """
        if progress_callback:
            progress_callback(status="writing", progress=0.0, detail="Retrieving past research...")

        # Retrieve RAG context
        rag_context = retrieve_context(state.topic, k=3)

        # Prepare findings text
        findings_text = "\n\n".join(
            f"### {f.get('question', 'Question')}\n{f.get('content', 'No content')}"
            for f in state.findings
        )

        # Build citation context
        citation_manager = CitationManager.from_list(state.sources) if state.sources else CitationManager()
        sources_text = citation_manager.format_sources_for_prompt()

        if progress_callback:
            progress_callback(status="writing", progress=0.3, detail="Generating report...")

        # Get depth-specific token limit
        depth_config = RESEARCH_DEPTH_CONFIG.get(state.depth, RESEARCH_DEPTH_CONFIG["Medium"])

        # Format prompt with sources
        prompt = WRITER_PROMPT.format(
            topic=state.topic,
            findings_text=findings_text,
            rag_context=rag_context if rag_context else "No relevant past research found.",
            sources_text=sources_text
        )

        # Generate report with quality model
        state.draft = self._generate(
            prompt,
            temperature=0.65,
            use_quality=True,
            max_tokens=depth_config["max_tokens"]
        )

        # Append bibliography
        bibliography = citation_manager.format_bibliography()
        if bibliography and state.draft:
            state.draft = state.draft.rstrip() + "\n" + bibliography

        if progress_callback:
            progress_callback(status="writing", progress=0.8, detail="Storing in knowledge base...")

        # Store in RAG with proper metadata
        try:
            metadata = {
                "topic": state.topic,
                "timestamp": datetime.now().isoformat(),
                "depth": state.depth,
                "source_count": citation_manager.count
            }
            full_content = findings_text + "\n\n" + (state.draft or "")
            add_research_to_rag(full_content[:5000], metadata)
        except Exception as e:
            logger.warning(f"RAG storage warning: {e}")

        # Store citations in state
        state.citations = [src.get("url", "") for src in state.sources]

        if progress_callback:
            progress_callback(status="complete", progress=1.0, detail="Report complete!")

        return state