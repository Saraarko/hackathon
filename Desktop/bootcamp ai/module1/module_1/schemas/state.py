"""
Module 1 — Etat LangGraph partage entre les noeuds du pipeline d'extraction.
Generalise pour tout type d'equipement mecanique industriel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from module_1.schemas.specs import MechanicalEquipmentSpecs


@dataclass
class ExtractionState:
    """Etat mutable transmis a travers le graphe LangGraph Module 1."""

    # Input
    pdf_path   : str = ""
    pdf_text   : str = ""           # texte brut extrait par pdfplumber
    pdf_tables : list[dict] = field(default_factory=list)

    # Processing
    raw_llm_response : str = ""     # reponse JSON brute du LLM
    parse_attempts   : int = 0      # compteur de tentatives de parsing

    # Output
    specs  : Optional[MechanicalEquipmentSpecs] = None
    errors : list[str] = field(default_factory=list)

    # Pipeline control
    extraction_done   : bool = False
    validation_passed : bool = False
