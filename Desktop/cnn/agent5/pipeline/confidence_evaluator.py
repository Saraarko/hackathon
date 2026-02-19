import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import CONFIDENCE_THRESHOLD

class ConfidenceEvaluator:

    def evaluate(self, fusion_score, annotation):
        
        if fusion_score >= CONFIDENCE_THRESHOLD:
            print(f"[EVAL] ✅ Score {fusion_score} ≥ {CONFIDENCE_THRESHOLD} → AUTO-LABEL")
            annotation["status"] = "AUTO_LABELED"
            return "AUTO_LABEL", annotation

        elif fusion_score >= 0.50:
            print(f"[EVAL] ⚠️ Score {fusion_score} → VALIDATION HUMAINE (priorité normale)")
            annotation["status"] = "PENDING_HUMAN"
            annotation["priority"] = "normal"
            return "HUMAN_VALIDATION", annotation

        else:
            print(f"[EVAL] 🔴 Score {fusion_score} → VALIDATION HUMAINE (priorité haute)")
            annotation["status"] = "PENDING_HUMAN"
            annotation["priority"] = "high"
            return "HUMAN_VALIDATION", annotation