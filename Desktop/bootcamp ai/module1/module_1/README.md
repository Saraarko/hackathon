# Module 1 — Extraction Automatique de Spécifications Techniques

**INDUSTRIE IA** — OpenIndustry Algérie

---

## 📋 Présentation

Le **Module 1** est le premier maillon critique et autonome de la pipeline **INDUSTRIE IA**.  

Il transforme un **datasheet technique PDF** (KSB, GrabCAD, fournisseurs, etc.) en un **JSON structuré, normalisé et riche** prêt à être consommé par tous les modules aval (CAD, sourcing, TCO, jumeau numérique, etc.).

Conçu pour être **robuste, générique et production-ready**, il gère à la fois les pompes centrifuges, vannes et tout équipement mécanique industriel.

---

## ✨ Fonctionnalités Principales

- Extraction intelligente via LLM (Anthropic Claude – compatible Ollama)
- Parser PDF industriel haute fidélité avec `pdfplumber`
- Gestion avancée des diamètres : `nominal_diameter_mm`, `suction_diameter_mm`, `outlet_diameter_mm`
- Calcul objectif de confiance (`compute_confidence`)
- Système intelligent de warnings
- Cache MD5 performant pour éviter les appels LLM redondants
- Exports spécialisés pour chaque module aval
- Architecture **LangGraph** modulaire avec retry automatique
- Tests unitaires complets

---

## 📁 Structure du Projet

```bash
module_1/
├── __main__.py                 # Point d'entrée CLI
├── __init__.py                 # Fonction run() réutilisable
├── config.py                   # Configuration LLM
├── requirements.txt
├── README.md
│
├── agents/
│   ├── extraction_nodes.py     # Noeuds LangGraph
│   ├── graph.py                # Construction du graphe
│
├── prompts/
│   └── extraction_prompt.py    # Prompts optimisés KSB
│
├── schemas/
│   ├── specs.py                # Modèle Pydantic MechanicalEquipmentSpecs
│   └── state.py                # État partagé du graphe
│
├── parsers/
│   ├── parser_factory.py
│   ├── pdf_parser.py           # Texte + tableaux
│   └── dwg_parser.py           # Support DXF
│
├── cache/
│   ├── cache_manager.py        # Cache basé sur hash MD5
│
├── outputs/
│   ├── writer.py               # Sauvegarde + exports spécialisés
│
├── plans/                      # PDFs de test
│   └── KSBdatasheet4025.pdf
│
└── tests/
    └── test_module1.py         # Suite de tests unitaires

    🚀 Installation & Utilisation
1. Installation
Bashcd module_1
pip install -r requirements.txt

# Commande recommandée
python -m module_1 --pdf plans/KSBdatasheet4025.pdf

# Avec Ollama local
python -m module_1 --pdf plans/KSBdatasheet4025.pdf --provider ollama
