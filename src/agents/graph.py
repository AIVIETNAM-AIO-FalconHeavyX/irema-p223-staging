from langgraph.graph import END, StateGraph

from src.agents.nodes.controller import controller_node
from src.agents.nodes.escalation_node import escalation_node
from src.agents.nodes.query_rewriter import query_rewriter_node
from src.agents.nodes.rag_node import rag_node
from src.agents.nodes.response_generator import response_generator_node
from src.agents.nodes.troubleshooting_node import troubleshooting_node
from src.agents.nodes.workflow_node import workflow_node
from src.agents.state import AgentState


def route_intent(state: AgentState) -> str:
    """Route execution path based on classified intent from Controller.

    GENERAL_QA bypass RAG hoàn toàn → response_generator trực tiếp.
    """
    intent = state.get("intent", "RAG_SEARCH")
    if intent == "TROUBLESHOOTING":
        return "troubleshooting"
    elif intent == "WORKFLOW":
        return "workflow"
    elif intent == "CREATE_TICKET":
        return "escalation"
    elif intent == "GENERAL_QA":
        # Bypass RAG — trả lời trực tiếp từ persona
        return "response_generator"
    elif intent == "CONVERSATION_META":
        return "response_generator"
    else:
        return "rag"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("controller", controller_node)
    graph.add_node("query_rewriter", query_rewriter_node)
    graph.add_node("rag", rag_node)
    graph.add_node("troubleshooting", troubleshooting_node)
    graph.add_node("workflow", workflow_node)
    graph.add_node("escalation", escalation_node)
    graph.add_node("response_generator", response_generator_node)

    graph.set_entry_point("query_rewriter")
    graph.add_edge("query_rewriter", "controller")

    # Conditional routing từ controller (bao gồm cả GENERAL_QA → response_generator)
    graph.add_conditional_edges("controller", route_intent)

    # Intermediate edges to RAG or Response Generator
    graph.add_edge("troubleshooting", "rag")
    graph.add_edge("workflow", "rag")
    graph.add_edge("rag", "response_generator")
    graph.add_edge("escalation", "response_generator")

    graph.add_edge("response_generator", END)

    return graph.compile()


agent = build_graph()
