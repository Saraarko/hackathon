"""
Module 1 — Noeuds LangGraph avec cache + parser factory + confidence objective.
Generalise pour tout equipement mecanique (pompes, vannes, echangeurs, etc.)
"""

from __future__ import annotations
import json
import logging
import re
from typing import Any

from module_1.prompts.extraction_prompt import (
    SYSTEM_PROMPT, build_extraction_prompt, build_tables_summary,
)
from module_1.schemas.specs import MechanicalEquipmentSpecs, compute_confidence
from module_1.schemas.state import ExtractionState

logger = logging.getLogger(__name__)
MAX_PARSE_ATTEMPTS = 3


# ── NODE 1 — Lecture fichier (PDF ou DWG) ─────────────────────────────────────

def node_parse_pdf(state: ExtractionState) -> dict[str, Any]:
    logger.info("[Module 1] Lecture fichier : %s", state.pdf_path)
    try:
        from module_1.parsers.parser_factory import get_parser
        text, tables = get_parser(state.pdf_path)
    except Exception as exc:
        logger.error("[Module 1] Erreur parsing : %s", exc)
        return {"errors": state.errors + [str(exc)]}

    logger.info("[Module 1] Fichier ok — %d chars, %d tableaux", len(text), len(tables))
    return {"pdf_text": text, "pdf_tables": tables}


# ── NODE 2 — Extraction LLM (avec cache) ──────────────────────────────────────

def node_extract_specs(state: ExtractionState, llm_client) -> dict[str, Any]:
    logger.info("[Module 1] Extraction LLM (tentative %d)", state.parse_attempts + 1)

    from module_1.cache.cache_manager import get_cache_key, load_from_cache, save_to_cache
    cache_key = get_cache_key(state.pdf_path)
    cached    = load_from_cache(cache_key)
    if cached:
        logger.info("[Module 1] Resultat depuis cache")
        return {"raw_llm_response": cached, "parse_attempts": state.parse_attempts + 1}

    tables_summary = build_tables_summary(state.pdf_tables)
    user_prompt    = build_extraction_prompt(state.pdf_text, tables_summary)

    try:
        raw = _call_llm(llm_client, user_prompt)
        save_to_cache(cache_key, raw)
    except Exception as exc:
        logger.error("[Module 1] Erreur LLM : %s", exc)
        return {"errors": state.errors + [f"LLM error: {exc}"],
                "parse_attempts": state.parse_attempts + 1}

    return {"raw_llm_response": raw, "parse_attempts": state.parse_attempts + 1}


# ── NODE 3 — Validation + confidence objective ────────────────────────────────

def node_validate_specs(state: ExtractionState) -> dict[str, Any]:
    logger.info("[Module 1] Validation des specs")
    raw = state.raw_llm_response
    if not raw:
        return {"errors": state.errors + ["Reponse LLM vide"]}

    # Nettoyer les fences markdown que le LLM pourrait ajouter
    raw = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data  = json.loads(raw)
        specs = MechanicalEquipmentSpecs(**data)
    except json.JSONDecodeError as exc:
        return {"errors": state.errors + [f"JSON invalide: {exc}"]}
    except Exception as exc:
        return {"errors": state.errors + [f"Pydantic: {exc}"]}

    # Remplace l'auto-notation LLM par une confidence objective
    specs.extraction_confidence = compute_confidence(specs)

    # Avertissements sur champs critiques manquants
    warnings = []
    if not specs.dimensions.nominal_diameter_mm:
        warnings.append("DN manquant")
    if not specs.hydraulics.nominal_pressure_bar:
        warnings.append("Pression nominale manquante")
    if specs.body_material == "unknown":
        warnings.append("Materiau corps non identifie")
    if specs.fluid_type == "unknown":
        warnings.append("Fluide non identifie")
    if specs.equipment_category == "unknown":
        warnings.append("Categorie equipement non identifiee")
    if not specs.hydraulics.design_flow_m3h and specs.equipment_category == "pump":
        warnings.append("Debit nominal manquant (pompe)")

    specs.extraction_warnings = warnings

    logger.info("[Module 1] Specs validees — %s / %s / confiance %.0f%%",
                specs.equipment_category,
                specs.equipment_subtype,
                specs.extraction_confidence * 100)
    return {"specs": specs, "extraction_done": True, "validation_passed": True}


# ── Edge condition ─────────────────────────────────────────────────────────────

def should_retry(state: ExtractionState) -> str:
    if state.validation_passed:
        return "end"
    if state.parse_attempts < MAX_PARSE_ATTEMPTS:
        return "retry"
    return "end"


# ── LLM dispatcher ─────────────────────────────────────────────────────────────

def _call_llm(client, user_prompt: str) -> str:
    client_type = type(client).__name__
    if client_type == "Anthropic":
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return response.content[0].text
    if hasattr(client, "chat"):
        response = client.chat(
            model="mistral",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
        )
        return response["message"]["content"]
    raise ValueError(f"Client LLM non reconnu : {client_type}")
