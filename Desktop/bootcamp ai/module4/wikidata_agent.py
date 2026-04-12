"""
Module 4 — Agent Wikidata
Interroge le endpoint SPARQL public de Wikidata pour identifier
les fabricants / fournisseurs de matières premières métalliques (inox 316L…)
et les enrichit avec pays, site web et description.
"""

from __future__ import annotations

import time
import logging
from typing import Any, TypedDict

import requests

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────── #

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
HEADERS = {
    "User-Agent": "OpenIndustry-Algeria-Sourcing/1.0 (educational project)",
    "Accept": "application/sparql-results+json",
}

# Mapping matière → QID Wikidata
MATERIAL_QIDS: dict[str, dict] = {
    "stainless steel 316l": {
        "material_qid": "Q172587",       # acier inoxydable (stainless steel)
        "industry_qid": "Q22667",        # sidérurgie
        "hs_family":    "7219",
        "label":        "Stainless Steel 316L",
    },
    "titanium": {
        "material_qid": "Q932",
        "industry_qid": "Q22667",
        "hs_family":    "8108",
        "label":        "Titanium",
    },
    "aluminum": {
        "material_qid": "Q663",
        "industry_qid": "Q22667",
        "hs_family":    "7601",
        "label":        "Aluminum",
    },
    "iron": {
        "material_qid": "Q677",
        "industry_qid": "Q22667",
        "hs_family":    "7201",
        "label":        "Iron",
    },
    "nickel": {
        "material_qid": "Q744",
        "industry_qid": "Q22667",
        "hs_family":    "7502",
        "label":        "Nickel",
    },
}


# ── Types LangGraph-style ─────────────────────────────────────────────────── #

class WikidataState(TypedDict):
    material:        str
    material_info:   dict
    raw_companies:   list[dict]
    raw_countries:   list[dict]
    suppliers:       list[dict]
    market_analysis: dict
    errors:          list[str]


# ── Agent ─────────────────────────────────────────────────────────────────── #

