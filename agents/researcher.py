"""Researcher agent: conducts web search, browses pages, and synthesizes findings."""
import json
import logging
from typing import Optional, Callable
from agents.base_agent import BaseAgent
from core.prompts import RESEARCHER_PROMPT
from core.state import AgentState
from core.citation_manager import CitationManager
from tools.search import web_search, browse_page
from config.settings import RESEARCH_DEPTH_CONFIG

logger = logging.getLogger(__name__)


class ResearchAgent(BaseAgent):
    """Conducts research by searching the web, browsing pages, and synthesizing."""

    def run(self, state: AgentState, progress_callback: Optional[Callable] = None) -> AgentState:
        """Execute research for each question in the plan.
        
        Args:
            state: Current agent state with plan and topic.
            progress_callback: Optional callback for UI progress updates.
                Signature: callback(status: str, progress: float, detail: str)
        """
        if not state.plan:
            state.findings.append({"question": "General", "content": "No research plan available.", "sources": []})
            return state

        depth_config = RESEARCH_DEPTH_CONFIG.get(state.depth, RESEARCH_DEPTH_CONFIG["Medium"])
        max_questions = depth_config["max_questions"]
        max_search_results = depth_config["max_search_results"]
        max_browse_pages = depth_config["max_browse_pages"]

        citation_manager = CitationManager()
        questions = state.plan[:max_questions]

        for i, question in enumerate(questions):
            progress = (i + 1) / len(questions)
            if progress_callback:
                progress_callback(
                    status="researching",
                    progress=progress,
                    detail=f"Researching ({i+1}/{len(questions)}): {question[:70]}..."
                )

            try:
                # Step 1: Web Search
                search_results = web_search(question, max_results=max_search_results)

                # Track sources
                ref_nums = citation_manager.add_sources_from_search(search_results)

                # Step 2: Browse top pages for deeper content
                detailed_content = ""
                for result in search_results[:max_browse_pages]:
                    if result.get("link"):
                        page_content = browse_page(result["link"])
                        detailed_content += f"\n\nSource: {result.get('title', 'N/A')}\n{page_content[:2000]}\n"

                # Step 3: Synthesize with LLM
                prompt = RESEARCHER_PROMPT.format(
                    topic=state.topic,
                    question=question
                ) + f"\n\nSearch Results:\n{json.dumps(search_results, indent=2)}\n\nDetailed Content:{detailed_content}"

                result_text = self._generate(prompt)

                state.findings.append({
                    "question": question,
                    "content": result_text,
                    "sources": search_results,
                    "ref_nums": ref_nums
                })

                if progress_callback:
                    progress_callback(
                        status="completed_question",
                        progress=progress,
                        detail=f"Completed: {question[:60]}..."
                    )

                logger.info(f"Completed research question {i+1}/{len(questions)}")

            except Exception as e:
                logger.error(f"Error researching '{question[:50]}': {e}")
                state.findings.append({
                    "question": question,
                    "content": f"Research failed: {str(e)}",
                    "sources": [],
                    "ref_nums": []
                })

        # Store all collected sources in state
        state.sources = citation_manager.to_list()
        return state