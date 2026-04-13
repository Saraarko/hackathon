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

# S'assure que le dossier pipeline est dans le path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import build_pipeline


def parse_args() -> dict:
    parser = argparse.ArgumentParser(description="Pipeline IA OpenIndustry — Modules 2→3→4→5→6")
    parser.add_argument("--type",        default="valve",              help="Type de pièce")
    parser.add_argument("--diameter",    type=int,   default=100,      help="Diamètre (mm)")
    parser.add_argument("--pressure",    type=int,   default=40,       help="Pression (bar)")
    parser.add_argument("--material",    default="316L",               help="Matériau (ex: 316L)")
    parser.add_argument("--length",      type=int,   default=250,      help="Longueur (mm)")
    parser.add_argument("--quantity",    type=int,   default=200,      help="Quantité à commander")
    parser.add_argument("--budget",      type=float, default=2.5,      help="Budget max EUR/kg")
    args = parser.parse_args()
    return vars(args)


def main():
    args = parse_args()

    print("\n" + "="*55)
    print("  PIPELINE IA — OpenIndustry Algérie")
    print("  Modules 2 → 3 → 4 → 5 → 6")
    print("="*55)
    print(f"  Vanne : ⌀{args['diameter']}mm · {args['pressure']}bar · {args['material']}")
    print(f"  Qty   : {args['quantity']} unités · Budget : {args['budget']} €/kg max")
    print("="*55 + "\n")

    # État initial
    initial_state = {
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
        "summary":             {},
        "errors":              [],
    }

    pipeline = build_pipeline()
    final_state = pipeline.invoke(initial_state)

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

    print(f"\n  Résultat complet sauvegardé → {output_path}\n")
    return final_state


if __name__ == "__main__":
    main()
