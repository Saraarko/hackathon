# Module 4 — Sourcing Agent Documentation

## Vue d'ensemble

Le `SourcingAgent` est un agent de sourcing industriel multi-source qui identifie, score et analyse des fournisseurs de matières premières. Il combine deux sources de données réelles (Wikidata + UN Comtrade) et une analyse LLM pour produire un rapport JSON complet.

---

## Architecture

```
SourcingAgent.run(product_name, filters)
        │
        ├── Source 1 : Wikidata SPARQL
        │       └── Requete sur les entreprises industrielles mondiales
        │
        ├── Source 2 : UN Comtrade API
        │       └── Flux d'imports/exports reels (2022)
        │
        ├── Deduplication + scoring de pertinence
        │       └── calculate_relevance_score() + get_match_reasons()
        │
        ├── Claude Haiku (LLM)
        │       └── Analyse croisee + recommandations supply chain
        │
        └── output_sourcing.json
```

---

## Sources de donnees

### 1. Wikidata SPARQL

Endpoint : `https://query.wikidata.org/sparql`

Requete dynamique qui cherche les entreprises industrielles (`wd:Q4830453`) dont le nom contient le produit recherche :

```sparql
SELECT DISTINCT ?company ?companyLabel ?countryLabel ?websiteLabel WHERE {
  ?company wdt:P31 wd:Q4830453 .
  ?company wdt:P452 ?industry .
  ?company rdfs:label ?nameLabel .
  FILTER(LANG(?nameLabel) = "en")
  FILTER(CONTAINS(LCASE(?nameLabel), "<product>"))
  OPTIONAL { ?company wdt:P17 ?country . }
  OPTIONAL { ?company wdt:P856 ?website . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,fr". }
}
LIMIT 15
```

Chaque resultat est transforme en objet `Supplier` avec `source="wikidata"`.

### 2. UN Comtrade API

Endpoint : `https://comtradeapi.un.org/public/v1/preview/C/A/HS`

Recupere les flux d'imports mondiaux pour l'annee 2022 (`flowCode=M`) sur les codes HS correspondant au produit.

Correspondances HS pre-definies :

| Produit         | Codes HS       |
|-----------------|----------------|
| stainless steel | 7219, 7220     |
| steel           | 7219, 7206     |
| aluminium       | 7601, 7604     |
| iron            | 7201, 7206     |
| nickel          | 7502           |
| titanium        | 8108           |
| polyurethane    | 3909           |
| polymers        | 3901, 3902     |
| glass           | 7005, 7007     |

---

## Modeles Pydantic

