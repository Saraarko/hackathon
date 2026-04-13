"""
Pipeline Global — Point d'entrée

Orchestre les modules 2, 3, 4, 5, 6 dans un seul graphe LangGraph.

Usage :
    cd pipeline
    python main.py

    # Ou avec paramètres personnalisés :
    python main.py --diameter 150 --pressure 60 --quantity 500
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

# Force UTF-8 output on Windows consoles that default to cp1252
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# S'assure que le dossier pipeline est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_pipeline


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="Pipeline IA OpenIndustry — Modules 1→2→3→4→5→6")
    parser.add_argument("--pdf",        default=None,                 help="Chemin vers le PDF technique (active module 1)")
    parser.add_argument("--type",        default="valve",              help="Type de pièce (écrasé par --pdf)")
    parser.add_argument("--diameter",    type=int,   default=100,      help="Diamètre mm (écrasé par --pdf)")
    parser.add_argument("--pressure",    type=int,   default=40,       help="Pression bar (écrasée par --pdf)")
    parser.add_argument("--material",    default="316L",               help="Matériau (écrasé par --pdf)")
    parser.add_argument("--length",      type=int,   default=250,      help="Longueur mm (écrasée par --pdf)")
    parser.add_argument("--quantity",    type=int,   default=200,      help="Quantité à commander")
    parser.add_argument("--budget",      type=float, default=2.5,      help="Budget max EUR/kg")
    args = parser.parse_args()
    return vars(args)


def main():
    args = parse_args()

    pdf_path = os.path.abspath(args["pdf"]) if args["pdf"] else ""

    print("\n" + "="*55)
    print("  PIPELINE IA — OpenIndustry Algérie")
    print("  Modules 1 → 2 → 3 → 4 → 5 → 6")
    print("="*55)
    if pdf_path:
        print(f"  PDF    : {os.path.basename(pdf_path)}")
        print(f"  Qty    : {args['quantity']} unités · Budget : {args['budget']} €/kg max")
        print("  (specs extraites automatiquement par module 1)")
    else:
        print(f"  Vanne : ⌀{args['diameter']}mm · {args['pressure']}bar · {args['material']}")
        print(f"  Qty   : {args['quantity']} unités · Budget : {args['budget']} €/kg max")
        print("  (pas de PDF — paramètres manuels utilisés)")
    print("="*55 + "\n")

    # État initial
    initial_state = {
        "pdf_path":        pdf_path,
        "extraction_result": {},
        "valve_type":      args["type"],
        "diameter":        args["diameter"],
        "pressure":        args["pressure"],
        "material":        args["material"],
        "length":          args["length"],
        "quantity":        args["quantity"],
        "budget_per_unit": args["budget"],
        # Champs résultats initialisés vides
        "design_result":       {},
        "render_result":       {},
        "sourcing_result":     {},
        "negotiation_result":  {},
        "financial_result":    {},
        "businessplan_result": {},
        "summary":             {},
        "errors":              [],
    }

    pipeline = build_pipeline()
    
    t0 = time.time()
    final_state = pipeline.invoke(initial_state)
    duration = time.time() - t0

    print(f"\n  ⏱️  Durée totale du pipeline : {duration:.1f}s")

    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # ── Nettoyage des objets non-sérialisables ────────────────────────────── #
    def _clean(obj):
        if isinstance(obj, dict):
            return {k: _clean(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_clean(i) for i in obj]
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)

    def _save(filename: str, data: dict):
        path = os.path.join(output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_clean(data), f, ensure_ascii=False, indent=2)
        print(f"  ✓ {filename}")
        return path

    # ── Outputs structurés par module ─────────────────────────────────────── #
    print("\n  Sauvegarde des outputs :")

    _save("module1_extraction.json", {
        "source_pdf":        os.path.basename(pdf_path) if pdf_path else None,
        "equipment_type":    final_state.get("valve_type"),
        "diameter_mm":       final_state.get("diameter"),
        "pressure_bar":      final_state.get("pressure"),
        "material":          final_state.get("material"),
        "length_mm":         final_state.get("length"),
        "quantity":          final_state.get("quantity"),
        "extraction_result": final_state.get("extraction_result", {}),
    })

    _save("module2_design.json", {
        "inputs": {
            "type":     final_state.get("valve_type"),
            "diameter": final_state.get("diameter"),
            "pressure": final_state.get("pressure"),
            "material": final_state.get("material"),
            "length":   final_state.get("length"),
        },
        "design_result": final_state.get("design_result", {}),
    })

    render = final_state.get("render_result", {})
    _save("module3_render.json", {
        "video_path":   render.get("video_path"),
        "scene_config": render.get("scene_config"),
        "status":       render.get("status"),
    })

    sourcing = final_state.get("sourcing_result", {})
    _save("module4_sourcing.json", {
        "material":        sourcing.get("material"),
        "search_mode":     sourcing.get("market_analysis", {}).get("search_mode"),
        "equipment_type":  sourcing.get("market_analysis", {}).get("equipment_type"),
        "total_suppliers": len(sourcing.get("suppliers", [])),
        "suppliers":       sourcing.get("suppliers", []),
        "market_analysis": sourcing.get("market_analysis", {}),
        "trade_data":      sourcing.get("trade_data", {}),
    })

    nego = final_state.get("negotiation_result", {})
    _save("module5_negotiation.json", {
        "product":                    f"{final_state.get('valve_type')} DN{final_state.get('diameter')} {final_state.get('material')}",
        "quantity":                   final_state.get("quantity"),
        "total_suppliers_negotiated": nego.get("total_suppliers_negotiated"),
        "best_deal":                  nego.get("best_deal", {}),
        "all_negotiations":           nego.get("all_negotiations", []),
    })

    fin = final_state.get("financial_result", {})
    _save("module6_financial.json", {
        "base_cost_eur":  fin.get("base_cost"),
        "total_cost_eur": fin.get("total_cost"),
        "roi":            fin.get("roi"),
        "risk":           fin.get("risk"),
        "scenarios":      fin.get("scenarios"),
        "inflation":      fin.get("inflation"),
        "monte_carlo":    fin.get("mc"),
    })

    bp = final_state.get("businessplan_result", {})
    _save("module7_businessplan.json", {
        "decision":    bp.get("decision"),
        "npv_3y":      bp.get("npv"),
        "financials":  bp.get("financials", {}),
        "projections": bp.get("projections", []),
        "swot":        bp.get("swot"),
        "summary":     bp.get("summary"),
        "exports": {
            "pdf":   bp.get("pdf_path"),
            "excel": bp.get("excel_path"),
        },
    })

    # ── Résultat complet (tous modules) ──────────────────────────────────── #
    _save("pipeline_result.json", final_state)

    if pdf_path:
        print(f"\n  Source PDF : {os.path.basename(pdf_path)}")
    print(f"\n  Outputs sauvegardés dans : {output_dir}\n")
    return final_state


if __name__ == "__main__":
    main()
