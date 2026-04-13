"""
Module 5 — Agent de Négociation IA
OpenIndustry Algérie — ARIA (Agent de Recherche et d'Intelligence en Achat)

Architecture : LangGraph StateGraph + Claude Haiku
Chaque tour de négociation = un nœud du graphe
"""

from __future__ import annotations

import csv
import operator
import os
import re
from typing import Annotated, Literal, TypedDict

import anthropic
from dotenv import load_dotenv
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ─── Constantes ──────────────────────────────────────────────────────────────

CSV_PATH = os.path.join(os.path.dirname(__file__), "suppliers.csv")
MODEL    = "claude-haiku-4-5-20251001"
MAX_ROUNDS = 8

# Commande : 200 vannes haute pression
ORDER_DEFAULTS = {
    "product":             "vannes industrielles haute pression — acier inoxydable 316L",
    "quantity":            200,
    "target_price":        720.0,   # prix cible agressif (−15% catalogue min)
    "max_price":           980.0,   # prix maximum acceptable
    "max_delivery_days":   60,
}


# ─── État LangGraph ───────────────────────────────────────────────────────────

class NegotiationState(TypedDict):
    supplier:           dict
    messages:           Annotated[list[dict], operator.add]   # historique complet
    rounds:             int
    current_best_price: float
    status:             str     # "negotiating" | "agreed" | "rejected"
    order:              dict
    last_input:         str     # dernier message utilisateur
    ai_response:        str     # dernière réponse IA
    agreement:          dict | None


# ─── Nœud principal ───────────────────────────────────────────────────────────

def negotiate_node(state: NegotiationState) -> dict:
    """Un tour de négociation — appel Claude Haiku."""

    client   = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    supplier = state["supplier"]
    order    = state["order"]

    catalog_price = float(supplier["price_per_unit_usd"])
    quantity      = int(order["quantity"])
    target        = float(order["target_price"])
    max_price     = float(order["max_price"])

    system_prompt = f"""Tu es ARIA, agente IA de négociation pour OpenIndustry Algérie.
Mission : négocier l'achat de {quantity} unités de {order['product']} au meilleur prix.

━━━ PROFIL FOURNISSEUR ━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Nom         : {supplier['name']}
  Pays / Ville: {supplier['country']} — {supplier['city']}
  Description : {supplier['description']}
  Prix cata.  : {catalog_price:.2f} USD/unité
  Qté minimum : {supplier['min_quantity']} unités
  Délai std.  : {supplier['delivery_days']} jours
  Certifs.    : {supplier['certifications']}
  E-mail      : {supplier['email']}
  Téléphone   : {supplier['phone']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PARAMÈTRES COMMANDE :
  • Quantité commandée  : {quantity} unités  ← levier fort !
  • Prix cible          : {target:.2f} USD/unité
  • Prix max acceptable : {max_price:.2f} USD/unité
  • Délai maximum       : {order['max_delivery_days']} jours
  • Budget total max    : {quantity * max_price:,.2f} USD

ÉTAT ACTUEL :
  • Tour           : {state['rounds'] + 1} / {MAX_ROUNDS}
  • Meilleure offre: {state['current_best_price']:.2f} USD/unité
  • Statut         : {state['status']}

STRATÉGIE DE NÉGOCIATION :
  Tour 1  → Présentation professionnelle + première offre à {target:.2f} USD
  Tours 2-4 → Lever le volume ({quantity} unités), certifications, paiement 60 jours
  Tours 5-6 → Concessions progressives (+3 à +5% par tour max)
  Tours 7+  → Offre finale ferme ou rejet poli

RÈGLES IMPÉRATIVES :
  1. Si le fournisseur propose ≤ {max_price:.2f} USD → ACCEPTER et clôturer
  2. Si impossible après {MAX_ROUNDS} tours → REJETER poliment
  3. Toujours terminer par l'une de ces balises :
       [OFFRE_EN_COURS: X.XX USD]  — si négociation en cours
       [ACCORD: X.XX USD]          — si accord trouvé ≤ {max_price:.2f} USD
       [REJET]                     — si négociation échouée

Style : français, ton expert et professionnel, arguments chiffrés, concis."""

    # ── Construction de l'historique pour le LLM ──
    history = list(state["messages"])

    if state["rounds"] == 0 and not state["last_input"].strip():
        # Premier tour : démarrage automatique
        trigger = (
            f"Lance la négociation avec {supplier['name']} pour {quantity} unités de "
            f"{order['product']}. Présente-toi et fais notre offre initiale."
        )
        history.append({"role": "user", "content": trigger})
    elif state["last_input"].strip():
        history.append({"role": "user", "content": state["last_input"]})

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system_prompt,
        messages=history,
    )
    ai_text = response.content[0].text

    # ── Parsing des balises de statut ──
    new_status     = state["status"]
    new_best_price = state["current_best_price"]
    agreement      = state.get("agreement")

    if "[ACCORD:" in ai_text:
        m = re.search(r'\[ACCORD:\s*([\d.]+)\s*USD\]', ai_text)
        if m:
            price         = float(m.group(1))
            new_status    = "agreed"
            new_best_price = price
            agreement = {
                "price_per_unit":  price,
                "total_price":     round(price * quantity, 2),
                "quantity":        quantity,
                "supplier_name":   supplier["name"],
                "supplier_email":  supplier["email"],
                "supplier_phone":  supplier["phone"],
                "delivery_days":   int(supplier["delivery_days"]),
                "certifications":  supplier["certifications"],
                "savings_vs_catalog": round((catalog_price - price) * quantity, 2),
            }
    elif "[REJET]" in ai_text:
        new_status = "rejected"
    else:
        m = re.search(r'\[OFFRE_EN_COURS:\s*([\d.]+)\s*USD\]', ai_text)
        if m:
            new_best_price = float(m.group(1))

    # ── Messages à ajouter au state (operator.add les cumule) ──
    new_messages: list[dict] = []
    if state["rounds"] == 0 and not state["last_input"].strip():
        trigger = (
            f"Lance la négociation avec {supplier['name']} pour {quantity} unités de "
            f"{order['product']}. Présente-toi et fais notre offre initiale."
        )
        new_messages.append({"role": "user",      "content": trigger})
    elif state["last_input"].strip():
        new_messages.append({"role": "user",      "content": state["last_input"]})

    new_messages.append({"role": "assistant", "content": ai_text})

    return {
        "messages":           new_messages,
        "rounds":             state["rounds"] + 1,
        "current_best_price": new_best_price,
        "status":             new_status,
        "ai_response":        ai_text,
        "agreement":          agreement,
        "last_input":         "",          # reset après traitement
    }


