# ============================================================
# Agent 5 — AUTO LABEL ENGINE
# models/yolo_detector.py — Détection d'objets avec YOLOv8
# ============================================================

from ultralytics import YOLO
import numpy as np
import sys
import os

# Ajouter le dossier parent au path pour importer config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import YOLO_MODEL_PATH, YOLO_CONFIDENCE_MIN


class YOLODetector:
    """
    Détecte les objets dans une image avec YOLOv8.
    Retourne les bounding boxes, classes et scores de confiance.
    """

    def __init__(self, model_path: str = YOLO_MODEL_PATH):
        print(f"[YOLO] Chargement du modèle : {model_path}")
        # ultralytics télécharge automatiquement le modèle si absent
        self.model = YOLO(model_path)
        print("[YOLO] ✅ Modèle chargé avec succès")

    def detect(self, image_path: str) -> dict:
        """
        Lance la détection sur une image.

        Args:
            image_path: Chemin vers l'image

        Returns:
            dict avec les détections et le score de confiance global
        """
        print(f"[YOLO] Analyse de : {image_path}")
        results = self.model(image_path, conf=YOLO_CONFIDENCE_MIN, verbose=False)

        detections = []
        best_confidence = 0.0

        for result in results:
            boxes = result.boxes
            if boxes is None or len(boxes) == 0:
                print("[YOLO] ⚠️ Aucun objet détecté")
                continue

            for box in boxes:
                confidence = float(box.conf[0])
                class_id   = int(box.cls[0])
                class_name = self.model.names[class_id]
                bbox       = box.xyxy[0].tolist()  # [x1, y1, x2, y2]

                detections.append({
                    "class":      class_name,
                    "class_id":   class_id,
                    "confidence": round(confidence, 4),
                    "bbox":       [round(v, 2) for v in bbox],
                })

                if confidence > best_confidence:
                    best_confidence = confidence

        # Trier par confiance décroissante
        detections.sort(key=lambda d: d["confidence"], reverse=True)

        print(f"[YOLO] ✅ {len(detections)} objet(s) détecté(s) | Meilleur score : {best_confidence:.2f}")

        return {
            "detections":        detections,
            "model_confidence":  round(best_confidence, 4),
            "top_detection":     detections[0] if detections else None,
        }


# ============================================================
# TEST RAPIDE — exécuter directement : python models/yolo_detector.py
# ============================================================
if __name__ == "__main__":
    import sys

    # Utilise une image de test si fournie, sinon une image par défaut
    test_image = sys.argv[1] if len(sys.argv) > 1 else "test.jpg"

    if not os.path.exists(test_image):
        print(f"[YOLO] ❌ Image introuvable : {test_image}")
        print("[YOLO] Usage : python models/yolo_detector.py <chemin_image>")
        sys.exit(1)

    detector = YOLODetector()
    result   = detector.detect(test_image)

    print("\n--- Résultats YOLO ---")
    for det in result["detections"]:
        print(f"  • {det['class']} | confiance: {det['confidence']} | bbox: {det['bbox']}")
    print(f"  Score global : {result['model_confidence']}")
