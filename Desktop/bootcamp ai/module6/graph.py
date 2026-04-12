# graph.py

from langgraph.graph import StateGraph

from agents.scenario_agent import generate_scenarios
from agents.data_agent import run_data_agent
from agents.projection_agent import project
from agents.montecarlo_agent import run_montecarlo
from agents.risk_agent import compute_risk
from agents.finance_agent import compute_roi
from agents.report_agent import generate_all_outputs
def build_graph():

    graph = StateGraph(dict)

    graph.add_node("scenario", lambda s: {**s, "scenarios": generate_scenarios(s["base_cost"])})
    graph.add_node("data", run_data_agent)
    graph.add_node("projection", lambda s: {**s, "total_cost": project(s["base_cost"], s["inflation"])[0]})
    graph.add_node("montecarlo", lambda s: {**s, "mc": run_montecarlo(s["base_cost"], s["inflation"])})
    graph.add_node("risk", lambda s: {**s, "risk": compute_risk(s["inflation"], s["mc"])})
    graph.add_node("finance", lambda s: {**s, "roi": compute_roi(s["total_cost"])})
    graph.add_node("report", lambda s: generate_all_outputs(s) or s)

    graph.set_entry_point("scenario")

    graph.add_edge("scenario", "data")
    graph.add_edge("data", "projection")
    graph.add_edge("projection", "montecarlo")
    graph.add_edge("montecarlo", "risk")
    graph.add_edge("risk", "finance")
    graph.add_edge("finance", "report")

    return graph.compile()