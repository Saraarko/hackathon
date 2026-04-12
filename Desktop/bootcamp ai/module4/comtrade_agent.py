"""
Module 4 — Agent UN Comtrade
Interroge l'API publique v1 preview de UN Comtrade pour récupérer
les flux commerciaux mondiaux de matières premières métalliques.

API utilisée (gratuite, sans clé) :
  https://comtradeapi.un.org/public/v1/preview/C/A/HS
"""

from __future__ import annotations

import time
import logging
from typing import Any, TypedDict

import requests

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────── #

COMTRADE_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

MATERIAL_HS: dict[str, dict] = {
    "stainless steel 316l": {
        "codes": ["7219", "7220", "7222", "7218"],
        "label": "Stainless Steel / Inox 316L",
        "description": "Flat-rolled stainless steel products and bars/rods",
    },
    "titanium": {
        "codes": ["8108"],
        "label": "Titanium",
        "description": "Titanium and articles thereof",
    },
    "aluminum": {
        "codes": ["7601", "7604", "7606"],
        "label": "Aluminum",
        "description": "Aluminium unwrought, bars/rods and plates/sheets",
    },
    "iron": {
        "codes": ["7201", "7206"],
        "label": "Iron",
        "description": "Pig iron and primary forms of iron",
    },
    "nickel": {
        "codes": ["7502", "7505"],
        "label": "Nickel",
        "description": "Nickel unwrought and bars/rods/profiles/wire",
    },
}

# Codes ISO numériques → noms de pays (ISO 3166-1 numeric)
COUNTRY_CODES: dict[int, str] = {
    4: "Afghanistan", 8: "Albania", 12: "Algeria", 24: "Angola",
    32: "Argentina", 36: "Australia", 40: "Austria", 31: "Azerbaijan",
    50: "Bangladesh", 112: "Belarus", 56: "Belgium", 68: "Bolivia",
    70: "Bosnia & Herzegovina", 76: "Brazil", 100: "Bulgaria",
    104: "Myanmar", 116: "Cambodia", 120: "Cameroon", 124: "Canada",
    144: "Sri Lanka", 152: "Chile", 156: "China", 170: "Colombia",
    178: "Congo", 180: "DR Congo", 188: "Costa Rica", 191: "Croatia",
    192: "Cuba", 196: "Cyprus", 203: "Czechia", 208: "Denmark",
    218: "Ecuador", 818: "Egypt", 231: "Ethiopia", 246: "Finland",
    250: "France", 266: "Gabon", 276: "Germany", 288: "Ghana",
    300: "Greece", 320: "Guatemala", 332: "Haiti", 340: "Honduras",
    348: "Hungary", 356: "India", 360: "Indonesia", 364: "Iran",
    368: "Iraq", 372: "Ireland", 376: "Israel", 380: "Italy",
    388: "Jamaica", 392: "Japan", 400: "Jordan", 398: "Kazakhstan",
    404: "Kenya", 410: "South Korea", 414: "Kuwait", 418: "Laos",
    422: "Lebanon", 430: "Liberia", 434: "Libya", 458: "Malaysia",
    484: "Mexico", 498: "Moldova", 504: "Morocco", 516: "Namibia",
    524: "Nepal", 528: "Netherlands", 554: "New Zealand", 566: "Nigeria",
    578: "Norway", 586: "Pakistan", 591: "Panama", 604: "Peru",
    608: "Philippines", 616: "Poland", 620: "Portugal", 630: "Puerto Rico",
    634: "Qatar", 642: "Romania", 643: "Russia", 682: "Saudi Arabia",
    686: "Senegal", 694: "Sierra Leone", 703: "Slovakia", 705: "Slovenia",
    706: "Somalia", 710: "South Africa", 724: "Spain", 736: "Sudan",
    752: "Sweden", 756: "Switzerland", 760: "Syria", 158: "Taiwan",
    762: "Tajikistan", 834: "Tanzania", 764: "Thailand", 788: "Tunisia",
    792: "Turkey", 800: "Uganda", 804: "Ukraine", 784: "UAE",
    826: "United Kingdom", 840: "United States", 858: "Uruguay",
    860: "Uzbekistan", 862: "Venezuela", 704: "Vietnam",
    887: "Yemen", 894: "Zambia", 716: "Zimbabwe",
    0: "World",
}

LATEST_YEAR = "2022"


# ── Types LangGraph-style ─────────────────────────────────────────────────── #

class ComtradeState(TypedDict):
    material:    str
    hs_info:     dict
    raw_exports: list[dict]
    raw_imports: list[dict]
    trade_flows: list[dict]
    summary:     dict
    errors:      list[str]


# ── Agent ─────────────────────────────────────────────────────────────────── #

