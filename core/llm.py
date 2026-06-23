import os
import json
from config.settings import USE_MOCK, GEMINI_MODEL, GROQ_MODEL

def get_llm_client():
    if USE_MOCK:
        print("🟡 Mock Mode ACTIVE")
        return {"provider": "mock", "client": None}
   
    # Try Gemini first (fast model for most calls)
    if os.getenv("GEMINI_API_KEY"):
        try:
            from google import genai
            print(f"✅ Using Gemini ({GEMINI_MODEL})")
            return {"provider": "gemini", "client": genai.Client(api_key=os.getenv("GEMINI_API_KEY"))}
        except Exception as e:
            print(f"Gemini init failed: {e}")
   
    # Groq as fallback
    if os.getenv("GROQ_API_KEY"):
        try:
            from groq import Groq
            print(f"✅ Using Groq ({GROQ_MODEL})")
            return {"provider": "groq", "client": Groq(api_key=os.getenv("GROQ_API_KEY"))}
        except Exception as e:
            print(f"Groq init failed: {e}")
   
    print("⚠️ No API available → Mock Mode")
    return {"provider": "mock", "client": None}


def generate_content(llm, prompt: str, temperature: float = 0.7, max_tokens: int = 8192) -> str:
    """Optimized generate function with better error handling"""
    if llm["provider"] == "mock":
        return enhanced_mock_generate(prompt)
    
    # Try Gemini first
    if llm["provider"] == "gemini":
        try:
            response = llm["client"].models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
                config={
                    "temperature": temperature, 
                    "max_output_tokens": max_tokens
                }
            )
            return response.text
        except Exception as e:
            print(f"❌ Gemini failed: {e}")
            print("🔄 Switching to Groq fallback...")

    # Try Groq
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq failed: {e}")
    
    print("⚠️ Both LLMs failed → Using Mock")
    return enhanced_mock_generate(prompt)


def enhanced_mock_generate(prompt: str) -> str:
    prompt_lower = prompt.lower()
    
    if "planner" in prompt_lower:
        return json.dumps({
            "research_plan": [
                "Core concepts and definitions",
                "Key architectures and frameworks",
                "Recent developments and case studies",
                "Implementation best practices",
                "Challenges, limitations and future outlook"
            ]
        })
    
    # Default rich mock for Writer/Reviewer
    return """# Comprehensive Research Report

## Executive Summary
This report provides a detailed analysis based on current knowledge and latest trends in the field.

## Key Findings
• Significant advancements have been observed
• Multiple architectural approaches exist with different trade-offs
• Real-world adoption is accelerating rapidly

## Technical Details
• Strong emphasis on modularity and scalability
• Good performance benchmarks

## Best Practices
1. Start with clear requirements and success metrics
2. Implement iterative development and testing
3. Use monitoring and observability from day one

## Conclusion
The field continues to evolve rapidly. Future efforts should focus on better integration, reliability, and ethical considerations.
"""