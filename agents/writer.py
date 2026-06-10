from agents.base_agent import BaseAgent
from core.prompts import WRITER_PROMPT
from core.state import AgentState
from rag.vectorstore import add_research_to_rag, retrieve_context

class WriterAgent(BaseAgent):
    def run(self, state: AgentState):
        findings_text = "\n\n".join(
            f"### {f.get('question', 'Q')}\n{f.get('content', '')}" 
            for f in state.findings
        )

        # RAG Retrieval
        rag_context = retrieve_context(state.topic, k=4)

        # Final Prompt with RAG
        full_prompt = WRITER_PROMPT.format(topic=state.topic) + f"""

=== RELEVANT PAST RESEARCH (Use when helpful) ===
{rag_context}

=== CURRENT RESEARCH FINDINGS ===
{findings_text}
"""

        state.draft = self._generate(full_prompt)

        # Store current research in RAG
        try:
            metadata = {"topic": state.topic, "date": "current"}
            add_research_to_rag(findings_text + "\n\n" + (state.draft or ""), metadata)
        except:
            pass

        return state