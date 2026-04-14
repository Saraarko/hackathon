from langgraph.graph import StateGraph
from agents.agent2 import run_agent2

def build_graph():
    """
    Module 2 Graph - CAD Pipeline.
    Consolidated into a single Agent 2 node for professional engineering output.
    """
    graph = StateGraph(dict)

    # Simplified single-node architecture for Agent 2
    graph.add_node("engineer", run_agent2)

    graph.set_entry_point("engineer")
    graph.set_finish_point("engineer")

    return graph.compile()