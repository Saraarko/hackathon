"""
Pipeline Global — État partagé entre tous les modules (1→2→3→4→5→6)
"""

from __future__ import annotations
from typing import TypedDict, Optional


class GlobalState(TypedDict):
    # ── Module 1 : Extraction PDF ────────────────────────────────────────── #
    pdf_path:          str    # chemin vers le PDF technique
    extraction_result: dict   # specs complètes extraites par module1

    # ── Entrée (peuplée par module1 ou par défaut) ───────────────────────── #
    valve_type:     str    # "valve", "pump", etc.
    diameter:       int    # mm
    pressure:       int    # bar
    material:       str    # "316L"
    length:         int    # mm
    quantity:       int    # nb unités à commander
    budget_per_unit: float # EUR/unité max acceptable

    # ── Module 2 : CAD & Design ──────────────────────────────────────────── #
    design_result:  dict   # geometry, fichiers, validation

    # ── Module 3 : Rendu 3D ──────────────────────────────────────────────── #
    render_result:  dict   # video_path, scene_config

    # ── Module 4 : Sourcing ──────────────────────────────────────────────── #
    sourcing_result: dict  # suppliers[], market_analysis, trade_data

    # ── Module 5 : Négociation ───────────────────────────────────────────── #
    negotiation_result: dict  # best_deal, all_negotiations

    # ── Module 6 : Finance ───────────────────────────────────────────────── #
    financial_result: dict    # roi, risk, scenarios, report

    # ── Module 7 : Business Plan ──────────────────────────────────────── #
    businessplan_result: dict  # financials, projections, npv, decision, swot, summary

    # ── Méta ─────────────────────────────────────────────────────────────── #
    errors:  list[str]
    summary: dict

