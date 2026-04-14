"""
Pipeline Global — Nœuds LangGraph (un par module)

Chaque nœud :
  - reçoit le GlobalState
  - appelle le module correspondant
  - retourne un dict partiel fusionné dans le state
"""

from __future__ import annotations

import importlib.util
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── helpers ──────────────────────────────────────────────────────────────── #

def _add_path(module_dir: str):
    """Ajoute un répertoire en tête de sys.path (idempotent)."""
    p = os.path.join(ROOT, module_dir)
    if p not in sys.path:
        sys.path.insert(0, p)


def _import_from(module_dir: str, module_name: str):
    """Importe un module par chemin absolu pour éviter les conflits de noms."""
    module_path = os.path.join(ROOT, module_dir, f"{module_name}.py")
    spec = importlib.util.spec_from_file_location(
        f"{module_dir}.{module_name}", module_path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _safe(fn, state: dict, key: str) -> dict:
    """Execute fn(state), capture les exceptions dans state['errors']."""
    try:
        return fn(state)
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(f"[{key}] {type(exc).__name__}: {exc}")
        return {**state, "errors": errors, key: {"error": str(exc)}}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 1 — Extraction PDF
# ══════════════════════════════════════════════════════════════════════════════

def node_extraction(state: dict) -> dict:
    """
    Module 1 : Lit le PDF technique et extrait les specs via Claude.
    Output : met à jour diameter, pressure, material, valve_type, quantity
             depuis les specs extraites — tous les modules avals s'en nourrissent.
    """
    print("\n[Pipeline] ▶ Module 1 — Extraction PDF")

    pdf_path = state.get("pdf_path", "")
    if not pdf_path or not os.path.exists(pdf_path):
        print(f"  ⚠ PDF introuvable ({pdf_path}) — paramètres par défaut conservés")
        return {**state, "extraction_result": {}}

    # Module1 est un package : on ajoute module1/ au path
    _add_path("module1")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, "module4", ".env"))   # contient ANTHROPIC_API_KEY
    load_dotenv(os.path.join(ROOT, "module5", ".env"))

    from module_1.config import get_llm_client
    from module_1 import run as m1_run

    client = get_llm_client()
    specs  = m1_run(pdf_path=pdf_path, llm_client=client, save_output=True,
                    output_dir=os.path.join(ROOT, "module1", "module_1", "outputs"))

    if specs is None:
        print("  ⚠ Extraction échouée — paramètres par défaut conservés")
        return {**state, "extraction_result": {"error": "extraction failed"}}

    # ── Mapping specs → GlobalState ──────────────────────────────────────────
    category = specs.equipment_category or "unknown"
    diameter = specs.dimensions.nominal_diameter_mm
    pressure = specs.hydraulics.nominal_pressure_bar
    material = specs.body_material or state.get("material", "316L")
    quantity = specs.quantity_required or state.get("quantity", 200)
    length   = specs.dimensions.face_to_face_mm or specs.dimensions.overall_length_mm

    updates = {
        "extraction_result": specs.dict(),
        "valve_type":  category if category != "unknown" else state.get("valve_type", "valve"),
        "diameter":    int(diameter)  if diameter else state.get("diameter", 100),
        "pressure":    int(pressure)  if pressure else state.get("pressure", 40),
        "material":    str(material),
        "quantity":    int(quantity),
        "length":      int(length)    if length   else state.get("length", 250),
    }

    print(f"  ✓ Équipement    : {specs.equipment_category} / {specs.equipment_subtype}")
    print(f"  ✓ Référence     : {specs.part_number or specs.model_reference or 'N/A'}")
    print(f"  ✓ DN            : {updates['diameter']} mm")
    print(f"  ✓ Pression      : {updates['pressure']} bar")
    print(f"  ✓ Matériau      : {updates['material']}")
    print(f"  ✓ Confiance     : {specs.extraction_confidence:.0%}")

    return {**state, **updates}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 2 — CAD & Design
# ══════════════════════════════════════════════════════════════════════════════

