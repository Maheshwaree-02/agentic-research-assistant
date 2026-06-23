from abc import ABC, abstractmethod
from core.llm import generate_content

class BaseAgent(ABC):
    def __init__(self, client):
        self.client = client

    def _generate(self, prompt: str, temperature: float = 0.7) -> str:
        """Generate content with optional temperature parameter"""
        return generate_content(self.client, prompt, temperature=temperature)

    @abstractmethod
    def run(self, state, **kwargs):
        pass