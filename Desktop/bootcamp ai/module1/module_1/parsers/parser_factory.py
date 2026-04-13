"""
Module 1 — Factory de parseurs.
Détecte automatiquement le format (PDF/DXF/DWG) et retourne le bon parseur.
Gère aussi la détection PDF natif vs scanné (bascule OCR si nécessaire).
"""

from __future__ import annotations
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Seuil : moins de 100 caractères = PDF probablement scanné
OCR_FALLBACK_THRESHOLD = 600


def get_parser(file_path: str | Path):
    """
    Retourne le parseur adapté selon l'extension du fichier.
    Pour les PDFs, bascule automatiquement sur OCR si le texte natif est insuffisant.

    Returns:
        tuple(text: str, tables: list[dict])
    """
    path = Path(file_path)
    ext  = path.suffix.lower()

    if ext == ".pdf":
        return _parse_pdf(path)
    else:
     raise ValueError(f"Format non supporté : {ext}. Seul .pdf est accepté.")


def _parse_pdf(path: Path):
    from module_1.parsers.pdf_parser import PDFParser
    parser = PDFParser(path)
    text   = parser.extract_text()
    tables = parser.extract_tables()

    # Bascule OCR si texte insuffisant (PDF scanné)
    if len(text.strip()) < OCR_FALLBACK_THRESHOLD:
        logger.warning("Texte PDF insuffisant (%d chars) — tentative OCR", len(text.strip()))
        text = _ocr_fallback(path) or text

    return text, tables


def _parse_dwg(path: Path):
    from module_1.parsers.dwg_parser import DWGParser
    parser = DWGParser(path)
    text   = parser.extract_text()
    return text, []   # DXF ne produit pas de tableaux structurés


def _ocr_fallback(path: Path) -> str:
    """
    OCR via pytesseract sur un PDF scanné.
    Nécessite : pip install pytesseract pdf2image
    et Tesseract installé sur le système.
    """
    try:
        from pdf2image import convert_from_path  # type: ignore
        import pytesseract                        # type: ignore

        logger.info("OCR en cours sur : %s", path.name)
        images = convert_from_path(str(path), dpi=300)
        pages  = []
        for i, img in enumerate(images, 1):
            page_text = pytesseract.image_to_string(img, lang="fra+eng")
            pages.append(f"--- PAGE {i} (OCR) ---\n{page_text}")

        full = "\n\n".join(pages)
        logger.info("OCR terminé : %d caractères extraits", len(full))
        return full

    except ImportError:
        logger.warning("pytesseract/pdf2image non installés — OCR ignoré")
        return ""
    except Exception as exc:
        logger.warning("Échec OCR : %s", exc)
        return ""