# ─── Condition de fin ─────────────────────────────────────────────────────────

def _should_end(state: NegotiationState) -> Literal["end", "continue"]:
    if state["status"] in ("agreed", "rejected"):
        return "end"
    if state["rounds"] >= MAX_ROUNDS:
        return "end"
    return "continue"


# ─── Construction du graphe ───────────────────────────────────────────────────

def build_graph():
    """Compile et retourne le graphe LangGraph avec checkpointer mémoire."""
    wf = StateGraph(NegotiationState)
    wf.add_node("negotiate", negotiate_node)
    wf.set_entry_point("negotiate")
    wf.add_conditional_edges(
        "negotiate",
        _should_end,
        {"end": END, "continue": END},   # 1 step par invocation (WebSocket)
    )
    return wf.compile(checkpointer=MemorySaver())


# ─── Utilitaires CSV ──────────────────────────────────────────────────────────

def load_suppliers() -> list[dict]:
    """Charge tous les fournisseurs depuis suppliers.csv."""
    suppliers = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            suppliers.append(row)
    return suppliers


def get_supplier(supplier_id: str) -> dict | None:
    """Retourne un fournisseur par son ID."""
    for s in load_suppliers():
        if s["id"] == supplier_id:
            return s
    return None


def build_initial_state(supplier: dict) -> NegotiationState:
    """Construit l'état initial pour une nouvelle négociation."""
    return NegotiationState(
        supplier=supplier,
        messages=[],
        rounds=0,
        current_best_price=float(supplier["price_per_unit_usd"]),
        status="negotiating",
        order=ORDER_DEFAULTS.copy(),
        last_input="",
        ai_response="",
        agreement=None,
    )
