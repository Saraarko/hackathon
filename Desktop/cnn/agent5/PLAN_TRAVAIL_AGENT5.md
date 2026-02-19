# 🤖 Agent 5 — AUTO LABEL ENGINE
## Plan de Travail Détaillé

> **Projet** : Dataset Intelligence Engine  
> **Agent** : Agent 5 — Auto Label Engine  
> **Rôle** : Pipeline d'annotation automatique intelligent avec validation humaine  
> **Date** : 2026-02-18  

---

## 🎯 Objectif Principal

Développer un moteur d'annotation automatique capable de labelliser des images de manière autonome en combinant plusieurs modèles d'IA (YOLO, SAM, BLIP, CLIP) via une logique de **fusion d'intelligence**, tout en déclenchant une validation humaine lorsque le score de confiance est insuffisant.

---

## 🏗️ Architecture Générale

```
Image Brute
    │
    ▼
┌─────────────────────────────────────────────┐
│              AUTO LABEL ENGINE               │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌───────────┐ │
│  │  YOLO    │  │   SAM    │  │BLIP + CLIP│ │
│  │Detection │  │Segmentat.│  │Classific. │ │
│  └────┬─────┘  └────┬─────┘  └─────┬─────┘ │
│       │             │              │        │
│       └─────────────┴──────────────┘        │
│                     │                       │
│            ┌────────▼────────┐              │
│            │ FUSION ENGINE   │              │
│            │  (Agrégation    │              │
│            │  des scores)    │              │
│            └────────┬────────┘              │
└─────────────────────┼───────────────────────┘
                      │
          ┌───────────▼───────────┐
          │  Score de Confiance   │
          │   ≥ Seuil ?           │
          └───────────┬───────────┘
                      │
          ┌───────────┴───────────┐
          │                       │
    ✅ OUI (Auto)           ❌ NON (Humain)
          │                       │
    Label Sauvegardé      File de Validation
    automatiquement         Humaine
```

---

## 📋 Phases d'Implémentation

### Phase 1 — Mise en Place de l'Infrastructure

**Durée estimée** : 2-3 jours

#### 1.1 Structure du Projet
```
agent5/
├── PLAN_TRAVAIL_AGENT5.md
├── models/
│   ├── yolo_detector.py
│   ├── sam_segmentor.py
│   └── blip_clip_classifier.py
├── fusion/
│   └── fusion_engine.py
├── pipeline/
│   ├── auto_label_pipeline.py
│   └── confidence_evaluator.py
├── validation/
│   ├── human_validation_queue.py
│   └── validation_interface.py
├── storage/
│   ├── label_storage.py
│   └── annotation_schema.py
├── config/
│   └── settings.py
└── tests/
    ├── test_yolo.py
    ├── test_sam.py
    ├── test_fusion.py
    └── test_pipeline.py
```

#### 1.2 Dépendances à Installer
```bash
# Détection
pip install ultralytics          # YOLOv8/v11
pip install torch torchvision    # PyTorch

# Segmentation
pip install segment-anything     # SAM (Meta)

# Classification
pip install transformers         # BLIP (Salesforce)
pip install open-clip-torch      # CLIP (OpenAI)

# Utilitaires
pip install opencv-python
pip install Pillow
pip install numpy
pip install pydantic
pip install fastapi uvicorn      # API de validation humaine
```

#### 1.3 Configuration Initiale (`config/settings.py`)
```python
# Seuils de confiance
CONFIDENCE_THRESHOLD = 0.75      # Seuil global pour auto-label
YOLO_CONFIDENCE_MIN = 0.60       # Seuil minimum YOLO
SAM_IOU_THRESHOLD = 0.85         # Seuil IoU pour SAM
CLIP_SIMILARITY_MIN = 0.70       # Seuil similarité CLIP

# Poids de fusion (somme = 1.0)
FUSION_WEIGHTS = {
    "yolo": 0.40,
    "sam": 0.25,
    "blip": 0.20,
    "clip": 0.15
}

# Chemins des modèles
YOLO_MODEL_PATH = "models/yolov8n.pt"
SAM_CHECKPOINT = "models/sam_vit_h.pth"
```

---

### Phase 2 — Intégration des Modèles

**Durée estimée** : 4-5 jours

#### 2.1 Module YOLO — Détection d'Objets

