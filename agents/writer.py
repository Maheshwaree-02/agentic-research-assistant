from agents.base_agent import BaseAgent
from core.prompts import WRITER_PROMPT
from core.state import AgentState
from rag.vectorstore import add_research_to_rag, retrieve_context

class WriterAgent(BaseAgent):
    def run(self, state: AgentState):
        findings_text = "\n\n".join(
            f"### {f.get('question', 'Question')}\n{f.get('content', 'No content available')}" 
            for f in state.findings
        )

        # Retrieve RAG context
        rag_context = retrieve_context(state.topic, k=5)

        # Prepare final prompt
        full_prompt = WRITER_PROMPT.format(
            topic=state.topic,
            rag_context=rag_context if rag_context else "No relevant past research available.",
            findings_text=findings_text
        )

        # Generate report
        state.draft = self._generate(full_prompt, temperature=0.65)

        # Store this research into RAG for future use
        try:
            metadata = {
                "topic": state.topic,
                "timestamp": "current",
                "type": "research_report"
            }
            full_content = findings_text + "\n\n" + (state.draft or "")
            add_research_to_rag(full_content, metadata)
        except Exception as e:
            print(f"RAG storage warning: {e}")

        return state
