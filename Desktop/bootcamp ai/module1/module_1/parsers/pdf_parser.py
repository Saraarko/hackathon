"""
Module 1 — Parseur PDF.
Extrait le texte brut et les tableaux depuis un PDF technique
en utilisant pdfplumber (meilleure fidélité sur les plans industriels).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Import conditionnel : pdfplumber optionnel en CI/test ──────────────────
try:
    import pdfplumber
    _PDFPLUMBER_AVAILABLE = True
except ImportError:
    _PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber non installé — utilisation du fallback texte vide")


class PDFParseError(Exception):
    """Erreur de lecture PDF non récupérable."""


class PDFParser:
    """
    Extrait texte brut + tableaux depuis un PDF industriel.

    Usage:
        parser = PDFParser("plans/vanne_DN100.pdf")
        text   = parser.extract_text()
        tables = parser.extract_tables()
    """

    def __init__(self, pdf_path: str | Path, max_pages: int = 30):
        self.pdf_path  = Path(pdf_path)
        self.max_pages = max_pages

        if not self.pdf_path.exists():
            raise PDFParseError(f"Fichier introuvable : {self.pdf_path}")
        if self.pdf_path.suffix.lower() != ".pdf":
            raise PDFParseError(f"Extension non supportée : {self.pdf_path.suffix}")

    # ─────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────

    def extract_text(self) -> str:
        """
        Retourne le texte concaténé de toutes les pages.
        Chaque page est séparée par un marqueur pour faciliter
        le découpage par le LLM.
        """
        if not _PDFPLUMBER_AVAILABLE:
            logger.error("pdfplumber absent — retour texte vide")
            return ""

        pages_text: list[str] = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                pages = pdf.pages[: self.max_pages]
                for i, page in enumerate(pages, start=1):
                    raw = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
                    cleaned = self._clean_page_text(raw)
                    if cleaned:
                        pages_text.append(f"--- PAGE {i} ---\n{cleaned}")

        except Exception as exc:
            raise PDFParseError(f"Erreur lecture PDF : {exc}") from exc

        full_text = "\n\n".join(pages_text)
        logger.info("PDF parsé : %d pages, %d caractères", len(pages_text), len(full_text))
        return full_text

    def extract_tables(self) -> list[dict]:
        """
        Retourne les tableaux détectés, normalisés en liste de dicts
        {headers: [...], rows: [[...], ...]}.
        """
        if not _PDFPLUMBER_AVAILABLE:
            return []

        all_tables: list[dict] = []
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages[: self.max_pages], start=1):
                    for table in page.extract_tables() or []:
                        normalized = self._normalize_table(table, page_num=i)
                        if normalized:
                            all_tables.append(normalized)
        except Exception as exc:
            logger.warning("Extraction tableaux échouée : %s", exc)

        logger.info("Tableaux extraits : %d", len(all_tables))
        return all_tables

    # ─────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────

    @staticmethod
    def _clean_page_text(text: str) -> str:
        """Nettoie les artefacts courants des PDFs techniques."""
        lines = text.splitlines()
        cleaned = []
        for line in lines:
            line = line.strip()
            # Ignore les lignes trop courtes (numéros de page, artefacts OCR)
            if len(line) < 2:
                continue
            # Normalise les espaces multiples
            while "  " in line:
                line = line.replace("  ", " ")
            cleaned.append(line)
        return "\n".join(cleaned)

    @staticmethod
    def _normalize_table(raw_table: list[list], page_num: int) -> Optional[dict]:
        """Convertit une table pdfplumber brute en dict structuré."""
        if not raw_table or len(raw_table) < 2:
            return None

        # Première ligne = headers (si non-None)
        headers = [str(h or "").strip() for h in raw_table[0]]
        rows = []
        for row in raw_table[1:]:
            cleaned_row = [str(cell or "").strip() for cell in row]
            if any(cleaned_row):          # ignore lignes vides
                rows.append(cleaned_row)

        if not headers or not rows:
            return None

        return {"page": page_num, "headers": headers, "rows": rows}
