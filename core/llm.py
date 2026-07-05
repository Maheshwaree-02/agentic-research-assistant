"""LLM client management with Gemini primary, Groq fallback, and Mock mode."""
import os
import json
import time
import logging
from config.settings import USE_MOCK, GEMINI_MODEL, GEMINI_MODEL_QUALITY, GROQ_MODEL

logger = logging.getLogger(__name__)

_groq_client = None


def _get_groq_client():
    """Get or create a cached Groq client."""
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                from groq import Groq
                _groq_client = Groq(api_key=api_key)
            except Exception as e:
                logger.error(f"Groq client init failed: {e}")
    return _groq_client


def get_llm_client():
    """Create LLM client with fallback chain: Gemini -> Groq -> Mock."""
    if USE_MOCK:
        logger.info("Mock Mode ACTIVE")
        return {"provider": "mock", "client": None}

    if os.getenv("GEMINI_API_KEY"):
        try:
            from google import genai
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            logger.info(f"Using Gemini Primary ({GEMINI_MODEL})")
            return {"provider": "gemini", "client": client}
        except Exception as e:
            logger.error(f"Gemini init failed: {e}")

    groq_client = _get_groq_client()
    if groq_client:
        logger.info(f"Using Groq Fallback ({GROQ_MODEL})")
        return {"provider": "groq", "client": groq_client}

    logger.warning("No API available → Mock Mode")
    return {"provider": "mock", "client": None}


def generate_content(
    llm: dict,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 6000,
    use_quality: bool = False
) -> str:
    """Generate content with automatic fallback and retry.
    
    Args:
        llm: LLM client dict with 'provider' and 'client' keys.
        prompt: The prompt to send.
        temperature: Sampling temperature.
        max_tokens: Maximum output tokens.
        use_quality: If True, use higher-quality model (gemini-2.5-flash).
    """
    if llm["provider"] == "mock":
        return enhanced_mock_generate(prompt)

    if llm["provider"] == "gemini":
        model = GEMINI_MODEL_QUALITY if use_quality else GEMINI_MODEL
        for attempt in range(3):
            try:
                response = llm["client"].models.generate_content(
                    model=model,
                    contents=prompt,
                    config={"temperature": temperature, "max_output_tokens": max_tokens}
                )
                return response.text
            except Exception as e:
                error_str = str(e).lower()
                if "429" in error_str or "rate" in error_str or "quota" in error_str:
                    wait_time = 2 ** attempt * 5
                    logger.warning(f"Rate limited, waiting {wait_time}s (attempt {attempt + 1}/3)")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Gemini failed: {e}")
                    break

    groq_client = _get_groq_client()
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq failed: {e}")

    logger.warning("All LLMs failed → Using Mock")
    return enhanced_mock_generate(prompt)


def enhanced_mock_generate(prompt: str) -> str:
    """Generate mock responses for development/testing."""
    prompt_lower = prompt.lower()

    if "planner" in prompt_lower or "research plan" in prompt_lower:
        return json.dumps({
            "research_plan": [
                "Core concepts and definitions",
                "Key architectures and frameworks",
                "Recent developments and trends",
                "Implementation best practices and patterns",
                "Challenges, limitations, and future outlook"
            ]
        })

    if "researcher" in prompt_lower or "search results" in prompt_lower:
        return """Based on the research conducted, here are the key findings:

**Key Insights:**
- The technology has seen significant adoption in enterprise environments
- Multiple architectural patterns exist with different trade-offs
- Recent benchmarks show 40% improvement over previous approaches

**Technical Details:**
- Architecture follows a modular design pattern
- Integration with existing systems requires careful consideration
- Performance scales linearly with proper configuration

**Sources consulted include industry reports, academic papers, and official documentation.**"""

    if "reviewer" in prompt_lower or "evaluate" in prompt_lower:
        return json.dumps({
            "overall_score": 7.5,
            "scores": {"depth": 8, "accuracy": 7, "citations": 6, "clarity": 8, "completeness": 7},
            "strengths": ["Comprehensive coverage of core concepts", "Well-structured with clear sections", "Good use of technical examples"],
            "weaknesses": ["Could include more quantitative data", "Some sections lack depth"],
            "suggestions": ["Add performance benchmarks and comparison tables", "Include more recent references (2025-2026)"],
            "missing_aspects": ["Security considerations not covered"],
            "recommendation": "Minor Revision"
        })

    return """# Comprehensive Research Report

## Executive Summary
This report provides a detailed analysis of the topic based on current research findings and established knowledge. Key findings indicate significant progress in the field with multiple viable approaches [1].

## Key Findings
- Significant advancements have been observed in recent implementations [1]
- Multiple architectural approaches exist with different trade-offs [2]
- Enterprise adoption is accelerating with proven ROI [3]

## Technical Details
The current landscape shows a convergence of approaches toward modular, scalable architectures. Industry leaders have reported measurable improvements in efficiency and reliability.

## Best Practices
- Follow established design patterns for maintainability
- Implement comprehensive monitoring and observability
- Use progressive rollout strategies for production deployments

## Conclusion & Future Work
The field continues to evolve rapidly with promising developments on the horizon. Organizations should begin evaluating these technologies for their specific use cases.

## References
[1] Industry Research Report - Technology Trends 2026
[2] Architecture Patterns for Modern Systems - Technical Documentation
[3] Enterprise Adoption Survey - Market Analysis 2026"""