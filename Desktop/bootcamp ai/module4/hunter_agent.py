"""
Module 4 — Agent Hunter.io
Enrichit les fournisseurs avec leurs contacts (email, nom, poste)
en utilisant l'API Hunter.io Domain Search.

Doc API : https://hunter.io/api-documentation/v2#domain-search
Clé gratuite : 25 recherches/mois sur https://hunter.io
"""

from __future__ import annotations

import logging
import os
import time
from urllib.parse import urlparse

import requests

logger = logging.getLogger(__name__)

HUNTER_ENDPOINT = "https://api.hunter.io/v2/domain-search"

# Postes pertinents pour la prospection B2B industrielle (ordre de priorité)
RELEVANT_POSITIONS: list[tuple[int, list[str]]] = [
    (1, ["sales", "commercial", "export", "business development", "account"]),
    (2, ["procurement", "purchasing", "sourcing", "supply chain", "supply"]),
    (3, ["director", "manager", "head", "chief", "president", "vp", "vice"]),
    (4, ["engineer", "technical", "product"]),
]


class HunterAgent:
    """Enrichit une liste de fournisseurs avec leurs contacts via Hunter.io."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("HUNTER_API_KEY", "").strip()
        if not self.api_key or self.api_key == "your_hunter_api_key_here":
            logger.warning("[Hunter] HUNTER_API_KEY non configurée — enrichissement désactivé")

    # ── API publique ──────────────────────────────────────────────────────── #

    def enrich_suppliers(self, suppliers: list[dict], max_suppliers: int = 10) -> list[dict]:
        """
        Pour chaque fournisseur (qui a un website), interroge Hunter.io
        et ajoute les champs : contacts, email_principal, phone_principal.

        Args:
            suppliers:     liste de fournisseurs (sortie de wikidata_agent)
            max_suppliers: limite pour ne pas épuiser le quota gratuit

        Returns:
            Même liste enrichie avec les contacts trouvés.
        """
        if not self.api_key or self.api_key == "your_hunter_api_key_here":
            logger.warning("[Hunter] Clé absente — fournisseurs non enrichis")
            return suppliers

        enriched = []
        calls    = 0

        for supplier in suppliers:
            website = supplier.get("website", "").strip()
            domain  = self._extract_domain(website)

            if not domain or calls >= max_suppliers:
                enriched.append(supplier)
                continue

            contacts = self._search_domain(domain)
            calls   += 1

            # Filtrage par position pertinente
            best = self._pick_best_contact(contacts)

            supplier = {
                **supplier,
                "contacts":         contacts,
                "email_principal":  best["email"]    if best else "",
                "contact_name":     f"{best['first_name']} {best['last_name']}".strip() if best else "",
                "contact_position": best["position"] if best else "",
                "contact_source":   "Hunter.io",
            }

            if best:
                logger.info("[Hunter] %s → contact retenu : %s (%s)",
                            domain, supplier["contact_name"], best["position"])
            elif contacts:
                logger.info("[Hunter] %s → %d contact(s) trouvé(s) mais aucun poste pertinent",
                            domain, len(contacts))
            else:
                logger.info("[Hunter] %s → aucun contact", domain)

            enriched.append(supplier)

            # Respecte le rate limit Hunter (1 req/s sur plan gratuit)
            time.sleep(1.1)

        logger.info("[Hunter] %d/%d fournisseurs enrichis", calls, len(suppliers))
        return enriched

    # ── Interne ───────────────────────────────────────────────────────────── #

    @staticmethod
    def _position_score(contact: dict) -> int:
        """
        Retourne un score de priorité selon le poste (1 = meilleur, 99 = non pertinent).
        Les postes sans correspondance reçoivent 50 (conservés en dernier recours).
        """
        pos = (contact.get("position") or "").lower()
        if not pos:
            return 99
        for score, keywords in RELEVANT_POSITIONS:
            if any(kw in pos for kw in keywords):
                return score
        return 50

    def _pick_best_contact(self, contacts: list[dict]) -> dict | None:
        """
        Parmi les contacts retournés par Hunter.io, sélectionne le plus pertinent :
        1. Trier par score de position (sales > procurement > manager > engineer)
        2. À score égal, préférer le contact avec la plus haute confiance Hunter
        3. Si aucun contact n'a de poste connu, prendre le plus fiable (confiance max)
        """
        if not contacts:
            return None

        scored = sorted(
            contacts,
            key=lambda c: (self._position_score(c), -c.get("confidence", 0)),
        )
        return scored[0]

    def _search_domain(self, domain: str) -> list[dict]:
        """Appelle Hunter.io Domain Search et retourne les contacts trouvés."""
        try:
            resp = requests.get(
                HUNTER_ENDPOINT,
                params={
                    "domain":  domain,
                    "api_key": self.api_key,
                    "limit":   5,          # max 5 contacts par domaine
                    # pas de filtre "type" → retourne personal + generic
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})

            contacts = []
            for email_obj in data.get("emails", []):
                contacts.append({
                    "email":      email_obj.get("value", ""),
                    "first_name": email_obj.get("first_name") or "",
                    "last_name":  email_obj.get("last_name")  or "",
                    "position":   email_obj.get("position")   or "",
                    "confidence": email_obj.get("confidence", 0),
                    "type":       email_obj.get("type", ""),
                })

            # Trier par confiance décroissante
            contacts.sort(key=lambda c: c["confidence"], reverse=True)
            return contacts

        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 429:
                logger.warning("[Hunter] Quota mensuel atteint (429)")
            else:
                logger.warning("[Hunter] HTTP error pour %s : %s", domain, e)
            return []
        except Exception as e:
            logger.warning("[Hunter] Erreur pour %s : %s", domain, e)
            return []

    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extrait le domaine depuis une URL (ex: 'http://www.acerinox.com' → 'acerinox.com')."""
        if not url:
            return ""
        try:
            parsed = urlparse(url if url.startswith("http") else f"http://{url}")
            domain = parsed.netloc or parsed.path
            # Supprime le www.
            domain = domain.replace("www.", "").strip()
            return domain if "." in domain else ""
        except Exception:
            return ""
