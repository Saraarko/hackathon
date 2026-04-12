"""
Module 4 — Sourcing Agent (multi-source)
Sources :
  1. Wikidata SPARQL  — fournisseurs via requete SPARQL
  2. UN Comtrade      — flux commerciaux matiere premiere
  3. Claude Haiku     — scoring LLM + recommandations

Sortie : output_sourcing.json
"""

from __future__ import annotations

import os
import json
import time
import datetime
import requests
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from comtrade_agent import COUNTRY_CODES

# ── Config ────────────────────────────────────────────────────────────────── #

# Charge la cle depuis .env ou variable d'environnement
from dotenv import load_dotenv
load_dotenv()
# ANTHROPIC_API_KEY doit etre definie dans .env ou l'environnement

llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "output_sourcing.json")


# ── Modeles ───────────────────────────────────────────────────────────────── #

class SupplierCategory(str, Enum):
    MACHINERY     = "machinery"
    RAW_MATERIALS = "raw_materials"
    POLYMERS      = "polymers"
    GLASS         = "glass"
    COMPONENTS    = "components"
    ELECTRONICS   = "electronics"
    CHEMICALS     = "chemicals"
    EQUIPMENT_5_0 = "equipment_5.0"
    OTHER         = "other"


class SupplierStatus(str, Enum):
    PENDING  = "pending"
    VERIFIED = "verified"
    APPROVED = "approved"
    REJECTED = "rejected"


class SupplierRating(BaseModel):
    overall:       float = Field(default=0.0, ge=0, le=5)
    quality:       float = Field(default=0.0, ge=0, le=5)
    delivery:      float = Field(default=0.0, ge=0, le=5)
    price:         float = Field(default=0.0, ge=0, le=5)
    communication: float = Field(default=0.0, ge=0, le=5)
    total_reviews: int   = 0


class SupplierCompliance(BaseModel):
    andi_verified:   bool      = False
    aapi_verified:   bool      = False
    reach_compliant: bool      = False
    risk_score:      float     = Field(default=0.0, ge=0, le=100)


class SupplierCertification(BaseModel):
    name:     str
    verified: bool = False


class SupplierContact(BaseModel):
    first_name: str
    last_name:  str
    role:       str
    email:      str
    phone:      str


class SupplierCapacity(BaseModel):
    min_order_quantity: Optional[int] = None
    lead_time_days:     Optional[int] = None
    export_regions:     list[str]     = Field(default_factory=list)
    payment_terms:      list[str]     = Field(default_factory=list)


class Supplier(BaseModel):
    id:             Optional[str]              = None
    name:           str
    category:       SupplierCategory
    status:         SupplierStatus             = SupplierStatus.PENDING
    country:        str
    city:           Optional[str]              = None
    website:        Optional[str]              = None
    products:       list[str]                  = Field(default_factory=list)
    certifications: list[SupplierCertification] = Field(default_factory=list)
    compliance:     SupplierCompliance          = Field(default_factory=SupplierCompliance)
    capacity:       SupplierCapacity            = Field(default_factory=SupplierCapacity)
    rating:         SupplierRating              = Field(default_factory=SupplierRating)
    price_range:    Optional[str]              = None
    source:         str                        = "wikidata"
    contact:        Optional[SupplierContact]  = None


class SupplierSearchResult(BaseModel):
    supplier:        Supplier
    relevance_score: float     = Field(ge=0, le=100)
    match_reasons:   list[str] = Field(default_factory=list)


class SourcingFilter(BaseModel):
    regions:                 list[str] = Field(default=["DZ", "MA", "TN", "FR", "DE"])
    required_certifications: list[str] = Field(default_factory=list)
    min_rating:              float     = Field(default=0.0, ge=0, le=5)
    compliance_verified:     bool      = False


# ── Scoring (adapte de Elite-hack/group3/src/providers/base.py) ───────────── #

