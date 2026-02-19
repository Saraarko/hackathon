import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import FUSION_WEIGHTS
class FusionEngine:
    def __init__(self):
        self.weights = FUSION_WEIGHTS
def compute_score(self, yolo_result, sam_result, blip_clip_result):
        
        # 1. Récupérer les scores de chaque modèle
        yolo_score = yolo_result.get("model_confidence", 0.0)
        sam_score  = sam_result.get("model_confidence", 0.5)
        blip_score = blip_clip_result.get("model_confidence", 0.0)
        clip_score = blip_clip_result.get("clip_top_score", 0.0)

        # 2. Calculer la moyenne pondérée
        fusion_score = (
            yolo_score * self.weights["yolo"] +
            sam_score  * self.weights["sam"]  +
            blip_score * self.weights["blip"] +
            clip_score * self.weights["clip"]
        )

        # 3. Vérifier si YOLO et CLIP sont d'accord sur le label
        yolo_label = ""
        clip_label = blip_clip_result.get("top_label", "")
        if yolo_result.get("top_detection"):
            yolo_label = yolo_result["top_detection"].get("class", "")

        if yolo_label and clip_label and yolo_label.lower() == clip_label.lower():
            fusion_score += 0.05  # Bonus si accord entre modèles
            print(f"[FUSION] ✅ Accord YOLO+CLIP sur '{yolo_label}' → bonus +0.05")
        elif yolo_label and clip_label:
            fusion_score -= 0.05  # Pénalité si contradiction
            print(f"[FUSION] ⚠️ Désaccord YOLO('{yolo_label}') vs CLIP('{clip_label}') → -0.05")

        # 4. Garder le score entre 0 et 1
        fusion_score = round(min(max(fusion_score, 0.0), 1.0), 4)

        print(f"[FUSION] Score final : {fusion_score}")
        return fusion_score

