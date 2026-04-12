"""
Module 4 — FastAPI JSON API
Endpoints :
  GET  /health
  GET  /materials
  POST /source        <- Wikidata + UN Comtrade
  POST /economy       <- World Bank multi-indicateurs + Comtrade + Claude Haiku
  GET  /docs
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from wikidata_agent import WikidataSourceAgent
from comtrade_agent import ComtradeAgent
from worldbank_agent import WorldBankAgent
from sourcing_agent import SourcingAgent, SourcingFilter

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

app = FastAPI(
    title="Module 4 — Sourcing & Économie Algérie",
    description="Données multi-sources : Wikidata, UN Comtrade, World Bank, Claude Haiku.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SourcingRequest(BaseModel):
    material: str = Field(
        default="stainless steel",
        examples=["stainless steel", "titanium", "aluminum", "polyurethane", "glass"],
    )
    regions: list[str] = Field(default=["DZ", "MA", "TN", "FR", "DE"])
    min_rating: float = Field(default=3.0, ge=0, le=5)
    compliance_verified: bool = False


# ── Endpoints ────────────────────────────────────────────────────────────── #

@app.get("/health", tags=["Système"])
def health():
    return {"status": "ok", "module": "4 — Sourcing & Economy"}


@app.get("/materials", tags=["Utilitaires"])
def list_materials():
    return {
        "materials": ["Stainless Steel 316L", "Titanium", "Aluminum", "Iron", "Nickel"]
    }


@app.post("/source", tags=["Sourcing"])
def source(req: SourcingRequest):
    """
    Sourcing multi-source : base interne (Elite-hack) + Wikidata + Comtrade + Claude Haiku.
    Sauvegarde output_sourcing.json.
    """
    try:
        filters = SourcingFilter(
            regions=req.regions,
            min_rating=req.min_rating,
            compliance_verified=req.compliance_verified,
        )
        result = SourcingAgent().run(product_name=req.material, filters=filters)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/economy", tags=["Économie"])
def economy():
    """
    Données macro Algérie multi-sources :
    World Bank (inflation, PIB, chômage, exports) + Comtrade + analyse Claude Haiku.
    Sauvegarde également output_algeria.json.
    """
    try:
        result = WorldBankAgent().run()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8011)),
        reload=True,
        reload_dirs=[
            os.path.dirname(os.path.abspath(__file__)),
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        ],
    )
