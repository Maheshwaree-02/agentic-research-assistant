"""LangGraph-based workflow orchestration for ResearchPilot AI.

This module provides a LangGraph StateGraph alternative to the sequential
pipeline used in main.py. It can be used when LangGraph orchestration
with a supervisor pattern is preferred.

Usage:
    from agents.langgraph_workflow import create_research_graph
    graph = create_research_graph()
    result = graph.invoke({"topic": "...", "goals": "...", "depth": "Medium"})
"""
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
import logging

logger = logging.getLogger(__name__)


class ResearchGraphState(TypedDict):
    """Typed state for the LangGraph research workflow."""
    topic: str
    goals: str
    depth: str
    plan: Optional[List[str]]
    findings: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    draft: Optional[str]
    citations: List[str]
    next: Optional[str]


def planner_node(state: ResearchGraphState) -> dict:
    """Generate research plan."""
    from agents.planner import PlannerAgent
    from core.llm import get_llm_client
    from core.state import AgentState

    try:
        llm = get_llm_client()
        planner = PlannerAgent(llm)
        agent_state = AgentState(
            topic=state.get("topic", ""),
            goals=state.get("goals", ""),
            depth=state.get("depth", "Medium")
        )
        result = planner.run(agent_state)
        logger.info(f"Planner generated {len(result.plan)} questions")
        return {"plan": result.plan}
    except Exception as e:
        logger.error(f"Planner node failed: {e}")
        return {"plan": ["Core concepts", "Key developments", "Best practices"]}


def researcher_node(state: ResearchGraphState) -> dict:
    """Conduct research for each plan question."""
    from agents.researcher import ResearchAgent
    from core.llm import get_llm_client
    from core.state import AgentState

    try:
        llm = get_llm_client()
        researcher = ResearchAgent(llm)
        agent_state = AgentState(
            topic=state.get("topic", ""),
            plan=state.get("plan"),
            depth=state.get("depth", "Medium")
        )
        result = researcher.run(agent_state)
        return {"findings": result.findings, "sources": result.sources}
    except Exception as e:
        logger.error(f"Researcher node failed: {e}")
        return {"findings": [{"question": "Error", "content": str(e)}], "sources": []}


def writer_node(state: ResearchGraphState) -> dict:
    """Generate final report with citations."""
    from agents.writer import WriterAgent
    from core.llm import get_llm_client
    from core.state import AgentState

    try:
        llm = get_llm_client()
        writer = WriterAgent(llm)
        agent_state = AgentState(
            topic=state.get("topic", ""),
            findings=state.get("findings", []),
            sources=state.get("sources", []),
            plan=state.get("plan", []),
            depth=state.get("depth", "Medium")
        )
        result = writer.run(agent_state)
        return {"draft": result.draft, "citations": result.citations}
    except Exception as e:
        logger.error(f"Writer node failed: {e}")
        return {"draft": f"Report generation failed: {e}", "citations": []}


def supervisor_node(state: ResearchGraphState) -> dict:
    """Route to the next agent based on current state."""
    if not state.get("plan"):
        return {"next": "planner"}
    if not state.get("findings") or len(state.get("findings", [])) == 0:
        return {"next": "researcher"}
    if not state.get("draft"):
        return {"next": "writer"}
    return {"next": END}


def create_research_graph():
    """Create and compile the LangGraph research workflow.
    
    Returns:
        Compiled LangGraph StateGraph.
    """
    workflow = StateGraph(ResearchGraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("supervisor", supervisor_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x.get("next"),
        {
            "planner": "planner",
            "researcher": "researcher",
            "writer": "writer",
            END: END
        }
    )

    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("writer", "supervisor")

    return workflow.compile()