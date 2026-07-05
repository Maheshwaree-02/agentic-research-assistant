"""Planner agent: generates structured research plans."""
import json
import logging
from typing import Optional, Callable
from agents.base_agent import BaseAgent
from core.prompts import PLANNER_PROMPT
from core.state import AgentState

logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """Creates structured research plans based on topic, goals, and depth."""

    def run(self, state: AgentState, progress_callback: Optional[Callable] = None) -> AgentState:
        """Generate a research plan.
        
        Args:
            state: Current agent state with topic and goals.
            progress_callback: Optional callback for progress updates.
        """
        if progress_callback:
            progress_callback(status="planning", progress=0.0, detail="Creating research plan...")

        prompt = PLANNER_PROMPT.format(
            topic=state.topic,
            goals=state.goals or "Provide comprehensive technical research on the topic.",
            depth=state.depth
        )

        response = self._generate(prompt, temperature=0.7, use_quality=False)

        try:
            # Try to strip markdown code block if present
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
                cleaned = cleaned.rsplit("```", 1)[0]
            
            plan_data = json.loads(cleaned)
            state.plan = plan_data.get("research_plan", plan_data.get("plan", []))
        except (json.JSONDecodeError, ValueError):
            logger.warning("Could not parse plan as JSON, falling back to line splitting")
            state.plan = [line.strip() for line in response.split("\n") if line.strip() and len(line.strip()) > 5]

        if not state.plan:
            state.plan = [
                "Understand core concepts and definitions",
                "Key components, architecture, and design patterns",
                "Recent developments and industry trends",
                "Best practices and implementation guidelines",
                "Challenges, limitations, and future outlook"
            ]
            logger.info("Using default research plan")

        if progress_callback:
            progress_callback(status="complete", progress=1.0, detail=f"Plan ready: {len(state.plan)} questions")

        logger.info(f"Generated plan with {len(state.plan)} questions for: {state.topic}")
        return state