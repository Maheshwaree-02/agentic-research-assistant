# agents/langgraph_workflow.py
from typing import Dict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage

from core.llm import get_llm_client
from agents.planner import PlannerAgent
from agents.researcher import ResearchAgent
from agents.writer import WriterAgent
from core.state import AgentState

class GraphState(Dict):
    topic: str
    goals: str
    plan: list | None
    findings: list
    draft: str | None
    messages: Annotated[list, add_messages]
    next: str
    user_feedback: str | None = None


def planner_node(state: GraphState) -> Dict:
    llm = get_llm_client()
    planner = PlannerAgent(llm)
    temp_state = AgentState(topic=state["topic"], goals=state.get("goals"))
    result = planner.run(temp_state, state.get("goals"))
    
    return {
        "plan": result.plan,
        "messages": [HumanMessage(content="Planning completed")]
    }


def researcher_node(state: GraphState) -> Dict:
    llm = get_llm_client()
    researcher = ResearchAgent(llm)
    temp_state = AgentState(topic=state["topic"], plan=state.get("plan"))
    result = researcher.run(temp_state)
    
    return {
        "findings": result.findings,
        "messages": [HumanMessage(content="Research completed")]
    }


def writer_node(state: GraphState) -> Dict:
    llm = get_llm_client()
    writer = WriterAgent(llm)
    temp_state = AgentState(topic=state["topic"], findings=state.get("findings", []))
    result = writer.run(temp_state)
    
    return {
        "draft": result.draft,
        "messages": [HumanMessage(content="Draft generated")]
    }


def supervisor_node(state: GraphState) -> Dict:
    if not state.get("plan"):
        return {"next": "planner"}
    elif not state.get("findings") or len(state.get("findings", [])) == 0:
        return {"next": "researcher"}
    else:
        return {"next": "writer"}


def create_research_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("supervisor", supervisor_node)

    workflow.set_entry_point("supervisor")

    workflow.add_conditional_edges(
        "supervisor",
        lambda x: x["next"],
        {
            "planner": "planner",
            "researcher": "researcher",
            "writer": "writer"
        }
    )

    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("researcher", "supervisor")
    workflow.add_edge("writer", END)

    return workflow.compile()