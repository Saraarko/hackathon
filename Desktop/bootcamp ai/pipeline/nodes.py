"""
Pipeline Global — Nœuds LangGraph (un par module)

Chaque nœud :
  - reçoit le GlobalState
  - appelle le module correspondant
  - retourne un dict partiel fusionné dans le state
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── helpers ──────────────────────────────────────────────────────────────── #

def _add_path(module_dir: str):
    """Ajoute un répertoire en tête de sys.path (idempotent)."""
    p = os.path.join(ROOT, module_dir)
    if p not in sys.path:
        sys.path.insert(0, p)


def _safe(fn, state: dict, key: str) -> dict:
    """Execute fn(state), capture les exceptions dans state['errors']."""
    try:
        return fn(state)
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(f"[{key}] {type(exc).__name__}: {exc}")
        return {**state, "errors": errors, key: {"error": str(exc)}}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — CAD & Design
# ══════════════════════════════════════════════════════════════════════════════

def node_design(state: dict) -> dict:
    """
    Module 2 : Applique les règles de conception, génère géométrie + fichiers CAD.
    Input  : valve_type, diameter, pressure, material, length
    Output : design_result
    """
    print("\n[Pipeline] ▶ Module 2 — CAD & Design")

    _add_path("module2")

    from graph import build_graph as build_m2

    m2_state = {
        "type":     state.get("valve_type", "valve"),
        "diameter": state.get("diameter", 100),
        "pressure": state.get("pressure", 40),
        "material": state.get("material", "316L"),
        "length":   state.get("length", 250),
    }

    result = build_m2().invoke(m2_state)

    print(f"  ✓ Validation : {result.get('validation', {}).get('status', '?')}")
    print(f"  ✓ Warnings   : {result.get('validation', {}).get('warnings', [])}")

    return {**state, "design_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — Rendu 3D
# ══════════════════════════════════════════════════════════════════════════════

def node_render(state: dict) -> dict:
    """
    Module 3 : Génère le rendu 3D matplotlib de la vanne.
    Input  : design_result (geometry)
    Output : render_result
    """
    print("\n[Pipeline] ▶ Module 3 — Rendu 3D")

    _add_path("module3")

    os.makedirs(os.path.join(ROOT, "pipeline", "outputs"), exist_ok=True)
    orig_dir = os.getcwd()

    try:
        os.chdir(os.path.join(ROOT, "module3"))
        os.makedirs("outputs", exist_ok=True)

        from blender_runner import render_video
        render_video()

        video_path = os.path.join(ROOT, "module3", "outputs", "valve.mp4")
        result = {
            "video_path":   video_path,
            "scene_config": {"material": state.get("material", "316L")},
            "status":       "ok",
        }
        print(f"  ✓ Vidéo : {video_path}")
    finally:
        os.chdir(orig_dir)

    return {**state, "render_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — Sourcing
# ══════════════════════════════════════════════════════════════════════════════

def node_sourcing(state: dict) -> dict:
    """
    Module 4 : Identifie les fournisseurs via Wikidata + UN Comtrade.
    Input  : material (ex: "Stainless Steel 316L")
    Output : sourcing_result → suppliers[], market_analysis, trade_data
    """
    print("\n[Pipeline] ▶ Module 4 — Sourcing fournisseurs")

    _add_path("module4")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))

    from wikidata_agent import WikidataSourceAgent
    from comtrade_agent import ComtradeAgent

    # Normalisation du matériau
    raw_mat = state.get("material", "316L").upper()
    material = "Stainless Steel 316L" if "316" in raw_mat else raw_mat

    wikidata  = WikidataSourceAgent()
    comtrade  = ComtradeAgent()

    sourcing  = wikidata.run(material)
    trade     = comtrade.run(material)

    result = {
        "material":        material,
        "suppliers":       sourcing["suppliers"],
        "market_analysis": sourcing["market_analysis"],
        "trade_data":      trade,
    }

    nb = len(result["suppliers"])
    avg = result["market_analysis"].get("avg_price_eur", 0)
    print(f"  ✓ {nb} fournisseurs · Prix moyen : {avg} €/kg")

    return {**state, "sourcing_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — Négociation
# ══════════════════════════════════════════════════════════════════════════════

def node_negotiation(state: dict) -> dict:
    """
    Module 5 : Négocie avec les top-3 fournisseurs via Claude Haiku.
    Input  : sourcing_result.suppliers, budget_per_unit
    Output : negotiation_result → best_deal, all_negotiations
    """
    print("\n[Pipeline] ▶ Module 5 — Négociation IA (Claude Haiku)")

    _add_path("module5")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))

    from claude_agent import NegotiationAgent

    suppliers = state.get("sourcing_result", {}).get("suppliers", [])
    material  = state.get("sourcing_result", {}).get("material", "Stainless Steel 316L")
    budget    = float(state.get("budget_per_unit", 2.5))

    if not suppliers:
        return {**state, "negotiation_result": {"error": "Aucun fournisseur disponible"}}

    agent  = NegotiationAgent()
    result = agent.negotiate_all(
        suppliers=suppliers[:3],
        material=material,
        budget_eur_per_kg=budget,
    )

    best = result.get("best_deal", {})
    print(f"  ✓ {result.get('total_suppliers_negotiated', 0)} négociations")
    print(f"  ✓ Meilleur deal : {best.get('supplier_name')} à {best.get('counter_offer_price_eur')} €/kg")
    print(f"  ✓ Économies     : {best.get('savings_pct', 0)}%")

    return {**state, "negotiation_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 6 — Analyse financière
# ══════════════════════════════════════════════════════════════════════════════

def node_financial(state: dict) -> dict:
    """
    Module 6 : Projections financières, Monte Carlo, ROI, rapport.
    Input  : coût unitaire négocié × quantité → base_cost
    Output : financial_result → roi, risk, scenarios, report
    """
    print("\n[Pipeline] ▶ Module 6 — Analyse financière")

    _add_path("module6")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))

    from graph import build_graph as build_m6

    # Calcul du coût de base depuis le meilleur deal négocié
    best_deal = state.get("negotiation_result", {}).get("best_deal", {})
    price_per_kg = best_deal.get("counter_offer_price_eur", 2.5)
    quantity     = state.get("quantity", 200)

    # Estimation coût total matière (prix × quantité × 1kg moyen par vanne)
    base_cost = round(price_per_kg * quantity, 2)

    orig_dir = os.getcwd()
    try:
        os.chdir(os.path.join(ROOT, "module6"))
        os.makedirs("outputs", exist_ok=True)

        m6_state = {"base_cost": base_cost}
        result   = build_m6().invoke(m6_state)

        financial_result = {
            "base_cost":  base_cost,
            "roi":        result.get("roi"),
            "risk":       result.get("risk"),
            "scenarios":  result.get("scenarios"),
            "inflation":  result.get("inflation"),
            "total_cost": result.get("total_cost"),
            "mc":         result.get("mc"),
            "status":     "ok",
        }
    finally:
        os.chdir(orig_dir)

    print(f"  ✓ Coût base : {base_cost} €")
    print(f"  ✓ ROI       : {financial_result.get('roi')}")
    print(f"  ✓ Risque    : {financial_result.get('risk')}")

    return {**state, "financial_result": financial_result}


# ══════════════════════════════════════════════════════════════════════════════
# SYNTHÈSE FINALE
# ══════════════════════════════════════════════════════════════════════════════

def node_summary(state: dict) -> dict:
    """Nœud final : construit le résumé exécutif du pipeline."""
    print("\n[Pipeline] ▶ Synthèse finale")

    best_deal = state.get("negotiation_result", {}).get("best_deal", {})
    fin       = state.get("financial_result", {})

    summary = {
        "valve": {
            "type":     state.get("valve_type"),
            "diameter": state.get("diameter"),
            "pressure": state.get("pressure"),
            "material": state.get("material"),
            "validation": state.get("design_result", {}).get("validation", {}),
        },
        "render": {
            "video": state.get("render_result", {}).get("video_path"),
        },
        "sourcing": {
            "total_suppliers": len(state.get("sourcing_result", {}).get("suppliers", [])),
            "avg_market_price": state.get("sourcing_result", {}).get("market_analysis", {}).get("avg_price_eur"),
        },
        "negotiation": {
            "supplier":       best_deal.get("supplier_name"),
            "price_eur_kg":   best_deal.get("counter_offer_price_eur"),
            "savings_pct":    best_deal.get("savings_pct"),
            "recommendation": best_deal.get("final_recommendation"),
        },
        "finance": {
            "base_cost_eur": fin.get("base_cost"),
            "total_cost":    fin.get("total_cost"),
            "roi":           fin.get("roi"),
            "risk":          fin.get("risk"),
        },
        "errors": state.get("errors", []),
    }

    print("\n" + "="*55)
    print("  PIPELINE COMPLET — RÉSUMÉ EXÉCUTIF")
    print("="*55)
    print(f"  Vanne        : ⌀{summary['valve']['diameter']}mm · {summary['valve']['pressure']}bar · {summary['valve']['material']}")
    print(f"  Validation   : {summary['valve']['validation'].get('status', '?')}")
    print(f"  Fournisseurs : {summary['sourcing']['total_suppliers']} identifiés")
    print(f"  Meilleur deal: {summary['negotiation']['supplier']} à {summary['negotiation']['price_eur_kg']} €/kg (-{summary['negotiation']['savings_pct']}%)")
    print(f"  Coût total   : {summary['finance']['base_cost_eur']} €")
    print(f"  ROI          : {summary['finance']['roi']}")
    print(f"  Risque       : {summary['finance']['risk']}")
    if summary["errors"]:
        print(f"  Erreurs      : {len(summary['errors'])}")
        for e in summary["errors"]:
            print(f"    - {e}")
    print("="*55 + "\n")

    return {**state, "summary": summary}
