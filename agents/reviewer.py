"""Reviewer agent: evaluates research reports with structured scoring."""
import json
import logging
from typing import Optional, Callable
from agents.base_agent import BaseAgent
from core.prompts import REVIEWER_PROMPT
from core.state import AgentState

logger = logging.getLogger(__name__)


class ReviewerAgent(BaseAgent):
    """Reviews and scores research reports using LLM-as-Judge."""

    def run(self, state: AgentState, progress_callback: Optional[Callable] = None) -> AgentState:
        """Evaluate the draft report and store structured feedback.
        
        Args:
            state: Current agent state with draft to review.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Updated AgentState with review field populated.
        """
        if not state.draft:
            state.review = "No draft available to review."
            return state

        if progress_callback:
            progress_callback(status="reviewing", progress=0.0, detail="Analyzing report quality...")

        prompt = REVIEWER_PROMPT.format(
            topic=state.topic,
            report=state.draft
        )

        raw_review = self._generate(prompt, temperature=0.5)

        # Try to parse as JSON for structured scoring
        review_data = self._parse_review(raw_review)
        
        if review_data:
            state.review = self._format_review(review_data)
        else:
            # Fallback: use raw text
            state.review = raw_review

        if progress_callback:
            progress_callback(status="complete", progress=1.0, detail="Review complete!")

        logger.info(f"Review completed for: {state.topic}")
        return state

    def _parse_review(self, raw: str) -> Optional[dict]:
        """Try to parse reviewer output as JSON."""
        try:
            # Handle markdown code blocks
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                cleaned = cleaned.rsplit("```", 1)[0]
            return json.loads(cleaned)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Could not parse review as JSON, using raw text")
            return None

    def _format_review(self, data: dict) -> str:
        """Format structured review data into readable Markdown."""
        lines = []
        
        # Overall score
        overall = data.get("overall_score", "N/A")
        lines.append(f"**Overall Score**: {overall} / 10\n")

        # Sub-scores
        scores = data.get("scores", {})
        if scores:
            lines.append("**Detailed Scores:**")
            for key, val in scores.items():
                emoji = "🟢" if val >= 7 else "🟡" if val >= 5 else "🔴"
                lines.append(f"  {emoji} {key.title()}: {val}/10")
            lines.append("")

        # Sections
        for section, title in [
            ("strengths", "✅ Strengths"),
            ("weaknesses", "⚠️ Weaknesses / Gaps"),
            ("suggestions", "💡 Suggestions for Improvement"),
            ("missing_aspects", "❌ Missing Aspects")
        ]:
            items = data.get(section, [])
            if items:
                lines.append(f"**{title}:**")
                for item in items:
                    lines.append(f"- {item}")
                lines.append("")

        # Recommendation
        rec = data.get("recommendation", "N/A")
        emoji = {"Approve": "✅", "Minor Revision": "🟡", "Major Revision": "🟠", "Reject": "🔴"}.get(rec, "📋")
        lines.append(f"**Final Recommendation**: {emoji} {rec}")

        return "\n".join(lines)