def calculate_relevance_score(supplier: Supplier, product_name: str, filters: SourcingFilter) -> float:
    score = 50.0
    product_lower = product_name.lower()

    if any(product_lower in p.lower() or p.lower() in product_lower for p in supplier.products):
        score += 20
    if supplier.rating.overall > 0:
        score += supplier.rating.overall * 4
    if supplier.country in filters.regions:
        score += 10
    supplier_cert_names = [c.name for c in supplier.certifications]
    score += sum(5 for c in filters.required_certifications if c in supplier_cert_names)
    if supplier.compliance.andi_verified:
        score += 15
    if supplier.status == SupplierStatus.APPROVED:
        score += 10

    return min(100.0, score)


def get_match_reasons(supplier: Supplier, product_name: str, filters: SourcingFilter) -> list[str]:
    reasons = []
    if any(product_name.lower() in p.lower() or p.lower() in product_name.lower() for p in supplier.products):
        reasons.append("Product match")
    if supplier.country in filters.regions:
        reasons.append("Regional supplier")
    if supplier.rating.overall >= 4.5:
        reasons.append("Highly rated")
    if supplier.compliance.andi_verified:
        reasons.append("ANDI verified")
    if supplier.status == SupplierStatus.APPROVED:
        reasons.append("Pre-approved")
    return reasons


# ── Source 1 : Wikidata (principal) + DBpedia (fallback) ─────────────────── #

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DBPEDIA_ENDPOINT  = "https://dbpedia.org/sparql"


def _parse_suppliers(bindings: list[dict], id_prefix: str, source: str, material: str) -> list[Supplier]:
    suppliers = []
    for i, b in enumerate(bindings):
        name    = b.get("companyLabel", b.get("label", {})).get("value", "Unknown")
        country = b.get("countryLabel", b.get("country", {})).get("value", "XX")
        country_code = country[:2].upper() if country not in ("XX", "") else "XX"
        website = b.get("websiteLabel", b.get("website", {})).get("value")
        suppliers.append(Supplier(
            id=f"{id_prefix}_{i:03d}",
            name=name,
            category=SupplierCategory.RAW_MATERIALS,
            status=SupplierStatus.VERIFIED,
            country=country_code,
            website=website,
            products=[material],
            source=source,
        ))
    return suppliers


def _fetch_wikidata(material: str) -> list[Supplier]:
    query = f"""
SELECT DISTINCT ?companyLabel ?countryLabel ?websiteLabel WHERE {{
  ?company wdt:P31 wd:Q4830453 ;
           rdfs:label ?companyLabel .
  FILTER(LANG(?companyLabel) = "en")
  FILTER(CONTAINS(LCASE(?companyLabel), "{material.lower()}"))
  OPTIONAL {{ ?company wdt:P17/rdfs:label ?countryLabel . FILTER(LANG(?countryLabel)="en") }}
  OPTIONAL {{ ?company wdt:P856 ?websiteLabel . }}
}}
LIMIT 15
"""
    resp = requests.get(
        WIKIDATA_ENDPOINT,
        params={"query": query, "format": "json"},
        headers={"User-Agent": "OpenIndustry-Algeria/1.0", "Accept": "application/sparql-results+json"},
        timeout=15,
    )
    resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    return _parse_suppliers(bindings, "wd", "wikidata", material)


def _fetch_dbpedia(material: str) -> list[Supplier]:
    keyword = material.lower().split()[0]
    query = f"""
SELECT DISTINCT ?label ?country ?website WHERE {{
  ?company a dbo:Company ;
           rdfs:label ?label .
  FILTER(LANG(?label) = "en")
  FILTER(CONTAINS(LCASE(?label), "{keyword}"))
  OPTIONAL {{
    ?company dbo:country ?c .
    ?c rdfs:label ?country .
    FILTER(LANG(?country) = "en")
  }}
  OPTIONAL {{ ?company foaf:homepage ?website . }}
}}
LIMIT 15
"""
    resp = requests.get(
        DBPEDIA_ENDPOINT,
        params={"query": query, "format": "application/json"},
        headers={"User-Agent": "OpenIndustry-Algeria/1.0"},
        timeout=20,
    )
    resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    return _parse_suppliers(bindings, "dbp", "dbpedia", material)


