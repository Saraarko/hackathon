"""
Pipeline Global — Graphe LangGraph maître (Modules 1 → 2 → 3 → 4 → 5 → 6 → 7 → 9)

Flux :
  extraction ──→ design ──→ render ──→ sourcing ──→ negotiation ──→ financial ──→ businessplan ──→ catalogue ──→ summary
     (M1)         (M2)       (M3)       (M4)         (M5)             (M6)           (M7)            (M9)
"""

from langgraph.graph import StateGraph, END

from nodes import (
    node_extraction,
    node_design,
    node_render,
    node_sourcing,
    node_negotiation,
    node_financial,
    node_businessplan,
    node_catalogue,
    node_summary,
)
from state import GlobalState


def build_pipeline() -> "CompiledGraph":
    """Compile et retourne le graphe global."""

    graph = StateGraph(GlobalState)

    # ── Nœuds ────────────────────────────────────────────────────────────── #
    graph.add_node("extraction",   node_extraction)
    graph.add_node("design",       node_design)
    graph.add_node("render",       node_render)
    graph.add_node("sourcing",     node_sourcing)
    graph.add_node("negotiation",  node_negotiation)
    graph.add_node("financial",    node_financial)
    graph.add_node("businessplan", node_businessplan)
    graph.add_node("catalogue",    node_catalogue)
    graph.add_node("summary",      node_summary)

    # ── Flux principal ────────────────────────────────────────────────────── #
    graph.set_entry_point("extraction")

    graph.add_edge("extraction",   "design")
    graph.add_edge("design",       "render")
    graph.add_edge("render",       "sourcing")
    graph.add_edge("sourcing",     "negotiation")
    graph.add_edge("negotiation",  "financial")
    graph.add_edge("financial",    "businessplan")
    graph.add_edge("businessplan", "catalogue")
    graph.add_edge("catalogue",    "summary")
    graph.add_edge("summary",      END)

    return graph.compile()
