from langgraph.graph import StateGraph

from agents.rule_agent import apply_design_rules
from agents.geometry_agent import build_geometry
from agents.dxf_agent import generate_dxf
from agents.step_agent import generate_step
from agents.ifc_agent import generate_ifc
from agents.validation_agent import validate


def build_graph():
    graph = StateGraph(dict)

    graph.add_node("rules", apply_design_rules)
    graph.add_node("geometry", build_geometry)
    graph.add_node("dxf", generate_dxf)
    graph.add_node("step", generate_step)
    graph.add_node("ifc", generate_ifc)
    graph.add_node("validate", validate)

    graph.set_entry_point("rules")

    graph.add_edge("rules", "geometry")
    graph.add_edge("geometry", "dxf")
    graph.add_edge("dxf", "step")
    graph.add_edge("step", "ifc")
    graph.add_edge("ifc", "validate")

    return graph.compile()