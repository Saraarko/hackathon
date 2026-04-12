"""
Module 4 — Agent multi-source Algérie
Sources :
  1. World Bank API  — indicateurs macroéconomiques DZ
  2. UN Comtrade     — flux commerciaux Algérie (HS 2709 pétrole brut)
  3. Claude Haiku    — analyse économique croisée

Sortie : output_algeria.json
"""

from __future__ import annotations

import os
import json
import time
import datetime
import requests
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage

# ── Config ────────────────────────────────────────────────────────────────── #

from dotenv import load_dotenv
load_dotenv()
# ANTHROPIC_API_KEY doit etre definie dans .env ou l'environnement

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output_algeria.json")

WORLDBANK_BASE = "https://api.worldbank.org/v2/country/DZ/indicator"

WB_INDICATORS = {
    "inflation_cpi":   ("FP.CPI.TOTL.ZG", "Inflation, consumer prices (annual %)"),
    "gdp_growth":      ("NY.GDP.MKTP.KD.ZG", "GDP growth (annual %)"),
    "unemployment":    ("SL.UEM.TOTL.ZS", "Unemployment, total (% of labor force)"),
    "exports_pct_gdp": ("NE.EXP.GNFS.ZS", "Exports of goods and services (% of GDP)"),
}

COMTRADE_URL  = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
DZ_ISO_NUM    = "12"   # Algeria numeric ISO


# ── Source 1 : World Bank ─────────────────────────────────────────────────── #

def fetch_wb_indicator(indicator_code: str) -> list[dict]:
    url = f"{WORLDBANK_BASE}/{indicator_code}?format=json&per_page=30&mrv=25"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    records = payload[1] or []
    return [
        {"year": r["date"], "value": round(r["value"], 3)}
        for r in records
        if r.get("value") is not None
    ]


def fetch_all_worldbank() -> dict:
    data = {}
    for key, (code, label) in WB_INDICATORS.items():
        try:
            series = fetch_wb_indicator(code)
            data[key] = {
                "indicator_code": code,
                "label": label,
                "source": "World Bank API",
                "url": f"{WORLDBANK_BASE}/{code}?format=json",
                "series": sorted(series, key=lambda x: x["year"]),
            }
            time.sleep(0.5)
        except Exception as exc:
            data[key] = {"error": str(exc)}
    return data


# ── Source 2 : UN Comtrade (pétrole brut DZ — HS 2709) ───────────────────── #

def fetch_comtrade_dz() -> dict:
    params = {
        "cmdCode":        "2709",   # Crude petroleum oils
        "reporterCode":   DZ_ISO_NUM,
        "period":         "2022",
        "flowCode":       "X",
    }
    headers = {"Accept": "application/json", "User-Agent": "OpenIndustry-Algeria/1.0"}
    try:
        resp = requests.get(COMTRADE_URL, params=params, headers=headers, timeout=30)
        resp.raise_for_status()
        rows = resp.json().get("data", [])
        flows = [
            {
                "partner":          r.get("partnerDesc", "Unknown"),
                "trade_value_usd":  int(r.get("primaryValue") or 0),
                "quantity_kg":      round(float(r.get("netWgt") or 0), 2),
                "year":             r.get("period"),
            }
            for r in rows
            if r.get("primaryValue")
        ]
        return {
            "indicator": "Crude petroleum exports (HS 2709)",
            "source": "UN Comtrade v1 Preview",
            "url": COMTRADE_URL,
            "year": "2022",
            "flows": sorted(flows, key=lambda x: -x["trade_value_usd"]),
        }
    except Exception as exc:
        return {"error": str(exc)}


# ── Source 3 : Claude Haiku — analyse croisée ─────────────────────────────── #

def build_context(wb: dict, comtrade: dict) -> str:
    lines = ["=== DONNÉES ÉCONOMIQUES ALGÉRIE ===\n"]

    for key, block in wb.items():
        if "error" in block:
            continue
        lines.append(f"[{block['label']}]")
        for pt in block["series"][-10:]:
            lines.append(f"  {pt['year']} : {pt['value']}")
        lines.append("")

    if "flows" in comtrade and comtrade["flows"]:
        lines.append("[Exportations pétrole brut 2022 — top partenaires]")
        for f in comtrade["flows"][:5]:
            lines.append(
                f"  {f['partner']} : {f['trade_value_usd']:,} USD"
            )

    return "\n".join(lines)


def analyze_with_llm(context: str) -> str:
    prompt = (
        f"{context}\n\n"
        "À partir de ces données réelles, fournis une analyse économique structurée "
        "de l'Algérie : tendances de l'inflation, croissance du PIB, dépendance aux "
        "exportations pétrolières, et risques macroéconomiques identifiés."
    )
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


# ── Agent principal ───────────────────────────────────────────────────────── #

class WorldBankAgent:

    def run(self) -> dict:
        wb_data       = fetch_all_worldbank()
        comtrade_data = fetch_comtrade_dz()
        context       = build_context(wb_data, comtrade_data)
        analysis      = analyze_with_llm(context)

        output = {
            "country":      "Algeria",
            "iso_code":     "DZ",
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "sources": {
                "world_bank": wb_data,
                "comtrade":   comtrade_data,
            },
            "llm_analysis": {
                "model":    "claude-haiku-4-5-20251001",
                "analysis": analysis,
            },
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"[OK] Donnees sauvegardees -> {OUTPUT_FILE}")
        return output


# ── Exécution directe ─────────────────────────────────────────────────────── #

if __name__ == "__main__":
    agent = WorldBankAgent()
    result = agent.run()

    print(f"\nCountry       : {result['country']} ({result['iso_code']})")
    print(f"Generated at  : {result['generated_at']}")
    print(f"WB indicators : {list(result['sources']['world_bank'].keys())}")
    comtrade = result["sources"]["comtrade"]
    if "flows" in comtrade:
        print(f"Comtrade flows: {len(comtrade['flows'])} partenaires")
    print("\n--- Analyse LLM ---")
    print(result["llm_analysis"]["analysis"].encode("ascii", "replace").decode("ascii"))
    print(f"\n=> JSON sauvegarde : {OUTPUT_FILE}")
