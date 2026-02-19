# ============================================================
# Agent 5 — AUTO LABEL ENGINE
# models/blip_clip_classifier.py — Classification BLIP + CLIP
# ============================================================

import sys
import os
from PIL import Image

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import (
    BLIP_MODEL_NAME,
    CLIP_MODEL_NAME,
    CLIP_PRETRAINED,
    CANDIDATE_LABELS,
    CLIP_SIMILARITY_MIN,
)


class BLIPCLIPClassifier:
    """
    Combine BLIP (image captioning) et CLIP (similarité image-texte)
    pour classifier une image parmi des labels candidats.
    """

    def __init__(self):
        self._load_blip()
        self._load_clip()

    def _load_blip(self):
        """Charge le modèle BLIP pour le captioning."""
        print(f"[BLIP] Chargement du modèle : {BLIP_MODEL_NAME}")
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import torch
            self.blip_processor = BlipProcessor.from_pretrained(BLIP_MODEL_NAME)
            self.blip_model     = BlipForConditionalGeneration.from_pretrained(BLIP_MODEL_NAME)
            self.blip_model.eval()
            self.blip_available = True
            print("[BLIP] ✅ Modèle chargé avec succès")
        except Exception as e:
            print(f"[BLIP] ⚠️ Impossible de charger BLIP : {e}")
            self.blip_available = False

    def _load_clip(self):
        """Charge le modèle CLIP pour la similarité image-texte."""
        print(f"[CLIP] Chargement du modèle : {CLIP_MODEL_NAME}")
        try:
            import open_clip
            self.clip_model, _, self.clip_preprocess = open_clip.create_model_and_transforms(
                CLIP_MODEL_NAME, pretrained=CLIP_PRETRAINED
            )
            self.clip_tokenizer = open_clip.get_tokenizer(CLIP_MODEL_NAME)
            self.clip_model.eval()
            self.clip_available = True
            print("[CLIP] ✅ Modèle chargé avec succès")
        except Exception as e:
            print(f"[CLIP] ⚠️ Impossible de charger CLIP : {e}")
            self.clip_available = False

    def generate_caption(self, image_path: str) -> str:
        """
        Génère une description textuelle de l'image avec BLIP.

        Args:
            image_path: Chemin vers l'image

        Returns:
            Description textuelle (caption)
        """
        if not self.blip_available:
            return "description non disponible"

        import torch
        image = Image.open(image_path).convert("RGB")
        inputs = self.blip_processor(image, return_tensors="pt")

        with torch.no_grad():
            output = self.blip_model.generate(**inputs, max_new_tokens=50)

        caption = self.blip_processor.decode(output[0], skip_special_tokens=True)
        print(f"[BLIP] ✅ Caption : \"{caption}\"")
        return caption

    def compute_clip_scores(self, image_path: str, labels: list = None) -> dict:
        """
        Calcule la similarité entre l'image et chaque label candidat avec CLIP.

        Args:
            image_path: Chemin vers l'image
            labels: Liste de labels à comparer (utilise CANDIDATE_LABELS par défaut)

        Returns:
            dict {label: score} trié par score décroissant
        """
        if not self.clip_available:
            return {label: 0.0 for label in (labels or CANDIDATE_LABELS)}

        import torch
        labels = labels or CANDIDATE_LABELS

        image = Image.open(image_path).convert("RGB")
        image_tensor = self.clip_preprocess(image).unsqueeze(0)
        text_tokens  = self.clip_tokenizer(labels)

        with torch.no_grad():
            image_features = self.clip_model.encode_image(image_tensor)
            text_features  = self.clip_model.encode_text(text_tokens)

            # Normalisation
            image_features /= image_features.norm(dim=-1, keepdim=True)
            text_features  /= text_features.norm(dim=-1, keepdim=True)

            # Similarité cosinus → probabilités
            similarity = (100.0 * image_features @ text_features.T).softmax(dim=-1)
            scores     = similarity[0].tolist()

        scores_dict = {label: round(score, 4) for label, score in zip(labels, scores)}
        scores_dict = dict(sorted(scores_dict.items(), key=lambda x: x[1], reverse=True))

        top_label = list(scores_dict.keys())[0]
        top_score = list(scores_dict.values())[0]
        print(f"[CLIP] ✅ Top label : \"{top_label}\" | Score : {top_score:.2f}")

        return scores_dict

    def classify(self, image_path: str, labels: list = None) -> dict:
        """
        Pipeline complet : BLIP caption + CLIP scores.

        Args:
            image_path: Chemin vers l'image
            labels: Labels candidats optionnels

        Returns:
            dict avec caption, scores CLIP, top label et confiance globale
        """
        print(f"[BLIP+CLIP] Classification de : {image_path}")

        caption      = self.generate_caption(image_path)
        clip_scores  = self.compute_clip_scores(image_path, labels)

        top_label    = list(clip_scores.keys())[0]   if clip_scores else "inconnu"
        top_score    = list(clip_scores.values())[0] if clip_scores else 0.0

        # Score global = score CLIP du meilleur label
        model_confidence = round(top_score, 4)

        return {
            "blip_caption":      caption,
            "clip_scores":       clip_scores,
            "top_label":         top_label,
            "clip_top_score":    top_score,
            "model_confidence":  model_confidence,
        }

# TEST RAPIDE — python models/blip_clip_classifier.py <image>

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage : python models/blip_clip_classifier.py <chemin_image>")
        sys.exit(1)

    img_path   = sys.argv[1]
    classifier = BLIPCLIPClassifier()
    result     = classifier.classify(img_path)

    print("\n--- Résultats BLIP + CLIP ---")
    print(f"  Caption BLIP : {result['blip_caption']}")
    print(f"  Top label    : {result['top_label']} ({result['clip_top_score']:.2f})")
    print(f"  Tous les scores :")
    for label, score in result["clip_scores"].items():
        bar = "█" * int(score * 30)
        print(f"    {label:<15} {bar} {score:.4f}")
