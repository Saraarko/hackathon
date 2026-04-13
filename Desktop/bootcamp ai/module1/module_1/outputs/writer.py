"""
Module 1 — Persistance des sorties.
Produit le JSON principal + des vues specialisees pour tous les modules avals.
Compatible modules 2, 4, 6, 7, 8, 9 du pipeline INDUSTRIE IA.
"""

from __future__ import annotations
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from module_1.schemas.specs import MechanicalEquipmentSpecs

logger     = logging.getLogger(__name__)
OUTPUT_DIR = Path(__file__).parent


def save_specs_json(
    specs: MechanicalEquipmentSpecs,
    source_pdf: str = "",
    output_dir: Path | None = None,
) -> Path:
    """Sauvegarde principale — JSON complet avec _meta."""
    out_dir   = output_dir or OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    part_slug = (
        specs.part_number or specs.model_reference or "unknown"
    ).replace("/", "-").replace(" ", "_")
    filepath  = out_dir / f"specs_{part_slug}_{timestamp}.json"

    payload = {
        "_meta": {
            "module":           "module_1",
            "pipeline":         "INDUSTRIE_IA",
            "source_pdf":       source_pdf,
            "generated":        timestamp,
            "schema_version":   "3.0.0",
            "equipment_type":   specs.equipment_category,
        },
        "specs": specs.dict(),
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)

    logger.info("[Module 1] JSON principal : %s", filepath)

    # Exports specialises pour modules avals
    _export_for_module2(specs, out_dir, timestamp)
    _export_for_module4(specs, out_dir, timestamp)
    _export_for_module6(specs, out_dir, timestamp)

    return filepath


def _export_for_module2(specs: MechanicalEquipmentSpecs, out_dir: Path, ts: str) -> None:
    """
    Module 2 (Plans CAD) — dimensions + tolerances + connexions.
    Le generateur DXF/IFC a besoin des cotes et du type de raccordement.
    """
    data = {
        "equipment_category":  specs.equipment_category,
        "equipment_subtype":   specs.equipment_subtype,
        "mounting":            specs.mounting,
        "dimensions": {
            "nominal_diameter_mm":  specs.dimensions.nominal_diameter_mm,
            "outlet_diameter_mm":   specs.dimensions.outlet_diameter_mm,
            "face_to_face_mm":      specs.dimensions.face_to_face_mm,
            "overall_length_mm":    specs.dimensions.overall_length_mm,
            "overall_width_mm":     specs.dimensions.overall_width_mm,
            "overall_height_mm":    specs.dimensions.overall_height_mm,
            "impeller_diameter_mm": specs.dimensions.impeller_diameter_mm,
            "weight_kg":            specs.dimensions.weight_kg,
            "drawing_scale":        specs.dimensions.drawing_scale,
        },
        "tolerances": {
            "dimensional_tolerance": specs.tolerances.dimensional_tolerance,
            "surface_finish_ra":     specs.tolerances.surface_finish_ra,
            "acceptance_standard":   specs.tolerances.acceptance_standard,
        },
        "connections": {
            "inlet_type":      specs.connections.inlet_type,
            "outlet_type":     specs.connections.outlet_type,
            "flange_standard": specs.connections.flange_standard,
        },
        "quantity": specs.quantity_required,
    }
    _write(out_dir / f"for_module2_{ts}.json", data)


def _export_for_module4(specs: MechanicalEquipmentSpecs, out_dir: Path, ts: str) -> None:
    """
    Module 4 (Sourcing fournisseurs) — materiaux + quantite + pression + fluide.
    Wikidata / UN Comtrade ont besoin de ces donnees pour identifier les fournisseurs.
    """
    data = {
        "body_material":      specs.body_material,
        "impeller_material":  specs.impeller_material,
        "shaft_material":     specs.shaft_material,
        "seal_material":      specs.seal_material,
        "trim_material":      specs.trim_material,
        "fluid_type":         specs.fluid_type,
        "nominal_pressure_bar": specs.hydraulics.nominal_pressure_bar,
        "nominal_diameter_mm":  specs.dimensions.nominal_diameter_mm,
        "equipment_category": specs.equipment_category,
        "equipment_subtype":  specs.equipment_subtype,
        "quantity":           specs.quantity_required,
        "certifications": {
            "standards": specs.certifications.standards,
            "markings":  specs.certifications.markings,
        },
    }
    _write(out_dir / f"for_module4_{ts}.json", data)


def _export_for_module6(specs: MechanicalEquipmentSpecs, out_dir: Path, ts: str) -> None:
    """
    Module 6 (TCO — Total Cost of Ownership) — specs pour calcul du cout total.
    Le calcul TCO World Bank a besoin des caracteristiques techniques completes.
    """
    data = {
        "part_number":        specs.part_number,
        "model_reference":    specs.model_reference,
        "equipment_category": specs.equipment_category,
        "equipment_subtype":  specs.equipment_subtype,
        "body_material":      specs.body_material,
        "drive_type":         specs.drive_type,
        "electrical": {
            "rated_power_kw":         specs.electrical.rated_power_kw,
            "motor_efficiency_class": specs.electrical.motor_efficiency_class,
            "motor_enclosure":        specs.electrical.motor_enclosure,
        },
        "hydraulics": {
            "design_flow_m3h":     specs.hydraulics.design_flow_m3h,
            "design_head_m":       specs.hydraulics.design_head_m,
            "efficiency_pct":      specs.hydraulics.efficiency_pct,
            "nominal_pressure_bar":specs.hydraulics.nominal_pressure_bar,
        },
        "surface_treatment": specs.surface_treatment.dict(),
        "sealing": {
            "seal_type":  specs.sealing.seal_type,
            "seal_code":  specs.sealing.seal_code,
        },
        "weight_kg":      specs.dimensions.weight_kg,
        "weight_total_kg": specs.dimensions.weight_total_kg,
        "quantity":       specs.quantity_required,
        "pressure_class": specs.hydraulics.pressure_class,
    }
    _write(out_dir / f"for_module6_{ts}.json", data)


def _write(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    logger.info("[Module 1] Export : %s", path.name)


def load_specs_json(filepath: str | Path) -> MechanicalEquipmentSpecs:
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return MechanicalEquipmentSpecs(**(data.get("specs", data)))