Adaptes de [Elite-hack/group3/src/models/supplier.py](https://github.com/Ouail-Ahmed/Elite-hack).

### `Supplier`

```python
class Supplier(BaseModel):
    id:             str
    name:           str
    category:       SupplierCategory     # raw_materials | polymers | glass | ...
    status:         SupplierStatus       # pending | verified | approved | rejected
    country:        str                  # code ISO 2 lettres
    city:           str
    website:        str
    products:       list[str]
    certifications: list[SupplierCertification]
    compliance:     SupplierCompliance   # andi_verified, aapi_verified, reach_compliant
    capacity:       SupplierCapacity     # MOQ, lead_time, export_regions
    rating:         SupplierRating       # overall, quality, delivery, price (0-5)
    source:         str                  # wikidata
```

### `SourcingFilter`

```python
class SourcingFilter(BaseModel):
    regions:                 list[str]   # defaut: ["DZ","MA","TN","FR","DE"]
    required_certifications: list[str]   # ex: ["ISO9001","REACH"]
    min_rating:              float       # defaut: 0.0
    compliance_verified:     bool        # filtre sur andi_verified
```

### `SupplierSearchResult`

```python
class SupplierSearchResult(BaseModel):
    supplier:        Supplier
    relevance_score: float        # 0-100
    match_reasons:   list[str]    # ["Product match", "Regional supplier", ...]
```

---

## Algorithme de scoring

Adapte de [Elite-hack/group3/src/providers/base.py — `_calculate_relevance_score()`](https://github.com/Ouail-Ahmed/Elite-hack).

```
score de base = 50

+ 20  si le produit recherche correspond a un produit du fournisseur
+ 20  maximum selon le rating overall (rating * 4)
+ 10  si le pays est dans les regions cibles
+  5  par certification requise presente
+ 15  si ANDI verifie
+ 10  si statut APPROVED

score final = min(100, total)
```

---

## Analyse LLM — Claude Haiku

Modele : `claude-haiku-4-5-20251001`

Le contexte envoye contient :
- Les 8 premiers fournisseurs scores (nom, pays, score, rating, source)
- Les 5 premiers flux Comtrade (reporter, partenaire, valeur USD)

L'analyse produite couvre :
1. Identification des meilleurs fournisseurs Wikidata
2. Croisement avec les flux Comtrade pour evaluer les marches
3. Trois recommandations concretes
4. Evaluation des risques supply chain

---

## Format de sortie — `output_sourcing.json`

```json
{
  "product": "stainless steel",
  "generated_at": "2026-04-12T16:14:32Z",
  "filters_applied": {
    "regions": ["DZ", "MA", "TN", "FR", "DE"],
    "min_rating": 0.0,
    "compliance_verified": false
  },
  "sources": {
    "wikidata": {
      "label": "Wikidata SPARQL",
      "count": 12,
      "suppliers": [ ... ]
    },
    "comtrade": {
      "hs_codes": ["7219", "7220"],
      "source": "UN Comtrade v1 Preview",
      "flows": [
        { "reporter": "...", "partner": "...", "trade_value_usd": 12345678, "year": "2022" }
      ]
    }
  },
  "ranked_suppliers": [
    {
      "id": "wd_000",
      "name": "...",
      "country": "DE",
      "rating": 0.0,
      "relevance_score": 80.0,
      "match_reasons": ["Product match", "Regional supplier"],
      "source": "wikidata"
    }
  ],
  "total_unique": 12,
  "llm_analysis": {
    "model": "claude-haiku-4-5-20251001",
    "analysis": "..."
  }
}
```

---

## Utilisation

### En ligne de commande

```bash
cd "module4"
python sourcing_agent.py
```

### Via l'API FastAPI

```bash
python api/main.py
```

```bash
# Sourcing multi-source
curl -X POST http://localhost:8011/source \
  -H "Content-Type: application/json" \
  -d '{
    "material": "aluminium",
    "regions": ["DZ", "MA", "TN"],
    "min_rating": 0.0
  }'

# Analyse economique Algerie
curl -X POST http://localhost:8011/economy

# Documentation interactive
http://localhost:8011/docs
```

### En Python

```python
from sourcing_agent import SourcingAgent, SourcingFilter

agent = SourcingAgent()
result = agent.run(
    product_name="aluminium",
    filters=SourcingFilter(
        regions=["DZ", "MA", "FR"],
        required_certifications=["ISO9001"],
    )
)
# result est un dict + output_sourcing.json est sauvegarde
```

---

## Structure du module

```
module4/
├── sourcing_agent.py       <- Agent principal (Wikidata + Comtrade + LLM)
├── worldbank_agent.py      <- Agent World Bank multi-indicateurs
├── comtrade_agent.py       <- Agent UN Comtrade flux commerciaux
├── wikidata_agent.py       <- Agent Wikidata fournisseurs (legacy)
├── api/
│   └── main.py             <- API FastAPI (endpoints JSON)
├── output_sourcing.json    <- Dernier rapport sourcing genere
├── output_algeria.json     <- Dernier rapport economique genere
└── requirements.txt
```

---

## Dependances

```
fastapi
uvicorn[standard]
requests
pydantic
python-dotenv
langchain-anthropic
langchain-core
```

```bash
pip install fastapi uvicorn requests pydantic python-dotenv langchain-anthropic langchain-core
```

---