**Fichier** : `models/yolo_detector.py`

**Responsabilités** :
- Détecter les objets dans l'image
- Retourner les bounding boxes avec scores de confiance
- Retourner les classes détectées

**Sorties** :
```python
{
    "detections": [
        {
            "class": "chat",
            "confidence": 0.92,
            "bbox": [x1, y1, x2, y2],
            "class_id": 15
        }
    ],
    "model_confidence": 0.92
}
```

#### 2.2 Module SAM — Segmentation

**Fichier** : `models/sam_segmentor.py`

**Responsabilités** :
- Prendre les bounding boxes de YOLO comme prompts
- Générer des masques de segmentation précis
- Calculer un score de qualité du masque (IoU)

**Sorties** :
```python
{
    "masks": [...],          # Masques binaires numpy
    "iou_scores": [0.88],    # Qualité de chaque masque
    "model_confidence": 0.88
}
```

#### 2.3 Module BLIP + CLIP — Classification

**Fichier** : `models/blip_clip_classifier.py`

**Responsabilités** :
- **BLIP** : Générer une description textuelle de l'image (image captioning)
- **CLIP** : Calculer la similarité entre l'image et les labels candidats
- Combiner les deux scores pour une classification robuste

**Sorties** :
```python
{
    "blip_caption": "a cat sitting on a chair",
    "clip_scores": {
        "chat": 0.89,
        "chien": 0.12,
        "oiseau": 0.05
    },
    "top_label": "chat",
    "model_confidence": 0.89
}
```

---

### Phase 3 — Fusion Intelligence

**Durée estimée** : 3-4 jours

#### 3.1 Moteur de Fusion (`fusion/fusion_engine.py`)

**Logique de fusion** :

```python
def compute_fusion_score(yolo_result, sam_result, blip_clip_result):
    """
    Agrège les scores de confiance de tous les modèles
    en utilisant une moyenne pondérée.
    """
    weights = FUSION_WEIGHTS
    
    score = (
        yolo_result["model_confidence"] * weights["yolo"] +
        sam_result["model_confidence"] * weights["sam"] +
        blip_clip_result["model_confidence"] * weights["blip"] +
        blip_clip_result["clip_top_score"] * weights["clip"]
    )
    
    # Vérification de la cohérence entre modèles
    consistency_bonus = check_label_consistency(
        yolo_result, blip_clip_result
    )
    
    return min(score + consistency_bonus, 1.0)
```

**Vérification de cohérence** :
- Si YOLO et CLIP détectent la même classe → bonus de +0.05
- Si les labels sont contradictoires → pénalité de -0.10

#### 3.2 Évaluateur de Confiance (`pipeline/confidence_evaluator.py`)

```python
def evaluate_and_route(fusion_score, annotation):
    """
    Route l'annotation vers le stockage automatique
    ou la file de validation humaine.
    """
    if fusion_score >= CONFIDENCE_THRESHOLD:
        return "AUTO_LABEL", annotation
    else:
        return "HUMAN_VALIDATION", annotation
```

---

### Phase 4 — Pipeline Principal

**Durée estimée** : 2-3 jours

#### 4.1 Pipeline Auto-Label (`pipeline/auto_label_pipeline.py`)

**Flux d'exécution** :

```
1. Réception de l'image
2. Prétraitement (resize, normalisation)
3. Inférence YOLO → Détections
4. Inférence SAM (avec prompts YOLO) → Masques
5. Inférence BLIP → Caption
6. Inférence CLIP → Scores de similarité
7. Fusion des scores → Score global
8. Évaluation du seuil
   ├── Score ≥ 0.75 → Sauvegarde automatique
   └── Score < 0.75 → File de validation humaine
9. Logging et traçabilité
```

#### 4.2 Schéma d'Annotation (`storage/annotation_schema.py`)

```python
class Annotation(BaseModel):
    image_id: str
    image_path: str
    timestamp: datetime
    
    # Labels
    detected_class: str
    bbox: List[float]          # [x1, y1, x2, y2]
    mask: Optional[bytes]      # Masque SAM encodé
    
    # Scores
    yolo_confidence: float
    sam_iou: float
    blip_caption: str
    clip_score: float
    fusion_score: float
    
    # Statut
    status: Literal["AUTO_LABELED", "PENDING_HUMAN", "HUMAN_VALIDATED"]
    validated_by: Optional[str]
    validation_timestamp: Optional[datetime]
```

