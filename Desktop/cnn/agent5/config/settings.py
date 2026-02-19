# ============================================================
# Agent 5 — AUTO LABEL ENGINE
# config/settings.py — Configuration globale
# ============================================================

# ----------------------------
# Seuils de confiance
# ----------------------------
CONFIDENCE_THRESHOLD = 0.75      # Seuil global pour auto-label
YOLO_CONFIDENCE_MIN  = 0.60      # Seuil minimum YOLO
SAM_IOU_THRESHOLD    = 0.85      # Seuil IoU pour SAM
CLIP_SIMILARITY_MIN  = 0.70      # Seuil similarité CLIP

# ----------------------------
# Poids de fusion (somme = 1.0)
# ----------------------------
FUSION_WEIGHTS = {
    "yolo": 0.40,
    "sam":  0.25,
    "blip": 0.20,
    "clip": 0.15,
}

# ----------------------------
# Chemins des modèles
# ----------------------------
YOLO_MODEL_PATH  = "models/yolov8n.pt"       # Téléchargé automatiquement par ultralytics
SAM_CHECKPOINT   = "models/sam_vit_h.pth"    # À télécharger manuellement
SAM_MODEL_TYPE   = "vit_h"                   # vit_h | vit_l | vit_b

BLIP_MODEL_NAME  = "Salesforce/blip-image-captioning-base"
CLIP_MODEL_NAME  = "ViT-B-32"
CLIP_PRETRAINED  = "openai"

# ----------------------------
# Stockage
# ----------------------------
OUTPUT_DIR       = "output/annotations"
QUEUE_DIR        = "output/validation_queue"

# ----------------------------
# Labels candidats (à adapter à ton dataset)
# ----------------------------
CANDIDATE_LABELS = [
    "chat", "chien", "voiture", "personne",
    "vélo", "moto", "camion", "bus",
    "oiseau", "arbre", "maison", "téléphone",
]
