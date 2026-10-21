"""Researcher agent: conducts web search, browses pages, and synthesizes findings using batched API calls."""
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
    """Conducts research by searching the web, browsing pages, and synthesizing all questions in one batched LLM call."""

    def run(self, state: AgentState, progress_callback: Optional[Callable] = None) -> AgentState:
        """Execute research for each question in the plan using a batched LLM call.
        
        Args:
            state: Current agent state with plan and topic.
            progress_callback: Optional callback for UI progress updates.
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
        
        all_search_data = []
        detailed_content = ""

        # Step 1 & 2: Loop to fetch web data (HTTP calls, NO LLM calls)
        for i, question in enumerate(questions):
            progress = (i + 1) / len(questions) * 0.8  # Reserve last 20% for LLM call
            if progress_callback:
                progress_callback(
                    status="researching",
                    progress=progress,
                    detail=f"Gathering data ({i+1}/{len(questions)}): {question[:50]}..."
                )

            try:
                search_results = web_search(question, max_results=max_search_results)
                ref_nums = citation_manager.add_sources_from_search(search_results)
                
                all_search_data.append({
                    "question": question,
                    "sources": search_results,
                    "ref_nums": ref_nums
                })

                for result in search_results[:max_browse_pages]:
                    if result.get("link"):
                        page_content = browse_page(result["link"])
                        detailed_content += f"\n\nSource: {result.get('title', 'N/A')}\n{page_content[:2000]}\n"
                        
            except Exception as e:
                logger.error(f"Error gathering data for '{question[:50]}': {e}")
                all_search_data.append({
                    "question": question,
                    "sources": [],
                    "ref_nums": []
                })
        
        # Step 3: Synthesize with a single batched LLM call
        if progress_callback:
            progress_callback(
                status="researching",
                progress=0.9,
                detail="Synthesizing all findings via LLM (1 API call)..."
            )
            
        try:
            # Flatten sources for the prompt
            flat_sources = []
            for q_data in all_search_data:
                flat_sources.extend(q_data["sources"])
                
            prompt = RESEARCHER_PROMPT.format(
                topic=state.topic,
                questions_json=json.dumps(questions, indent=2)
            ) + f"\n\nSearch Results:\n{json.dumps(flat_sources, indent=2)}\n\nDetailed Content:{detailed_content}"

            # Make the single LLM call
            result_text = self._generate(prompt)

            # Parse the JSON response
            cleaned = result_text.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                cleaned = cleaned.rsplit("```", 1)[0]
                
            findings_data = json.loads(cleaned)
            findings_dict = {f["question"]: f["content"] for f in findings_data if "question" in f and "content" in f}
            
            # Map back to state.findings
            for q_data in all_search_data:
                q = q_data["question"]
                content = findings_dict.get(q, "Research synthesis missing for this question.")
                state.findings.append({
                    "question": q,
                    "content": content,
                    "sources": q_data["sources"],
                    "ref_nums": q_data["ref_nums"]
                })
                
        except Exception as e:
            logger.error(f"Error during batched synthesis: {e}")
            # Fallback if JSON parsing fails
            for q_data in all_search_data:
                state.findings.append({
                    "question": q_data["question"],
                    "content": f"Failed to synthesize batched findings. (Error: {str(e)})",
                    "sources": q_data["sources"],
                    "ref_nums": q_data["ref_nums"]
                })

        if progress_callback:
            progress_callback(
                status="completed_research",
                progress=1.0,
                detail="Completed all research synthesis."
            )

        # Store all collected sources in state
        state.sources = citation_manager.to_list()
        return state