import json
from agents.base_agent import BaseAgent
from core.prompts import PLANNER_PROMPT
from core.state import AgentState

class PlannerAgent(BaseAgent):
    def run(self, state: AgentState, goals: str):
        prompt = PLANNER_PROMPT.format(
            topic=state.topic,
            goals=goals or "General deep technical research"
        )
        response = self._generate(prompt)
        
        try:
            plan_data = json.loads(response.strip())
            # Ensure it's a list of strings
            state.plan = plan_data.get("research_plan", [])
            if not isinstance(state.plan, list):
                state.plan = [str(state.plan)]
        except:
            # Fallback
            state.plan = [
                f"Understand the fundamentals of {state.topic}",
                f"Key components and architecture",
                f"Recent developments and real-world examples",
                f"Best practices and implementation strategies",
                f"Challenges and future outlook"
            ]
        
        return state