def node_design(state: dict) -> dict:
    """
    Module 2 : Applique les règles de conception, génère géométrie + fichiers CAD.
    Input  : valve_type, diameter, pressure, material, length
    Output : design_result
    """
    print("\n[Pipeline] ▶ Module 2 — CAD & Design")

    _add_path("module2")

    m2_graph = _import_from("module2", "graph")
    build_m2 = m2_graph.build_graph

    m2_state = {
        "type":     state.get("valve_type", "valve"),
        "diameter": state.get("diameter", 100),
        "pressure": state.get("pressure", 40),
        "material": state.get("material", "316L"),
        "length":   state.get("length", 250),
    }

    result = build_m2().invoke(m2_state)

    print(f"  ✓ Validation : {result.get('validation', {}).get('status', '?')}")
    print(f"  ✓ Warnings   : {result.get('validation', {}).get('warnings', [])}")

    return {**state, "design_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 3 — Rendu 3D
# ══════════════════════════════════════════════════════════════════════════════

def node_render(state: dict) -> dict:
    """
    Module 3 : Génère le rendu 3D matplotlib de la vanne.
    Input  : design_result (geometry)
    Output : render_result
    """
    print("\n[Pipeline] ▶ Module 3 — Rendu 3D")

    _add_path("module3")

    os.makedirs(os.path.join(ROOT, "pipeline", "outputs"), exist_ok=True)
    orig_dir = os.getcwd()

    try:
        os.chdir(os.path.join(ROOT, "module3"))
        os.makedirs("outputs", exist_ok=True)

        from blender_runner import render_video
        render_video(
            diameter_mm    = float(state.get("diameter", 100)),
            material       = str(state.get("material", "316L")),
            equipment_type = str(state.get("valve_type", "valve")),
        )

        # Pick whichever format was generated (mp4 if ffmpeg present, else gif)
        for ext in ("mp4", "gif"):
            candidate = os.path.join(ROOT, "module3", "outputs", f"valve.{ext}")
            if os.path.exists(candidate):
                video_path = candidate
                break
        else:
            video_path = os.path.join(ROOT, "module3", "outputs", "valve.gif")

        result = {
            "video_path":   video_path,
            "scene_config": {"material": state.get("material", "316L")},
            "status":       "ok",
        }
        print(f"  ✓ Rendu  : {video_path}")
    finally:
        os.chdir(orig_dir)

    return {**state, "render_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 4 — Sourcing
# ══════════════════════════════════════════════════════════════════════════════

def node_sourcing(state: dict) -> dict:
    """
    Module 4 : Identifie les fournisseurs via Wikidata + UN Comtrade,
               puis enrichit les contacts via Hunter.io.
    Input  : material (ex: "Stainless Steel 316L")
    Output : sourcing_result → suppliers[], market_analysis, trade_data
    """
    print("\n[Pipeline] ▶ Module 4 — Sourcing fournisseurs")

    _add_path("module4")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
    load_dotenv(os.path.join(ROOT, "module4", ".env"))

    from wikidata_agent    import WikidataSourceAgent
    from comtrade_agent    import ComtradeAgent
    from hunter_agent      import HunterAgent
    from madeinchina_agent import MadeInChinaAgent

    # Normalisation du matériau
    raw_mat        = state.get("material", "316L").upper()
    material       = "Stainless Steel 316L" if "316" in raw_mat else raw_mat
    equipment_type = state.get("valve_type", "unknown")

    wikidata = WikidataSourceAgent()
    comtrade = ComtradeAgent()

    sourcing = wikidata.run(material, equipment_type=equipment_type)
    trade    = comtrade.run(material)

    search_mode = sourcing["market_analysis"].get("search_mode", "material")
    eq_label    = sourcing["market_analysis"].get("equipment_type", equipment_type)
    print(f"  Mode recherche : {search_mode} ({eq_label})")

    # ── Scraping prix Made-in-China ─────────────────────────────────────────
    mic       = MadeInChinaAgent()
    mic_data  = mic.run(equipment_type=equipment_type, material=material)
    mic_avg   = mic_data.get("price_avg", 0.0)
    mic_min   = mic_data.get("price_min", 0.0)
    mic_max   = mic_data.get("price_max", 0.0)
    print(f"  ✓ Made-in-China : {len(mic_data.get('prices', []))} prix trouvés "
          f"· moy. ${mic_avg:.0f} (${mic_min:.0f}–${mic_max:.0f}) USD")

    suppliers = sourcing["suppliers"]

    # ── Enrichissement Hunter.io ────────────────────────────────────────────
    hunter    = HunterAgent()
    suppliers = hunter.enrich_suppliers(suppliers, max_suppliers=10)

    nb_contacts = sum(1 for s in suppliers if s.get("email_principal") or s.get("contact_name"))
    print(f"  ✓ {len(suppliers)} fournisseurs · {nb_contacts} contacts Hunter.io trouvés")

    # Ajouter les données MIC à l'analyse marché
    sourcing["market_analysis"]["mic_price_avg_usd"] = mic_avg
    sourcing["market_analysis"]["mic_price_min_usd"] = mic_min
    sourcing["market_analysis"]["mic_price_max_usd"] = mic_max

    result = {
        "material":        material,
        "suppliers":       suppliers,
        "market_analysis": sourcing["market_analysis"],
        "trade_data":      trade,
        "mic_prices":      mic_data,
    }

    avg = result["market_analysis"].get("avg_price_eur", 0)
    print(f"  ✓ Prix moyen marché : {avg} €/kg")

    return {**state, "sourcing_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — Helpers
# ══════════════════════════════════════════════════════════════════════════════

def _map_wikidata_supplier(s: dict, idx: int, base_price: float = 980.0) -> dict:
    """
    Convertit un fournisseur Wikidata (module 4) vers le format
    attendu par negotiate_node (module 5).
    Les champs manquants (prix, délai, certifs) sont estimés.
    """
    # Légère variation de prix par rang pour simuler des catalogues différents
    # idx=0 → le moins cher, idx=2 → le plus cher
    price = round(base_price * (1.0 + idx * 0.08), 2)

    return {
        "id":                 s.get("wikidata_id") or f"WD{idx:03d}",
        "name":               s.get("name", "Unknown Supplier"),
        "country":            s.get("country", "Unknown"),
        "city":               "",
        "description":        s.get("description") or f"Fournisseur industriel — {s.get('material', '')}",
        "price_per_unit_usd": price,
        "min_quantity":       50,
        "delivery_days":      60,
        "certifications":     "ISO 9001",
        "email":              s.get("email_principal", ""),
        "phone":              "",
        # Champs bonus conservés depuis Wikidata/Hunter
        "website":            s.get("website", ""),
        "contact_name":       s.get("contact_name", ""),
        "contact_position":   s.get("contact_position", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 5 — Négociation
# ══════════════════════════════════════════════════════════════════════════════

def node_negotiation(state: dict) -> dict:
    """
    Module 5 : Négocie avec les top-3 fournisseurs via Claude Haiku.
    Utilise build_graph / build_initial_state / load_suppliers de negotiation_agent.
    Output : negotiation_result → best_deal, all_negotiations
    """
    print("\n[Pipeline] ▶ Module 5 — Négociation IA (Claude Haiku)")

    _add_path("module5")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))
    load_dotenv(os.path.join(ROOT, "module5", ".env"))  # credentials email + ANTHROPIC_API_KEY

    from negotiation_agent import build_graph, build_initial_state, load_suppliers, ORDER_DEFAULTS

    quantity = int(state.get("quantity", 200))
    material = state.get("material", "316L")
    eq_type  = state.get("valve_type", "valve")
    diameter = state.get("diameter", 100)
    pressure = state.get("pressure", 40)

    product_desc = f"{eq_type} industriel(le) — DN{diameter} — {pressure} bar — {material}"

    order = {
        **ORDER_DEFAULTS,
        "quantity": quantity,
        "product":  product_desc,
    }

    # ── Fournisseurs : priorité aux résultats réels de Module 4 ──────────────
    m4_suppliers = state.get("sourcing_result", {}).get("suppliers", [])

    if m4_suppliers:
        # Prix de base : utiliser le prix moyen Made-in-China si disponible
        mic_avg    = state.get("sourcing_result", {}).get("mic_prices", {}).get("price_avg", 0.0)
        base_price = mic_avg if mic_avg > 0 else ORDER_DEFAULTS.get("max_price", 980.0)
        suppliers = [
            _map_wikidata_supplier(s, idx, base_price)
            for idx, s in enumerate(m4_suppliers[:3])
        ]
        print(f"  (utilise les {len(suppliers)} fournisseurs trouvés par Module 4)")
    else:
        # Fallback : CSV local de module5
        suppliers = load_suppliers()[:3]
        print("  (fallback : fournisseurs CSV module5)")

    graph = build_graph()

    negotiations = []
    for supplier in suppliers:
        thread_cfg = {"configurable": {"thread_id": f"pipeline_{supplier['id']}"}}
        catalog    = float(supplier["price_per_unit_usd"])

        # Round 0 — ouverture automatique (last_input vide)
        s0 = build_initial_state(supplier)
        s0 = {**s0, "order": order}
        current = graph.invoke(s0, config=thread_cfg)

        # Rounds 1-7 — réponse simulée du fournisseur pour alimenter last_input
        for _ in range(7):
            if current.get("status") in ("agreed", "rejected"):
                break
            best_so_far = current.get("current_best_price", catalog)
            counter     = round(best_so_far * 0.97, 2)   # fournisseur concède 3 %
            simulated   = (
                f"Nous reconnaissons votre intérêt pour {quantity} unités. "
                f"Notre meilleure offre révisée est {counter:.2f} USD/unité avec livraison 45 jours."
            )
            current = graph.invoke({"last_input": simulated}, config=thread_cfg)

        negotiations.append(current)

    # Meilleur deal parmi les accords obtenus
    agreed = [n for n in negotiations if n.get("status") == "agreed" and n.get("agreement")]

    if agreed:
        best_neg = min(agreed, key=lambda n: n["agreement"]["price_per_unit"])
        agr      = best_neg["agreement"]
        catalog  = float(best_neg["supplier"]["price_per_unit_usd"])
        best_deal = {
            "supplier_name":            agr["supplier_name"],
            "counter_offer_price_eur":  round(agr["price_per_unit"] * 0.92, 2),
            "savings_pct":              round((catalog - agr["price_per_unit"]) / catalog * 100, 1),
        }
    elif negotiations:
        # Pas d'accord — prendre le moins cher en cours
        cheapest  = min(negotiations, key=lambda n: n.get("current_best_price", float("inf")))
        s         = cheapest["supplier"]
        catalog   = float(s["price_per_unit_usd"])
        cur_price = cheapest.get("current_best_price", catalog)
        best_deal = {
            "supplier_name":            s["name"],
            "counter_offer_price_eur":  round(cur_price * 0.92, 2),
            "savings_pct":              round((catalog - cur_price) / catalog * 100, 1),
        }
    else:
        best_deal = {}

    result = {
        "total_suppliers_negotiated": len(negotiations),
        "best_deal":                  best_deal,
        "all_negotiations": [
            {
                "supplier": n["supplier"]["name"],
                "status":   n.get("status"),
                "rounds":   n.get("rounds", 0),
                "price":    n.get("current_best_price"),
            }
            for n in negotiations
        ],
    }

    print(f"  ✓ {result['total_suppliers_negotiated']} négociations")
    if best_deal:
        print(f"  ✓ Meilleur deal : {best_deal.get('supplier_name')} à {best_deal.get('counter_offer_price_eur')} €/unité")
        print(f"  ✓ Économies     : {best_deal.get('savings_pct', 0)}%")

    return {**state, "negotiation_result": result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 6 — Analyse financière
# ══════════════════════════════════════════════════════════════════════════════

def node_financial(state: dict) -> dict:
    """
    Module 6 : Projections financières, Monte Carlo, ROI, rapport.
    Input  : coût unitaire négocié × quantité → base_cost
    Output : financial_result → roi, risk, scenarios, report
    """
    print("\n[Pipeline] ▶ Module 6 — Analyse financière")

    _add_path("module6")

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, ".env"))

    m6_graph = _import_from("module6", "graph")
    build_m6 = m6_graph.build_graph

    # Calcul du coût de base depuis le meilleur deal négocié
    best_deal = state.get("negotiation_result", {}).get("best_deal", {})
    price_per_kg = best_deal.get("counter_offer_price_eur", 2.5)
    quantity     = state.get("quantity", 200)

    # Estimation coût total matière (prix × quantité × 1kg moyen par vanne)
    base_cost = round(price_per_kg * quantity, 2)

    orig_dir = os.getcwd()
    try:
        os.chdir(os.path.join(ROOT, "module6"))
        os.makedirs("outputs", exist_ok=True)

        m6_state = {"base_cost": base_cost}
        result   = build_m6().invoke(m6_state)

        financial_result = {
            "base_cost":  base_cost,
            "roi":        result.get("roi"),
            "risk":       result.get("risk"),
            "scenarios":  result.get("scenarios"),
            "inflation":  result.get("inflation"),
            "total_cost": result.get("total_cost"),
            "mc":         result.get("mc"),
            "status":     "ok",
        }
    finally:
        os.chdir(orig_dir)

    print(f"  ✓ Coût base : {base_cost} €")
    print(f"  ✓ ROI       : {financial_result.get('roi')}")
    print(f"  ✓ Risque    : {financial_result.get('risk')}")

    return {**state, "financial_result": financial_result}


# ══════════════════════════════════════════════════════════════════════════════
# MODULE 7 — Business Plan
# ══════════════════════════════════════════════════════════════════════════════

def node_businessplan(state: dict) -> dict:
    """
    Module 7 : Génère le business plan complet (financials, NPV, SWOT, PDF/Excel).
    Input  : extraction_result (M1) + sourcing_result (M4) + financial_result (M6)
    Output : businessplan_result
    """
    print("\n[Pipeline] ▶ Module 7 — Business Plan")

    # Module 7 est un package — on ajoute ROOT au path
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT, "module4", ".env"))
    load_dotenv(os.path.join(ROOT, "module5", ".env"))
    load_dotenv(os.path.join(ROOT, "module7", ".env"))

    import module7.claude_llm as _claude_mod
    import module7.business_plan_agent as _bp_mod

    llm = _claude_mod.ClaudeLLM()

    # ── Mapping des données des modules amont ────────────────────────────────

    # Module 1 → specs
    extraction = state.get("extraction_result", {})
    specs = {
        "type":     extraction.get("equipment_category") or state.get("valve_type", "valve"),
        "diameter": state.get("diameter", 100),
        "pressure": state.get("pressure", 40),
        "material": state.get("material", "316L"),
    }

    # Module 4 → suppliers
    suppliers = state.get("sourcing_result", {}).get("suppliers", [])

    # Module 5 → prix d'achat négocié
    best_deal      = state.get("negotiation_result", {}).get("best_deal", {})
    purchase_price = float(best_deal.get("counter_offer_price_eur", 0.0) or 0.0)

    # Module 6 → tco (coût total d'acquisition sur 10 ans)
    fin = state.get("financial_result", {})
    base_cost  = float(fin.get("base_cost", 0.0) or 0.0)
    total_cost = float(fin.get("total_cost") or base_cost)

    # Marge industrielle standard B2B (35 %) : le prix de revente/valorisation
    # dépasse le coût d'achat pour que le projet soit rentable
    INDUSTRIAL_MARGIN = 1.35
    price_per_unit = round(purchase_price * INDUSTRIAL_MARGIN, 2)

    tco = {
        # Coût total d'acquisition sur 10 ans (achat + maintenance 2 %/an)
        "total_cost_10y": total_cost * 10 + base_cost * 0.02 * 10,
        "maintenance":    base_cost * 0.02,
    }

    quantity = int(state.get("quantity", 200))

    # ── Appel business_agent ─────────────────────────────────────────────────
    orig_dir = os.getcwd()
    try:
        os.chdir(os.path.join(ROOT, "module7"))
        os.makedirs("output", exist_ok=True)

        m7_state = {
            "specs":          specs,
            "suppliers":      suppliers,
            "tco":            tco,
            "quantity":       quantity,
            "price_per_unit": float(price_per_unit),
        }

        result = _bp_mod.business_agent(m7_state, llm)
    finally:
        os.chdir(orig_dir)

    businessplan_result = {
        "financials":    result.get("financials", {}),
        "projections":   result.get("projections", []),
        "npv":           result.get("npv", 0.0),
        "decision":      result.get("decision", "N/A"),
        "swot":          result.get("swot", ""),
        "summary":       result.get("summary", ""),
        "pdf_path":      os.path.join(ROOT, "module7", "output", "business.pdf"),
        "excel_path":    os.path.join(ROOT, "module7", "output", "business.xlsx"),
        "status":        "ok",
    }

    print(f"  ✓ Décision  : {businessplan_result['decision']}")
    print(f"  ✓ NPV 3 ans : ${businessplan_result['npv']:,.0f}")
    print(f"  ✓ Rapport   : {businessplan_result['pdf_path']}")

    return {**state, "businessplan_result": businessplan_result}