def fetch_wikidata_suppliers(material: str) -> tuple[list[Supplier], str]:
    """
    Essaie Wikidata en premier.
    Si timeout ou erreur → fallback automatique sur DBpedia.
    Retourne (suppliers, source_utilisee).
    """
    try:
        suppliers = _fetch_wikidata(material)
        print(f"[Wikidata] {len(suppliers)} fournisseurs trouves pour '{material}'")
        return suppliers, "wikidata"
    except Exception as e:
        print(f"[Wikidata] indisponible ({type(e).__name__}) -> fallback DBpedia")
        try:
            suppliers = _fetch_dbpedia(material)
            print(f"[DBpedia]  {len(suppliers)} fournisseurs trouves pour '{material}'")
            return suppliers, "dbpedia"
        except Exception as e2:
            print(f"[DBpedia] erreur: {e2}")
            return [], "none"


# ── Estimation certifications via Claude Haiku ───────────────────────────── #

CONTACT_PROMPT = """Tu es un expert en sourcing industriel.
Pour chaque fournisseur ci-dessous, genere un contact commercial realiste
(nom coherent avec le pays, email au format professionnel du domaine de l'entreprise).

Reponds UNIQUEMENT en JSON valide, format exact :
{{
  "contacts": {{
    "<nom_entreprise>": {{
      "first_name": "...",
      "last_name":  "...",
      "role":       "Sales Manager",
      "email":      "prenom.nom@domaine.com",
      "phone":      "+XX XXX XXX XXXX"
    }}
  }}
}}

Fournisseurs :
{suppliers_list}
"""

def estimate_contacts(suppliers: list[Supplier]) -> dict[str, dict]:
    """Claude Haiku genere des contacts realistes pour chaque fournisseur en un seul appel."""
    if not suppliers:
        return {}

    lines = [
        f"- {s.name} | pays: {s.country} | site: {s.website or 'inconnu'}"
        for s in suppliers
    ]
    prompt = CONTACT_PROMPT.format(suppliers_list="\n".join(lines))

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw   = response.content.strip()
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        data  = json.loads(raw[start:end])
        return data.get("contacts", {})
    except Exception as exc:
        print(f"[Contacts LLM] erreur: {exc}")
        return {}


REQ_CERT_PROMPT = """Tu es un expert en certifications industrielles et en sourcing.

Pour la matiere premiere suivante : "{product}"

Quelles certifications sont REQUISES ou FORTEMENT RECOMMANDEES pour qualifier un fournisseur ?
Considere les normes industrielles internationales, les exigences reglementaires et les bonnes pratiques du secteur.

Reponds UNIQUEMENT en JSON valide, format exact :
{{
  "required_certifications": ["CERT1", "CERT2", ...],
  "reason": "explication courte en une phrase"
}}

Certifications possibles : ISO9001, ISO14001, ISO45001, REACH, CE, EN10088, EN10204,
RoHS, IATF16949, AS9100, OHSAS18001, UL, SGS, BV, DNV, ANDI, AAPI, ISO3834, PED.
"""

def estimate_required_certifications(product_name: str) -> tuple[list[str], str]:
    """Claude Haiku estime les certifications requises pour sourcer ce produit."""
    prompt = REQ_CERT_PROMPT.format(product=product_name)
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        raw   = response.content.strip()
        start = raw.find("{")
        end   = raw.rfind("}") + 1
        data  = json.loads(raw[start:end])
        certs  = data.get("required_certifications", [])
        reason = data.get("reason", "")
        return certs, reason
    except Exception as exc:
        print(f"[Required Certifications LLM] erreur: {exc}")
        return [], ""


# ── Source 2 : UN Comtrade ────────────────────────────────────────────────── #

COMTRADE_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"

MATERIAL_HS = {
    "stainless steel": ["7219", "7220"],
    "steel":           ["7219", "7206"],
    "aluminium":       ["7601", "7604"],
    "aluminum":        ["7601", "7604"],
    "iron":            ["7201", "7206"],
    "nickel":          ["7502"],
    "titanium":        ["8108"],
    "polymers":        ["3901", "3902"],
    "polyurethane":    ["3909"],
    "glass":           ["7005", "7007"],
}