---

### Phase 5 — Interface de Validation Humaine

**Durée estimée** : 3-4 jours

#### 5.1 File d'Attente (`validation/human_validation_queue.py`)

**Fonctionnalités** :
- Stocker les annotations avec score < seuil
- Prioriser par score (les plus bas en premier)
- Notifier les annotateurs disponibles
- Gérer le timeout (réassignation si non traité)

#### 5.2 Interface de Validation (`validation/validation_interface.py`)

**API REST (FastAPI)** :
```
GET  /validation/queue          → Liste des items à valider
GET  /validation/item/{id}      → Détail d'un item
POST /validation/item/{id}      → Soumettre la validation
PUT  /validation/item/{id}      → Corriger le label
DELETE /validation/item/{id}    → Rejeter l'annotation
```

**Interface Web** :
- Affichage de l'image avec les prédictions des modèles
- Visualisation du score de fusion et des scores individuels
- Boutons : ✅ Valider / ✏️ Corriger / ❌ Rejeter
- Affichage du masque SAM superposé

---

### Phase 6 — Tests et Validation

**Durée estimée** : 2-3 jours

#### 6.1 Tests Unitaires
- `test_yolo.py` : Tester la détection sur images de référence
- `test_sam.py` : Vérifier la qualité des masques
- `test_fusion.py` : Valider la logique de fusion
- `test_pipeline.py` : Test end-to-end du pipeline

#### 6.2 Métriques de Performance
| Métrique | Objectif |
|----------|----------|
| Précision auto-label | ≥ 90% |
| Rappel | ≥ 85% |
| Taux d'auto-labellisation | ≥ 70% |
| Temps de traitement/image | ≤ 2 secondes |
| Taux de validation humaine | ≤ 30% |

---

## 📊 Tableau de Bord des Modèles

| Modèle | Rôle | Poids Fusion | Seuil Min |
|--------|------|-------------|-----------|
| YOLOv8 | Détection + BBox | 40% | 0.60 |
| SAM | Segmentation | 25% | 0.85 (IoU) |
| BLIP | Captioning | 20% | N/A |
| CLIP | Classification | 15% | 0.70 |

---

## 🔄 Logique de Décision

```
Score Fusion ≥ 0.75  →  ✅ AUTO-LABEL (sauvegarde automatique)
Score Fusion 0.50-0.74  →  ⚠️ VALIDATION HUMAINE (priorité normale)
Score Fusion < 0.50  →  🔴 VALIDATION HUMAINE (priorité haute)
```

---

## 📅 Planning Global

| Phase | Description | Durée | Statut |
|-------|-------------|-------|--------|
| 1 | Infrastructure & Setup | 2-3 jours | 🔲 À faire |
| 2 | Intégration des Modèles | 4-5 jours | 🔲 À faire |
| 3 | Fusion Intelligence | 3-4 jours | 🔲 À faire |
| 4 | Pipeline Principal | 2-3 jours | 🔲 À faire |
| 5 | Validation Humaine | 3-4 jours | 🔲 À faire |
| 6 | Tests & Validation | 2-3 jours | 🔲 À faire |
| **Total** | | **16-22 jours** | |

---

## 🔗 Intégration avec les Autres Agents

| Agent | Interaction |
|-------|-------------|
| Agent 1 (Collecte) | Fournit les images brutes à labelliser |
| Agent 2 (Prétraitement) | Prétraite les images avant annotation |
| Agent 3 (Stockage) | Reçoit les annotations validées |
| Agent 4 (Qualité) | Vérifie la qualité des annotations produites |
| Agent 6 (Entraînement) | Utilise les datasets annotés pour l'entraînement |

---

## 📝 Notes Techniques

- **GPU recommandé** : NVIDIA avec ≥ 8GB VRAM (pour YOLO + SAM simultanément)
- **RAM** : ≥ 16GB recommandé
- **Format d'annotation** : Compatible COCO JSON et YOLO TXT
- **Logging** : Traçabilité complète de chaque décision d'annotation
- **Versioning des modèles** : Chaque modèle doit être versionné pour reproductibilité

---

*Document généré le 2026-02-18 | Agent 5 — AUTO LABEL ENGINE*
