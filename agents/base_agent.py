"""Base agent class with progress callback support."""
from abc import ABC, abstractmethod
import logging
from core.llm import generate_content

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all agents in the research pipeline."""
    
    def __init__(self, client):
        """Initialize agent with an LLM client.
        
        Args:
            client: LLM client dict from get_llm_client().
        """
        self.client = client

    @abstractmethod
    def run(self, state, progress_callback=None):
        """Execute the agent's task.
        
        Args:
            state: AgentState instance.
            progress_callback: Optional callback for progress updates.
        """
        pass

    def _generate(self, prompt: str, temperature: float = 0.7, use_quality: bool = False, max_tokens: int = 6000):
        """Generate content using the LLM with fallback.
        
        Args:
            prompt: The prompt to send.
            temperature: Sampling temperature.
            use_quality: If True, use higher-quality model.
            max_tokens: Maximum output tokens.
        """
        return generate_content(
            self.client, 
            prompt, 
            temperature=temperature,
            max_tokens=max_tokens,
            use_quality=use_quality
        )