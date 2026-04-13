"""
Module 1 — Cache des résultats LLM.
Évite de re-appeler l'API Anthropic si le même PDF est soumis deux fois.
Le cache est stocké dans module_1/cache/.cache/ sous forme de fichiers JSON.
"""

from __future__ import annotations
import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent / ".cache"


def get_cache_key(pdf_path: str | Path) -> str:
    """Calcule le hash MD5 du fichier PDF — sert de clé de cache."""
    with open(pdf_path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def load_from_cache(cache_key: str) -> str | None:
    """
    Retourne la réponse LLM mise en cache, ou None si absente.
    """
    cache_file = CACHE_DIR / f"{cache_key}.json"
    if not cache_file.exists():
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("[Cache] Hit — clé %s", cache_key[:8])
        return data.get("llm_response")
    except Exception as exc:
        logger.warning("[Cache] Lecture échouée : %s", exc)
        return None


def save_to_cache(cache_key: str, llm_response: str) -> None:
    """
    Sauvegarde la réponse LLM dans le cache.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{cache_key}.json"
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"llm_response": llm_response}, f, ensure_ascii=False)
        logger.info("[Cache] Sauvegardé — clé %s", cache_key[:8])
    except Exception as exc:
        logger.warning("[Cache] Écriture échouée : %s", exc)


def clear_cache() -> int:
    """Vide le cache. Retourne le nombre de fichiers supprimés."""
    if not CACHE_DIR.exists():
        return 0
    count = 0
    for f in CACHE_DIR.glob("*.json"):
        f.unlink()
        count += 1
    logger.info("[Cache] Vidé — %d fichiers supprimés", count)
    return count
