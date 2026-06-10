from abc import ABC, abstractmethod
from core.llm import generate_content
from core.state import AgentState

class BaseAgent(ABC):
    def __init__(self, client):
        self.client = client

    @abstractmethod
    def run(self, state: AgentState, **kwargs):
        pass

    def _generate(self, prompt: str) -> str:
        return generate_content(self.client, prompt)