def guess_hs_codes(material: str) -> list[str]:
    mat = material.lower()
    for key, codes in MATERIAL_HS.items():
        if key in mat:
            return codes
    return ["7219"]

def fetch_comtrade_flows(material: str) -> dict:
    codes = guess_hs_codes(material)
    flows = []
    for code in codes[:1]:
        try:
            resp = requests.get(
                COMTRADE_URL,
                params={"cmdCode": code, "period": "2022", "flowCode": "M"},
                headers={"Accept": "application/json", "User-Agent": "OpenIndustry-Algeria/1.0"},
                timeout=20,
            )
            resp.raise_for_status()
            rows = resp.json().get("data", [])
            for r in rows[:10]:
                if r.get("primaryValue"):
                    reporter_code = int(r.get("reporterCode") or 0)
                    partner_code  = int(r.get("partnerCode")  or 0)
                    flows.append({
                        "reporter":        COUNTRY_CODES.get(reporter_code, f"Code {reporter_code}"),
                        "reporter_code":   reporter_code,
                        "partner":         COUNTRY_CODES.get(partner_code,  f"Code {partner_code}"),
                        "partner_code":    partner_code,
                        "trade_value_usd": int(r.get("primaryValue") or 0),
                        "hs_code":         code,
                        "year":            r.get("period"),
                    })
            time.sleep(0.5)
        except Exception as exc:
            print(f"[Comtrade] erreur: {exc}")
    return {
        "hs_codes": codes,
        "source":   "UN Comtrade v1 Preview",
        "flows":    sorted(flows, key=lambda x: -x["trade_value_usd"]),
    }


# ── Agent principal ───────────────────────────────────────────────────────── #

