"""
Module 4 — Agent Made-in-China.com
Scrape les prix des équipements industriels sur made-in-china.com
et retourne min, max et prix moyen USD.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://www.made-in-china.com/products-search/hot-china-products/{query}.html"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Mapping type équipement → termes de recherche MIC
EQUIPMENT_SEARCH_TERMS: dict[str, str] = {
    "pump":            "stainless_steel_pump",
    "centrifugal":     "centrifugal_pump",
    "valve":           "stainless_steel_valve",
    "heat_exchanger":  "heat_exchanger",
    "compressor":      "industrial_compressor",
    "filter":          "industrial_filter",
    "motor":           "electric_motor",
    "reducer":         "gear_reducer",
    "pressure_vessel": "pressure_vessel",
    "actuator":        "pneumatic_actuator",
}

MATERIAL_SEARCH_TERMS: dict[str, str] = {
    "stainless steel 316l": "316L_stainless_steel",
    "titanium":             "titanium_metal",
    "aluminum":             "aluminum_alloy",
    "iron":                 "cast_iron",
    "nickel":               "nickel_alloy",
}


class MadeInChinaAgent:
    """Scrape les prix sur made-in-china.com pour un équipement ou matériau donné."""

    def run(
        self,
        equipment_type: str = "unknown",
        material: str = "",
    ) -> dict[str, Any]:
        """
        Retourne :
        {
          "prices":      [{"title": ..., "price_min": ..., "price_max": ..., "unit": ..., "supplier": ...}],
          "price_min":   float,
          "price_max":   float,
          "price_avg":   float,
          "currency":    "USD",
          "source":      "Made-in-China.com",
          "search_term": str,
        }
        """
        query = self._resolve_query(equipment_type, material)
        url   = BASE_URL.format(query=query)
        logger.info("[MIC] Scraping : %s", url)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
        except Exception as exc:
            logger.warning("[MIC] Erreur HTTP : %s", exc)
            return self._empty(query)

        prices = self._parse_prices(resp.text)

        if not prices:
            logger.warning("[MIC] Aucun prix trouvé pour '%s'", query)
            return self._empty(query)

        all_mins = [p["price_min"] for p in prices if p["price_min"] > 0]
        all_maxs = [p["price_max"] for p in prices if p["price_max"] > 0]
        all_vals = all_mins + all_maxs

        return {
            "prices":      prices,
            "price_min":   round(min(all_mins), 2) if all_mins else 0.0,
            "price_max":   round(max(all_maxs), 2) if all_maxs else 0.0,
            "price_avg":   round(sum(all_vals) / len(all_vals), 2) if all_vals else 0.0,
            "currency":    "USD",
            "source":      "Made-in-China.com",
            "search_term": query.replace("_", " "),
            "url":         url,
        }

    # ── Helpers ───────────────────────────────────────────────────────────── #

    def _resolve_query(self, equipment_type: str, material: str) -> str:
        key_eq = equipment_type.lower().strip()
        # Essai correspondance exacte ou partielle sur l'équipement
        for k, term in EQUIPMENT_SEARCH_TERMS.items():
            if k in key_eq or key_eq in k:
                return term
        # Fallback sur le matériau
        key_mat = material.lower().strip()
        for k, term in MATERIAL_SEARCH_TERMS.items():
            if k in key_mat or key_mat in k:
                return term
        return "industrial_equipment"

    @staticmethod
    def _parse_prices(html: str) -> list[dict]:
        soup   = BeautifulSoup(html, "html.parser")
        items  = []

        price_pattern = re.compile(
            r"US\$\s*([\d,]+\.?\d*)\s*(?:-\s*([\d,]+\.?\d*))?",
            re.IGNORECASE,
        )

        # Chaque bloc produit contient une div.price et un titre
        price_elems = soup.find_all(class_="price")

        for elem in price_elems:
            raw = elem.get_text(strip=True)
            m   = price_pattern.search(raw)
            if not m:
                continue

            price_min = float(m.group(1).replace(",", ""))
            price_max = float(m.group(2).replace(",", "")) if m.group(2) else price_min

            # Remonter au bloc parent pour récupérer titre + fournisseur
            parent = elem.find_parent(
                lambda t: t.name in ("li", "div")
                and any("product" in (c or "") for c in t.get("class", []))
            ) or elem.parent

            title    = ""
            supplier = ""
            if parent:
                # Titre : premier lien ou texte significatif
                link = parent.find("a", title=True)
                if link:
                    title = link.get("title", "").strip()
                if not title:
                    title = parent.get_text(separator=" ", strip=True)[:80]
                # Fournisseur : souvent dans une balise avec "company" dans la classe
                comp = parent.find(class_=re.compile(r"company|supplier", re.I))
                if comp:
                    supplier = comp.get_text(strip=True)[:60]

            items.append({
                "title":     title,
                "price_min": price_min,
                "price_max": price_max,
                "unit":      "unit",
                "supplier":  supplier,
                "raw_price": raw,
            })

        return items[:20]   # garder les 20 premiers résultats

    @staticmethod
    def _empty(query: str) -> dict[str, Any]:
        return {
            "prices":      [],
            "price_min":   0.0,
            "price_max":   0.0,
            "price_avg":   0.0,
            "currency":    "USD",
            "source":      "Made-in-China.com",
            "search_term": query.replace("_", " "),
            "url":         "",
        }
