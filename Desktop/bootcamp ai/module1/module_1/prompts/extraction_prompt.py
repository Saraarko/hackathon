"""
Module 1 — Prompts d'extraction pour equipements mecaniques industriels generiques.
Supporte : pompes, vannes, echangeurs, compresseurs, et tout autre equipement.
"""

SYSTEM_PROMPT = """
Tu es un ingenieur mecanique senior specialise dans la lecture de plans techniques industriels.
Tu analyses des documents PDF/DXF d'equipements mecaniques (pompes, vannes, echangeurs, compresseurs...)
et tu extrais les specifications techniques avec precision.

REGLES STRICTES :
1. Reponds UNIQUEMENT avec un objet JSON valide — aucun texte avant ou apres.
2. Si une valeur est absente du document, utilise null. Ne jamais inventer une valeur.
3. Les valeurs numeriques sont des nombres (float/int), jamais des strings.
4. equipment_category doit etre exactement : "pump", "valve", "heat_exchanger", "compressor",
   "reducer", "pressure_vessel", "filter", "actuator", "motor" ou "unknown"
5. equipment_subtype depend de la categorie. Pour une pompe : "centrifugal", "axial", "gear_pump",
   "screw_pump", "piston_pump", "diaphragm_pump", "submersible_pump" ou "unknown".
   Pour une vanne : "ball_valve", "gate_valve", "butterfly_valve", "check_valve",
   "globe_valve", "safety_valve" ou "unknown".
6. body_material doit etre exactement : "316L", "304", "316", "1.4462", "1.4408", "1.4571",
   "carbon_steel", "cast_iron", "bronze", "hastelloy_c276", "titanium", "aluminum",
   "cast_steel" ou "unknown"
7. fluid_type : "water", "clean_water", "seawater", "steam", "gas", "oil", "acid",
   "slurry", "chemical" ou "unknown"
8. connections.inlet_type et outlet_type : "flanged", "threaded", "butt_weld",
   "socket_weld", "triclamp", "victaulic" ou "unknown"
9. drive_type : "electric_motor", "diesel_engine", "steam_turbine", "pneumatic",
   "hydraulic", "manual" ou "unknown"
10. mounting : "horizontal", "vertical", "inclined" ou "unknown"
11. nominal_diameter_mm doit etre extrait depuis :
- "DN xx"
- "DN1 DN xx"
- "DN2 DN xx"
- "Suction nominal dia."
- "Discharge nominal dia."
- "Nominal size DN"

Mapping obligatoire :
- DN suction → dimensions.nominal_diameter_mm
- DN discharge → dimensions.outlet_diameter_mm

Exemples :
"Suction nominal dia. DN 65" → nominal_diameter_mm = 65
"Discharge nominal dia. DN 50" → outlet_diameter_mm = 50
"""


def build_extraction_prompt(pdf_text: str, tables_summary: str = "") -> str:
    MAX_CHARS = 12_000
    if len(pdf_text) > MAX_CHARS:
        pdf_text = pdf_text[:MAX_CHARS] + "\n[... texte tronque ...]"

    tables_section = f"\nTABLEAUX DETECTES :\n{tables_summary}" if tables_summary else ""

    return f"""Analyse ce document technique d'equipement mecanique industriel
et extrais toutes les specifications disponibles.

TEXTE DU DOCUMENT :
{pdf_text}
{tables_section}

Reponds avec ce schema JSON exact :
{{
  "part_number": null,
  "revision": null,
  "drawing_number": null,
  "description": null,
  "manufacturer": null,
  "model_reference": null,
  "equipment_category": "unknown",
  "equipment_subtype": "unknown",
  "mounting": "unknown",
  "dimensions": {{
    "nominal_diameter_mm": null,
    "outlet_diameter_mm": null,
    "face_to_face_mm": null,
    "overall_length_mm": null,
    "overall_width_mm": null,
    "overall_height_mm": null,
    "weight_kg": null,
    "weight_total_kg": null,
    "wall_thickness_mm": null,
    "bore_diameter_mm": null,
    "impeller_diameter_mm": null,
    "drawing_scale": null
  }},
  "hydraulics": {{
    "nominal_pressure_bar": null,
    "max_operating_bar": null,
    "test_pressure_bar": null,
    "pressure_class": null,
    "design_flow_m3h": null,
    "max_flow_m3h": null,
    "min_flow_m3h": null,
    "design_head_m": null,
    "shutoff_head_m": null,
    "efficiency_pct": null,
    "npsh_required_m": null,
    "pump_speed_rpm": null,
    "max_flow_velocity_ms": null
  }},
  "temperature": {{
    "min_temp_celsius": null,
    "max_temp_celsius": null,
    "design_temp_celsius": null
  }},
  "body_material": "unknown",
  "impeller_material": null,
  "shaft_material": null,
  "trim_material": null,
  "seal_material": null,
  "fluid_type": "unknown",
  "fluid_density_kg_m3": null,
  "fluid_viscosity_mm2s": null,
  "connections": {{
    "inlet_type": "unknown",
    "outlet_type": "unknown",
    "flange_standard": null,
    "bolt_standard": null,
    "bolt_material": null,
    "bolt_size": null
  }},
  "drive_type": "unknown",
  "electrical": {{
    "rated_power_kw": null,
    "voltage_v": null,
    "frequency_hz": null,
    "rated_current_a": null,
    "motor_efficiency_class": null,
    "motor_enclosure": null,
    "number_of_poles": null,
    "insulation_class": null
  }},
  "sealing": {{
    "seal_type": null,
    "seal_material": null,
    "seal_code": null,
    "sealing_plan": null
  }},
  "tolerances": {{
    "dimensional_tolerance": null,
    "surface_finish_ra": null,
    "leakage_class": null,
    "acceptance_standard": null
  }},
  "surface_treatment": {{
    "coating": null,
    "paint_color": null,
    "internal_lining": null
  }},
  "certifications": {{
    "standards": [],
    "markings": []
  }},
  "quantity_required": 200,
  "extraction_confidence": 0.0,
  "extraction_warnings": []
}}
"""


def build_tables_summary(tables: list[dict]) -> str:
    if not tables:
        return ""
    lines = []
    for i, t in enumerate(tables, 1):
        headers = " | ".join(t.get("headers", []))
        lines.append(f"Tableau {i} (page {t.get('page','?')}) — {headers}")
        for row in t.get("rows", [])[:5]:
            lines.append("  " + " | ".join(row))
    return "\n".join(lines)
