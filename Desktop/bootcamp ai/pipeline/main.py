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

    # Sauvegarde du résultat complet
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "pipeline_result.json")

    # Nettoyer les objets non-sérialisables
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

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(_clean(final_state), f, ensure_ascii=False, indent=2)

    if pdf_path:
        print(f"\n  Source PDF : {os.path.basename(pdf_path)}")
    print(f"\n  Résultat complet sauvegardé → {output_path}\n")
    return final_state


if __name__ == "__main__":
    main()
