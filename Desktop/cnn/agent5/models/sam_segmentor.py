# Agent 5 — AUTO LABEL ENGINE
# models/sam_segmentor.py — Segmentation avec SAM (Meta AI)


import numpy as np
import cv2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import SAM_CHECKPOINT, SAM_MODEL_TYPE, SAM_IOU_THRESHOLD


class SAMSegmentor:
    """
    Génère des masques de segmentation précis avec SAM (Segment Anything Model).
    Utilise les bounding boxes de YOLO comme prompts d'entrée.
    """

    def __init__(self, checkpoint: str = SAM_CHECKPOINT, model_type: str = SAM_MODEL_TYPE):
        print(f"[SAM] Chargement du modèle : {checkpoint}")
        try:
            from segment_anything import sam_model_registry, SamPredictor
            sam = sam_model_registry[model_type](checkpoint=checkpoint)
            sam.to(device="cpu")  # Changer en "cuda" si GPU disponible
            self.predictor = SamPredictor(sam)
            self.available = True
            print("[SAM] ✅ Modèle chargé avec succès")
        except Exception as e:
            print(f"[SAM] ⚠️ Impossible de charger SAM : {e}")
            print("[SAM] Mode dégradé activé (score SAM = 0.5 par défaut)")
            self.predictor = None
            self.available = False

    def segment(self, image_path: str, bboxes: list) -> dict:
        """
        Génère des masques pour chaque bounding box fournie.

        Args:
            image_path: Chemin vers l'image
            bboxes: Liste de bounding boxes [[x1,y1,x2,y2], ...]

        Returns:
            dict avec les masques et scores IoU
        """
        print(f"[SAM] Segmentation de : {image_path} | {len(bboxes)} bbox(es)")

        # Mode dégradé si SAM non disponible
        if not self.available or not bboxes:
            print("[SAM] ⚠️ Mode dégradé — score par défaut : 0.5")
            return {
                "masks":            [],
                "iou_scores":       [0.5] * len(bboxes),
                "model_confidence": 0.5,
            }

        # Charger l'image
        image = cv2.imread(image_path)
        if image is None:
            raise FileNotFoundError(f"[SAM] ❌ Image introuvable : {image_path}")
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Définir l'image dans le predictor
        self.predictor.set_image(image_rgb)

        masks_list  = []
        iou_scores  = []

        for bbox in bboxes:
            import torch
            bbox_array = np.array(bbox)  # [x1, y1, x2, y2]

            masks, scores, _ = self.predictor.predict(
                box=bbox_array[None, :],  # Format attendu par SAM
                multimask_output=True,    # Retourne 3 masques, on prend le meilleur
            )

            # Prendre le masque avec le meilleur score
            best_idx   = np.argmax(scores)
            best_mask  = masks[best_idx]
            best_score = float(scores[best_idx])

            masks_list.append(best_mask)
            iou_scores.append(round(best_score, 4))

            print(f"[SAM]   → Masque généré | IoU score : {best_score:.2f}")

        avg_iou = round(float(np.mean(iou_scores)), 4) if iou_scores else 0.5

        print(f"[SAM] ✅ Segmentation terminée | Score moyen IoU : {avg_iou:.2f}")

        return {
            "masks":            masks_list,
            "iou_scores":       iou_scores,
            "model_confidence": avg_iou,
        }


# TEST RAPIDE — python models/sam_segmentor.py <image> x1 y1 x2 y2

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage : python models/sam_segmentor.py <image> <x1> <y1> <x2> <y2>")
        sys.exit(1)

    img_path = sys.argv[1]
    bbox     = [float(v) for v in sys.argv[2:6]]

    segmentor = SAMSegmentor()
    result    = segmentor.segment(img_path, [bbox])

    print("\n--- Résultats SAM ---")
    print(f"  Nombre de masques : {len(result['masks'])}")
    print(f"  Scores IoU        : {result['iou_scores']}")
    print(f"  Score global      : {result['model_confidence']}")