class ComtradeAgent:
    """
    Agent LangGraph-style : pipeline de nœuds pour récupérer et
    structurer les données de commerce international UN Comtrade.
    """

    def run(self, material: str) -> dict[str, Any]:
        state: ComtradeState = {
            "material":    material,
            "hs_info":     {},
            "raw_exports": [],
            "raw_imports": [],
            "trade_flows": [],
            "summary":     {},
            "errors":      [],
        }

        state = self._node_resolve_hs(state)
        state = self._node_fetch_exports(state)
        state = self._node_fetch_imports(state)
        state = self._node_build_flows(state)
        state = self._node_summary(state)

        return {
            "hs_codes":    state["hs_info"].get("codes", []),
            "trade_flows": state["trade_flows"],
            "summary":     state["summary"],
        }

    # ── Nœud 1 : résolution codes HS ─────────────────────────────────────── #

    def _node_resolve_hs(self, state: ComtradeState) -> ComtradeState:
        key = state["material"].lower().strip()
        state["hs_info"] = (
            MATERIAL_HS.get(key) or MATERIAL_HS["stainless steel 316l"]
        )
        return state

    # ── Nœud 2 : exports mondiaux (flowCode=X) ────────────────────────────── #

    def _node_fetch_exports(self, state: ComtradeState) -> ComtradeState:
        rows: list[dict] = []
        for code in state["hs_info"]["codes"][:2]:
            try:
                data = self._fetch(hs_code=code, flow_code="X")
                rows.extend(data)
                time.sleep(1.5)
            except Exception as exc:
                state["errors"].append(f"Comtrade exports [{code}]: {exc}")
        state["raw_exports"] = rows
        return state

    # ── Nœud 3 : imports mondiaux (flowCode=M) ────────────────────────────── #

    def _node_fetch_imports(self, state: ComtradeState) -> ComtradeState:
        rows: list[dict] = []
        for code in state["hs_info"]["codes"][:2]:
            try:
                data = self._fetch(hs_code=code, flow_code="M")
                rows.extend(data)
                time.sleep(1.5)
            except Exception as exc:
                state["errors"].append(f"Comtrade imports [{code}]: {exc}")
        state["raw_imports"] = rows
        return state

    # ── Nœud 4 : structuration des flux ──────────────────────────────────── #

    def _node_build_flows(self, state: ComtradeState) -> ComtradeState:
        flows: list[dict] = []

        def _parse(rows: list[dict], flow_label: str) -> list[dict]:
            # Agrégation par pays rapporteur
            agg: dict[int, dict] = {}
            for r in rows:
                r_code = r.get("reporterCode") or 0
                val    = float(r.get("primaryValue") or 0)
                wgt    = float(r.get("netWgt")       or 0)
                hs     = r.get("cmdCode", "")

                if r_code not in agg:
                    agg[r_code] = {
                        "reporter_code": r_code,
                        "reporter":      COUNTRY_CODES.get(int(r_code), str(r_code)),
                        "flow":          flow_label,
                        "hs_code":       hs,
                        "year":          r.get("period", LATEST_YEAR),
                        "trade_value_usd": 0.0,
                        "quantity_kg":   0.0,
                        "source":        "UN Comtrade v1 Preview API",
                    }
                agg[r_code]["trade_value_usd"] += val
                agg[r_code]["quantity_kg"]     += wgt

            result = list(agg.values())
            # Arrondi + tri
            for f in result:
                f["trade_value_usd"] = int(f["trade_value_usd"])
                f["quantity_kg"]     = round(f["quantity_kg"], 2)
            return sorted(result, key=lambda x: -x["trade_value_usd"])

        flows += _parse(state["raw_exports"], "Export")
        flows += _parse(state["raw_imports"], "Import")
        state["trade_flows"] = flows
        return state

    # ── Nœud 5 : résumé analytique ───────────────────────────────────────── #

    def _node_summary(self, state: ComtradeState) -> ComtradeState:
        exports = [f for f in state["trade_flows"] if f["flow"] == "Export"]
        imports = [f for f in state["trade_flows"] if f["flow"] == "Import"]

        # Exclure "World" (code 0) des tops pays pour ne garder que les nations
        real_exp = [e for e in exports if e["reporter_code"] != 0]
        real_imp = [i for i in imports if i["reporter_code"] != 0]

        state["summary"] = {
            "material":                state["hs_info"]["label"],
            "hs_codes":                state["hs_info"]["codes"],
            "description":             state["hs_info"]["description"],
            "year":                    LATEST_YEAR,
            "total_export_value_usd":  sum(e["trade_value_usd"] for e in real_exp),
            "total_import_value_usd":  sum(i["trade_value_usd"] for i in real_imp),
            "top_exporters": [
                {"country": e["reporter"], "trade_value_usd": e["trade_value_usd"]}
                for e in real_exp[:10]
            ],
            "top_importers": [
                {"country": i["reporter"], "trade_value_usd": i["trade_value_usd"]}
                for i in real_imp[:10]
            ],
            "total_flows_found": len(state["trade_flows"]),
            "data_source":  "UN Comtrade v1 Preview (https://comtradeapi.un.org/public/v1/preview/C/A/HS)",
            "errors":       state["errors"],
        }
        return state

    # ── Helper API ────────────────────────────────────────────────────────── #

    def _fetch(
        self,
        hs_code: str,
        flow_code: str,     # "X" = exports, "M" = imports
        retries: int = 3,
    ) -> list[dict]:
        """
        Appel à l'API Comtrade v1 preview (sans clé, max 500 lignes par appel).
        flowCode : X=exports, M=imports, RM=re-imports, RX=re-exports
        """
        params = {
            "cmdCode":  hs_code,
            "period":   LATEST_YEAR,
            "flowCode": flow_code,
        }
        headers = {
            "Accept":     "application/json",
            "User-Agent": "OpenIndustry-Algeria/1.0",
        }

        for attempt in range(retries):
            try:
                resp = requests.get(
                    COMTRADE_URL,
                    params=params,
                    headers=headers,
                    timeout=30,
                )
                resp.raise_for_status()
                payload = resp.json()
                data = payload.get("data", [])
                return data if isinstance(data, list) else []

            except requests.exceptions.Timeout:
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    logger.warning("Comtrade timeout for HS=%s flow=%s", hs_code, flow_code)
                    return []
            except Exception as exc:
                logger.warning("Comtrade error HS=%s: %s", hs_code, exc)
                return []

        return []
