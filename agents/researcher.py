import json
import streamlit as st
from agents.base_agent import BaseAgent
from core.prompts import RESEARCHER_PROMPT
from core.state import AgentState
from tools.search import web_search, browse_page

class ResearchAgent(BaseAgent):
    def run(self, state: AgentState):
        if not state.plan:
            state.findings.append({"question": "General", "content": "No research plan available."})
            return state

        for i, question in enumerate(state.plan[:5]):  # Limit to 5 for free tier stability
            with st.spinner(f"🔍 Researching ({i+1}/{len(state.plan)}): {question[:70]}..."):
                try:
                    # Step 1: Web Search
                    search_results = web_search(question, max_results=4)
                    
                    # Step 2: Browse top pages for deeper content
                    detailed_content = ""
                    for result in search_results[:2]:
                        if result.get("link"):
                            page_content = browse_page(result["link"])
                            detailed_content += f"\n\nSource: {result.get('title', 'N/A')}\n{page_content[:1800]}\n"
                    
                    # Step 3: Synthesize with Gemini
                    prompt = RESEARCHER_PROMPT.format(
                        topic=state.topic,
                        question=question
                    ) + f"\n\nSearch Results:\n{json.dumps(search_results, indent=2)}\n\nDetailed Content:{detailed_content}"
                    
                    result_text = self._generate(prompt)
                    
                    state.findings.append({
                        "question": question,
                        "content": result_text,
                        "sources": search_results
                    })
                    
                    st.success(f"✅ Completed: {question[:60]}...")
                    
                except Exception as e:
                    st.warning(f"⚠️ Error researching '{question[:50]}...': {str(e)}")
                    state.findings.append({
                        "question": question,
                        "content": f"Research failed: {str(e)}",
                        "sources": []
                    })
        
        return state