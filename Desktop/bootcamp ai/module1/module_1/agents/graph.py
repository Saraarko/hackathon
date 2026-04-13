"""
Module 1 — Construction et compilation du graphe LangGraph.

Usage:
    from module_1.agents.graph import build_graph
    import anthropic

    client = anthropic.Anthropic()
    graph  = build_graph(llm_client=client)
    result = graph.invoke({"pdf_path": "plans/vanne_DN100.pdf"})
    specs  = result["specs"]
"""

from __future__ import annotations

import functools
import logging
from typing import Any

from langgraph.graph import END, StateGraph

from module_1.agents.extraction_nodes import (
    node_extract_specs,
    node_parse_pdf,
    node_validate_specs,
    should_retry,
)
from module_1.schemas.state import ExtractionState

logger = logging.getLogger(__name__)


def build_graph(llm_client: Any) -> StateGraph:
    """
    Construit le graphe LangGraph du Module 1.

    Topologie :
        parse_pdf ──▶ extract_specs ──▶ validate_specs
                             ▲                 │
                             └────(retry)──────┘
                                               │
                                            (end) ──▶ END

    Args:
        llm_client: Instance du client LLM (anthropic.Anthropic ou ollama).

    Returns:
        Graphe compilé, prêt pour .invoke() ou .stream().
    """
    # Injecte le client LLM dans le nœud d'extraction via partial
    extract_node = functools.partial(node_extract_specs, llm_client=llm_client)

    builder = StateGraph(ExtractionState)

    # ── Nœuds ────────────────────────────────────────────────────────────────
    builder.add_node("parse_pdf",      node_parse_pdf)
    builder.add_node("extract_specs",  extract_node)
    builder.add_node("validate_specs", node_validate_specs)

    # ── Edges séquentiels ────────────────────────────────────────────────────
    builder.set_entry_point("parse_pdf")
    builder.add_edge("parse_pdf",     "extract_specs")
    builder.add_edge("extract_specs", "validate_specs")

    # ── Edge conditionnel (retry ou end) ─────────────────────────────────────
    builder.add_conditional_edges(
        "validate_specs",
        should_retry,
        {
            "retry": "extract_specs",   # Relance l'extraction LLM
            "end":   END,
        },
    )

    graph = builder.compile()
    logger.info("[Module 1] Graphe LangGraph compilé avec succès")
    return graph
