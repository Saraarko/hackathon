"""
Module 1 — Interface ligne de commande.

Exemples :
    # Avec Anthropic (API key dans ANTHROPIC_API_KEY)
    python -m module_1 --pdf plans/pompe_KSB.pdf --provider anthropic

    # Avec Ollama local (Mistral)
    python -m module_1 --pdf plans/pompe_KSB.pdf --provider ollama

    # PDF KSB de reference (telecharger depuis l'URL publique) :
    # https://www.industrialpumprepair.ca/resource-files/centrifugal-pumps/KSB%20data%20sheet%204025.pdf
"""

from __future__ import annotations
from module_1.config import get_llm_client
import argparse
import logging
import sys
from pathlib import Path


def _configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )


def _build_client(provider: str):
    return get_llm_client()


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="module_1",
        description="Module 1 — Extraction automatique de specs depuis un PDF d'equipement mecanique",
    )
    parser.add_argument("--pdf",        default="plans/pompe_MIFAB_SM_V1_local.pdf")
    parser.add_argument("--provider",   default="anthropic", choices=["anthropic", "ollama"])
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--log-level",  default="INFO")
    parser.add_argument("--no-save",    action="store_true")

    args = parser.parse_args()
    _configure_logging(args.log_level)

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"[ERREUR] Fichier introuvable : {pdf_path}", file=sys.stderr)
        return 1

    try:
        client = _build_client(args.provider)
    except (ImportError, ValueError) as exc:
        print(f"[ERREUR] Client LLM : {exc}", file=sys.stderr)
        return 1

    from module_1 import run

    output_dir = Path(args.output_dir) if args.output_dir else None
    specs = run(
        pdf_path=pdf_path,
        llm_client=client,
        save_output=not args.no_save,
        output_dir=output_dir,
    )

    if specs is None:
        print("[ERREUR] Extraction echouee. Consultez les logs.", file=sys.stderr)
        return 1

    # Resume console
    print("\n" + "─" * 60)
    print("  MODULE 1 — RESULTAT EXTRACTION")
    print("─" * 60)
    print(f"  Reference       : {specs.part_number or specs.model_reference or 'N/A'}")
    print(f"  Fabricant       : {specs.manufacturer or 'N/A'}")
    print(f"  Categorie       : {specs.equipment_category}")
    print(f"  Sous-type       : {specs.equipment_subtype}")
    print(f"  Montage         : {specs.mounting}")
    print(f"  DN entree       : {specs.dimensions.nominal_diameter_mm} mm")
    print(f"  DN sortie       : {specs.dimensions.outlet_diameter_mm} mm")
    print(f"  Pression        : {specs.hydraulics.nominal_pressure_bar} bar")
    print(f"  Debit           : {specs.hydraulics.design_flow_m3h} m³/h")
    print(f"  HMT             : {specs.hydraulics.design_head_m} m")
    print(f"  Rendement       : {specs.hydraulics.efficiency_pct} %")
    print(f"  Vitesse         : {specs.hydraulics.pump_speed_rpm} rpm")
    print(f"  Materiau corps  : {specs.body_material}")
    print(f"  Fluide          : {specs.fluid_type}")
    print(f"  Motorisation    : {specs.drive_type}")
    print(f"  Puissance       : {specs.electrical.rated_power_kw} kW")
    print(f"  Connexion       : {specs.connections.inlet_type} / {specs.connections.flange_standard}")
    print(f"  Normes          : {', '.join(specs.certifications.standards) or 'N/A'}")
    print(f"  Confiance       : {specs.extraction_confidence:.0%}")
    if specs.extraction_warnings:
        print(f"  Avertissements  : {', '.join(specs.extraction_warnings)}")
    print("─" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())