# ══════════════════════════════════════════════════════════════════════════════
# SYNTHÈSE FINALE
# ══════════════════════════════════════════════════════════════════════════════

def node_summary(state: dict) -> dict:
    """Nœud final : construit le résumé exécutif du pipeline."""
    print("\n[Pipeline] ▶ Synthèse finale")

    best_deal = state.get("negotiation_result", {}).get("best_deal", {})
    fin       = state.get("financial_result", {})
    bp        = state.get("businessplan_result", {})

    summary = {
        "valve": {
            "type":     state.get("valve_type"),
            "diameter": state.get("diameter"),
            "pressure": state.get("pressure"),
            "material": state.get("material"),
            "validation": state.get("design_result", {}).get("validation", {}),
        },
        "render": {
            "video": state.get("render_result", {}).get("video_path"),
        },
        "sourcing": {
            "total_suppliers": len(state.get("sourcing_result", {}).get("suppliers", [])),
            "avg_market_price": state.get("sourcing_result", {}).get("market_analysis", {}).get("avg_price_eur"),
        },
        "negotiation": {
            "supplier":       best_deal.get("supplier_name"),
            "price_eur_kg":   best_deal.get("counter_offer_price_eur"),
            "savings_pct":    best_deal.get("savings_pct"),
            "recommendation": best_deal.get("final_recommendation"),
        },
        "finance": {
            "base_cost_eur": fin.get("base_cost"),
            "total_cost":    fin.get("total_cost"),
            "roi":           fin.get("roi"),
            "risk":          fin.get("risk"),
        },
        "businessplan": {
            "decision":   bp.get("decision"),
            "npv":        bp.get("npv"),
            "pdf_path":   bp.get("pdf_path"),
            "excel_path": bp.get("excel_path"),
        },
        "errors": state.get("errors", []),
    }

    print("\n" + "="*55)
    print("  PIPELINE COMPLET — RÉSUMÉ EXÉCUTIF")
    print("="*55)
    print(f"  Vanne        : ⌀{summary['valve']['diameter']}mm · {summary['valve']['pressure']}bar · {summary['valve']['material']}")
    print(f"  Validation   : {summary['valve']['validation'].get('status', '?')}")
    print(f"  Fournisseurs : {summary['sourcing']['total_suppliers']} identifiés")
    print(f"  Meilleur deal: {summary['negotiation']['supplier']} à {summary['negotiation']['price_eur_kg']} €/kg (-{summary['negotiation']['savings_pct']}%)")
    print(f"  Coût total   : {summary['finance']['base_cost_eur']} €")
    print(f"  ROI          : {summary['finance']['roi']}")
    print(f"  Risque       : {summary['finance']['risk']}")
    if summary["errors"]:
        print(f"  Erreurs      : {len(summary['errors'])}")
        for e in summary["errors"]:
            print(f"    - {e}")
    print("="*55 + "\n")

    return {**state, "summary": summary}
