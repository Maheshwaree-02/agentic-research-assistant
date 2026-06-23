# agents/reviewer.py
from agents.base_agent import BaseAgent
from core.prompts import REVIEWER_PROMPT
from core.state import AgentState

class ReviewerAgent(BaseAgent):
    def run(self, state: AgentState):
        if not state.draft:
            return "No draft available to review."

        prompt = REVIEWER_PROMPT.format(
            topic=state.topic,
            report=state.draft
        )
        
        review = self._generate(prompt, temperature=0.5)  # Lower temperature for more structured output
        
        # Store review
        if not hasattr(state, 'citations') or state.citations is None:
            state.citations = []
        state.citations.append("=== REVIEWER FEEDBACK ===")
        state.citations.append(review)
        
        return review