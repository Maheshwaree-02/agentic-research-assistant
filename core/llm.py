import os
import json
from config.settings import USE_MOCK, GEMINI_MODEL, GROQ_MODEL

def get_llm_client():
    if USE_MOCK:
        print("🟡 Mock Mode ACTIVE - No API calls being made")
        return {"provider": "mock", "client": None}
    
    # Try Gemini
    if os.getenv("GEMINI_API_KEY"):
        try:
            from google import genai
            print(f"✅ Using Gemini")
            return {"provider": "gemini", "client": genai.Client(api_key=os.getenv("GEMINI_API_KEY"))}
        except:
            pass
    
    # Try Groq
    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq
            print(f"✅ Using Groq")
            return {"provider": "groq", "client": Groq(api_key=os.getenv("GROQ_API_KEY"))}
        except:
            pass
    
    print("⚠️ No API available → Forcing Mock Mode")
    return {"provider": "mock", "client": None}


def generate_content(llm, prompt: str, temperature: float = 0.7) -> str:
    if llm["provider"] == "mock":
        return enhanced_mock_generate(prompt)
    
    # Real LLM calls (Gemini/Groq) - existing logic
    try:
        if llm["provider"] == "gemini":
            response = llm["client"].models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={"temperature": temperature, "max_output_tokens": 8192}
            )
            return response.text
    except Exception as e:
        print(f"Gemini failed: {e}")
    
    # Try Groq as backup
    try:
        if os.getenv("GROQ_API_KEY"):
            from groq import Groq
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=8192,
            )
            return response.choices[0].message.content
    except Exception as e:
        print(f"Groq failed: {e}")
    
    print("Both LLMs failed → Using Mock")
    return enhanced_mock_generate(prompt)


def enhanced_mock_generate(prompt: str) -> str:
    if "writer" in prompt.lower() or "report" in prompt.lower():
        return """# Emerging AI, Cloud, and Software Development Technologies

## Executive Summary
This comprehensive report analyzes the current landscape of key technologies shaping enterprise software development in 2026.

## Key Findings
• **Agentic AI** has moved from experimental to production use in many organizations.
• **RAG architectures** significantly reduce hallucinations and improve factual accuracy.
• Multi-agent systems using LangGraph show superior orchestration capabilities.
• Cloud-native development with serverless and Kubernetes remains dominant.

## Technical Details
**Agentic AI vs RAG**
- Agentic AI excels at autonomous decision making and tool use.
- RAG excels at knowledge-intensive tasks and reducing hallucinations.

## Best Practices
1. Combine Agentic workflows with RAG for best results.
2. Implement human-in-the-loop for critical decisions.
3. Use PostgreSQL + PGVector for persistent memory.

## Conclusion
Enterprises that successfully integrate Agentic AI, RAG, and robust data infrastructure will have significant competitive advantage in 2026-2027.
"""
    return "Mock response generated."