class SourcingAgent:

    def run(self, product_name: str, filters: Optional[SourcingFilter] = None) -> dict:
        if filters is None:
            filters = SourcingFilter()

        # 1. Claude Haiku estime les certifications requises pour ce produit
        print("[LLM] Estimation des certifications requises...")
        required_certs, cert_reason = estimate_required_certifications(product_name)
        if required_certs and not filters.required_certifications:
            filters.required_certifications = required_certs
        print(f"[LLM] Certifications requises : {required_certs}")

        # 2. Wikidata (avec fallback DBpedia automatique)
        wikidata_suppliers, supplier_source = fetch_wikidata_suppliers(product_name)

        # 2b. Contacts generes par Claude Haiku (batch)
        print("[LLM] Generation des contacts fournisseurs...")
        contact_map = estimate_contacts(wikidata_suppliers)
        for s in wikidata_suppliers:
            c = contact_map.get(s.name, {})
            if c:
                s.contact = SupplierContact(
                    first_name = c.get("first_name", ""),
                    last_name  = c.get("last_name",  ""),
                    role       = c.get("role",       "Sales Manager"),
                    email      = c.get("email",      ""),
                    phone      = c.get("phone",      ""),
                )

        wikidata_results = [
            SupplierSearchResult(
                supplier=s,
                relevance_score=calculate_relevance_score(s, product_name, filters),
                match_reasons=get_match_reasons(s, product_name, filters),
            )
            for s in wikidata_suppliers
        ]

        # 2. Comtrade
        comtrade_data = fetch_comtrade_flows(product_name)

        # 3. Deduplication + tri par score
        all_results: dict[str, SupplierSearchResult] = {}
        for r in wikidata_results:
            key = r.supplier.name.lower()
            if key not in all_results or r.relevance_score > all_results[key].relevance_score:
                all_results[key] = r
        ranked = sorted(all_results.values(), key=lambda x: -x.relevance_score)

        # 4. Analyse Claude Haiku
        context  = self._build_context(product_name, ranked, comtrade_data)
        analysis = self._analyze(context)

        # 5. Serialisation
        output = {
            "product":         product_name,
            "generated_at":    datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "filters_applied": filters.model_dump(),
            "required_certifications": {
                "certifications": required_certs,
                "reason":         cert_reason,
                "estimated_by":   "claude-haiku-4-5-20251001",
            },
            "sources": {
                "wikidata": {
                    "label":     f"{'Wikidata' if supplier_source == 'wikidata' else 'DBpedia (fallback Wikidata indisponible)'}",
                    "source":    supplier_source,
                    "count":     len(wikidata_results),
                    "suppliers": [self._serialize(r) for r in wikidata_results],
                },
                "comtrade": comtrade_data,
            },
            "ranked_suppliers": [self._serialize(r) for r in ranked[:20]],
            "total_unique":     len(ranked),
            "llm_analysis": {
                "model":    "claude-haiku-4-5-20251001",
                "analysis": analysis,
            },
        }

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"[OK] JSON sauvegarde -> {OUTPUT_FILE}")
        return output

    def _serialize(self, r: SupplierSearchResult) -> dict:
        s = r.supplier
        return {
            "id":              s.id,
            "name":            s.name,
            "country":         s.country,
            "city":            s.city,
            "category":        s.category.value,
            "status":          s.status.value,
            "products":        s.products,
            "certifications":  [c.name for c in s.certifications],
            "andi_verified":   s.compliance.andi_verified,
            "reach_compliant": s.compliance.reach_compliant,
            "rating":          s.rating.overall,
            "website":         s.website,
            "source":          s.source,
            "relevance_score": round(r.relevance_score, 1),
            "match_reasons":   r.match_reasons,
            "contact": {
                "first_name": s.contact.first_name,
                "last_name":  s.contact.last_name,
                "role":       s.contact.role,
                "email":      s.contact.email,
                "phone":      s.contact.phone,
                "source":     "claude-haiku-4-5-20251001",
            } if s.contact else None,
        }

    def _build_context(self, product: str, ranked: list[SupplierSearchResult], comtrade: dict) -> str:
        lines = [f"=== SOURCING : {product} ===\n"]
        lines.append("Fournisseurs identifies (Wikidata) :")
        for i, r in enumerate(ranked[:8], 1):
            s = r.supplier
            lines.append(
                f"  {i}. {s.name} ({s.country}) | score={r.relevance_score:.0f} "
                f"| rating={s.rating.overall} | source={s.source}"
            )
        if comtrade.get("flows"):
            lines.append("\nFlux Comtrade (imports mondiaux 2022) :")
            for f in comtrade["flows"][:5]:
                lines.append(f"  {f['reporter']} importe {f['trade_value_usd']:,} USD depuis {f['partner']}")
        return "\n".join(lines)

    def _analyze(self, context: str) -> str:
        prompt = (
            f"{context}\n\n"
            "Analyse ces fournisseurs pour le sourcing industriel : "
            "identifie les meilleurs fournisseurs selon Wikidata, "
            "croise avec les flux Comtrade pour evaluer les marches fournisseurs, "
            "donne 3 recommandations concretes et evalue les risques supply chain."
        )
        try:
            return llm.invoke([HumanMessage(content=prompt)]).content
        except Exception as exc:
            return f"Erreur LLM : {exc}"


# ── Execution directe ─────────────────────────────────────────────────────── #

if __name__ == "__main__":
    agent  = SourcingAgent()
    result = agent.run(
        product_name="stainless steel",
        filters=SourcingFilter(regions=["DZ", "MA", "TN", "FR", "DE"]),
    )

    print(f"\nProduit      : {result['product']}")
    src = result['sources']['wikidata']
    print(f"Fournisseurs : {src['count']} ({src['source']})")
    print(f"Comtrade     : {len(result['sources']['comtrade']['flows'])} flux")
    print(f"Total unique : {result['total_unique']}")
    print("\nTop 5 :")
    for r in result["ranked_suppliers"][:5]:
        print(f"  {r['name']} ({r['country']}) — score {r['relevance_score']} — {r['source']}")
    print("\n--- Analyse LLM ---")
    print(result["llm_analysis"]["analysis"].encode("ascii", "replace").decode("ascii"))
    print(f"\n=> JSON sauvegarde : {OUTPUT_FILE}")