class WikidataSourceAgent:
    """
    Agent LangGraph-style : chaque nœud transforme l'état et retourne
    un dict partiel fusionné dans l'état global.
    """

    def run(self, material: str) -> dict[str, Any]:
        """
        Point d'entrée principal.
        Retourne {"suppliers": [...], "market_analysis": {...}}.
        """
        state: WikidataState = {
            "material":        material,
            "material_info":   {},
            "raw_companies":   [],
            "raw_countries":   [],
            "suppliers":       [],
            "market_analysis": {},
            "errors":          [],
        }

        # Pipeline de nœuds
        state = self._node_resolve_material(state)
        state = self._node_fetch_companies(state)
        state = self._node_fetch_top_countries(state)
        state = self._node_build_suppliers(state)
        state = self._node_market_analysis(state)

        return {
            "suppliers":       state["suppliers"],
            "market_analysis": state["market_analysis"],
        }

    # ── Nœud 1 : résolution matière ──────────────────────────────────────── #

    def _node_resolve_material(self, state: WikidataState) -> WikidataState:
        key = state["material"].lower().strip()
        info = MATERIAL_QIDS.get(key) or MATERIAL_QIDS.get("stainless steel 316l")
        state["material_info"] = info
        return state

    # ── Nœud 2 : entreprises via SPARQL ──────────────────────────────────── #

    def _node_fetch_companies(self, state: WikidataState) -> WikidataState:
        qid  = state["material_info"]["industry_qid"]
        mq   = state["material_info"]["material_qid"]

        # Deux requêtes complémentaires : par industrie & par produit fabriqué
        queries = [
            self._sparql_companies_by_industry(qid),
            self._sparql_companies_by_product(mq),
        ]

        results: list[dict] = []
        seen: set[str] = set()

        for sparql in queries:
            try:
                rows = self._sparql_query(sparql)
                for r in rows:
                    uri = r.get("company", {}).get("value", "")
                    if uri and uri not in seen:
                        seen.add(uri)
                        results.append(r)
            except Exception as exc:
                state["errors"].append(f"SPARQL companies error: {exc}")

        state["raw_companies"] = results
        return state

    # ── Nœud 3 : top pays producteurs ────────────────────────────────────── #

    def _node_fetch_top_countries(self, state: WikidataState) -> WikidataState:
        mq = state["material_info"]["material_qid"]
        try:
            rows = self._sparql_query(self._sparql_top_countries(mq))
            state["raw_countries"] = rows
        except Exception as exc:
            state["errors"].append(f"SPARQL countries error: {exc}")
        return state

    # ── Nœud 4 : construction des fournisseurs ───────────────────────────── #

    def _node_build_suppliers(self, state: WikidataState) -> WikidataState:
        suppliers: list[dict] = []

        for row in state["raw_companies"]:
            name    = row.get("companyLabel",     {}).get("value", "Unknown")
            country = row.get("countryLabel",     {}).get("value", "Unknown")
            website = row.get("website",          {}).get("value", "")
            desc    = row.get("description",      {}).get("value", "")
            founded = row.get("founded",          {}).get("value", "")
            revenue = row.get("revenue",          {}).get("value", "")
            uri     = row.get("company",          {}).get("value", "")
            wikidata_id = uri.split("/")[-1] if uri else ""

            suppliers.append({
                "name":        name,
                "country":     country,
                "website":     website,
                "description": desc,
                "founded":     founded[:4] if founded else "",
                "revenue_usd": revenue,
                "wikidata_id": wikidata_id,
                "wikidata_url": uri,
                "source":      "Wikidata",
                "material":    state["material"],
            })

        # Tri : pays connus en premier, puis alphabétique
        suppliers.sort(key=lambda s: (s["country"] == "Unknown", s["name"]))
        state["suppliers"] = suppliers
        return state

    # ── Nœud 5 : analyse marché ───────────────────────────────────────────── #

    def _node_market_analysis(self, state: WikidataState) -> WikidataState:
        countries_count: dict[str, int] = {}
        for s in state["suppliers"]:
            c = s["country"]
            countries_count[c] = countries_count.get(c, 0) + 1

        # Top pays producteurs depuis SPARQL pays
        top_producer_countries = [
            {
                "country": r.get("countryLabel", {}).get("value", "Unknown"),
                "supplier_count": int(r.get("cnt", {}).get("value", 0)),
            }
            for r in state["raw_countries"]
        ]

        state["market_analysis"] = {
            "total_suppliers_found": len(state["suppliers"]),
            "countries_represented": len(
                {s["country"] for s in state["suppliers"] if s["country"] != "Unknown"}
            ),
            "suppliers_by_country": dict(
                sorted(countries_count.items(), key=lambda x: -x[1])
            ),
            "top_producer_countries": top_producer_countries[:10],
            "data_source": "Wikidata SPARQL (https://query.wikidata.org/sparql)",
            "material": state["material_info"]["label"],
            "errors": state["errors"],
        }
        return state

    # ── SPARQL helpers ────────────────────────────────────────────────────── #

    @staticmethod
    def _sparql_companies_by_industry(industry_qid: str) -> str:
        return f"""
SELECT DISTINCT ?company ?companyLabel ?countryLabel ?website ?description ?founded ?revenue WHERE {{
  ?company wdt:P31 wd:Q4830453 ;
           wdt:P452 wd:{industry_qid} .
  OPTIONAL {{ ?company wdt:P17   ?country  . }}
  OPTIONAL {{ ?company wdt:P856  ?website  . }}
  OPTIONAL {{ ?company schema:description ?description FILTER(LANG(?description)="en") . }}
  OPTIONAL {{ ?company wdt:P571  ?founded  . }}
  OPTIONAL {{ ?company wdt:P2139 ?revenue  . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr". }}
}}
LIMIT 40
"""

    @staticmethod
    def _sparql_companies_by_product(material_qid: str) -> str:
        return f"""
SELECT DISTINCT ?company ?companyLabel ?countryLabel ?website ?description ?founded ?revenue WHERE {{
  ?company wdt:P31  wd:Q4830453 ;
           wdt:P1056 ?product .
  ?product wdt:P279* wd:{material_qid} .
  OPTIONAL {{ ?company wdt:P17   ?country  . }}
  OPTIONAL {{ ?company wdt:P856  ?website  . }}
  OPTIONAL {{ ?company schema:description ?description FILTER(LANG(?description)="en") . }}
  OPTIONAL {{ ?company wdt:P571  ?founded  . }}
  OPTIONAL {{ ?company wdt:P2139 ?revenue  . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr". }}
}}
LIMIT 40
"""

    @staticmethod
    def _sparql_top_countries(material_qid: str) -> str:
        return f"""
SELECT ?countryLabel (COUNT(DISTINCT ?company) AS ?cnt) WHERE {{
  ?company wdt:P31   wd:Q4830453 ;
           wdt:P1056 ?product ;
           wdt:P17   ?country .
  ?product wdt:P279* wd:{material_qid} .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr". }}
}}
GROUP BY ?countryLabel
ORDER BY DESC(?cnt)
LIMIT 20
"""

    def _sparql_query(self, sparql: str, retries: int = 3) -> list[dict]:
        """Exécute une requête SPARQL et retourne les bindings JSON."""
        params = {"query": sparql, "format": "json"}
        for attempt in range(retries):
            try:
                resp = requests.get(
                    SPARQL_ENDPOINT,
                    params=params,
                    headers=HEADERS,
                    timeout=30,
                )
                resp.raise_for_status()
                return resp.json()["results"]["bindings"]
            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
            except requests.exceptions.HTTPError as e:
                if resp.status_code == 429:          # rate limit
                    time.sleep(5)
                else:
                    raise
        return []
