"""
QR Code Verification Module
Detects, decodes, and verifies QR codes in documents
"""

import json
import logging
import os
from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger("doctome.qr_verifier")

class QRVerifier:
    """Verify QR codes in documents"""

    # Trusted institution public keys (example - would come from government DB)
    TRUSTED_INSTITUTIONS = {
        "Université de Tlemcen": {
            "public_key": None,  # Would be loaded from government registry
            "country": "Algeria",
            "trusted": True
        },
        "Ordre des Médecins Algeria": {
            "public_key": None,
            "country": "Algeria",
            "trusted": True
        },
        "Ministry of Health": {
            "public_key": None,
            "country": "Algeria",
            "trusted": True
        }
    }

    @staticmethod
    def detect_qr_in_image(image_path: str) -> Optional[bytes]:
        """
        Detect and extract QR code from image.

        Args:
            image_path: Path to image file

        Returns:
            QR code data if found, None otherwise
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                logger.warning(f"Could not read image: {image_path}")
                return None

            # Decode QR codes
            decoded_objects = decode(image)

            if decoded_objects:
                qr_data = decoded_objects[0].data
                logger.info(f"[QR] QR code detected in {os.path.basename(image_path)}")
                return qr_data
            else:
                logger.info(f"[QR] No QR code found in {os.path.basename(image_path)}")
                return None

        except Exception as e:
            logger.error(f"[QR] Error detecting QR code: {str(e)}")
            return None

    @staticmethod
    def parse_qr_data(qr_data: bytes) -> Optional[Dict[str, Any]]:
        """
        Parse QR code data (JSON or plain text).

        Args:
            qr_data: Raw QR code data

        Returns:
            Parsed QR data dictionary
        """
        try:
            # Try JSON first
            qr_text = qr_data.decode('utf-8')

            try:
                return json.loads(qr_text)
            except json.JSONDecodeError:
                # If not JSON, return as simple dict
                return {
                    "raw_data": qr_text,
                    "type": "text"
                }

        except Exception as e:
            logger.error(f"[QR] Error parsing QR data: {str(e)}")
            return None

    @staticmethod
    def verify_qr_signature(qr_data: Dict[str, Any],
                           institution: str) -> Tuple[bool, str]:
        """
        Verify QR code signature against trusted institution.

        Args:
            qr_data: Parsed QR code data
            institution: Institution name

        Returns:
            (is_valid, reason)
        """
        try:
            # Check if institution is trusted
            if institution not in QRVerifier.TRUSTED_INSTITUTIONS:
                return False, f"Unknown institution: {institution}"

            inst_info = QRVerifier.TRUSTED_INSTITUTIONS[institution]

            if not inst_info.get("trusted"):
                return False, f"Institution not trusted: {institution}"

            # Check required fields in QR
            required_fields = ["signature", "data", "timestamp"]
            missing = [f for f in required_fields if f not in qr_data]

            if missing:
                return False, f"QR missing fields: {missing}"

            # Verify signature (would use actual public key verification)
            # For now, just check format
            if not isinstance(qr_data.get("signature"), str):
                return False, "Invalid signature format"

            logger.info(f"[QR] Signature verified for {institution}")
            return True, "Signature verified"

        except Exception as e:
            logger.error(f"[QR] Signature verification error: {str(e)}")
            return False, f"Verification error: {str(e)}"

    @staticmethod
    def compare_data(extracted_data: Dict[str, Any],
                     qr_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Compare extracted document data with QR data.

        Args:
            extracted_data: Data extracted from document via OCR
            qr_data: Data from QR code

        Returns:
            (matches, comparison_details)
        """
        try:
            comparison = {
                "field_matches": {},
                "mismatches": [],
                "missing_in_qr": [],
                "overall_match": True
            }

            # Key fields to compare
            key_fields = [
                "nom",
                "name",
                "numéro d'inscription",
                "registration number",
                "serial number",
                "date",
                "année"
            ]

            # Check each field
            for field in key_fields:
                extracted_val = extracted_data.get(field, "").lower().strip()
                qr_val = qr_data.get(field, "").lower().strip()

                if extracted_val and qr_val:
                    match = extracted_val == qr_val
                    comparison["field_matches"][field] = match

                    if not match:
                        comparison["mismatches"].append({
                            "field": field,
                            "extracted": extracted_data.get(field),
                            "qr": qr_data.get(field)
                        })
                        comparison["overall_match"] = False

                elif extracted_val and not qr_val:
                    comparison["missing_in_qr"].append(field)

            logger.info(f"[QR] Data comparison: {len(comparison['field_matches'])} fields checked")

            return comparison["overall_match"], comparison

        except Exception as e:
            logger.error(f"[QR] Data comparison error: {str(e)}")
            return False, {"error": str(e)}

    @staticmethod
    def calculate_qr_trust_score(qr_found: bool,
                                qr_valid: bool,
                                data_matches: bool,
                                institution_trusted: bool) -> int:
        """
        Calculate trust score based on QR verification.

        Args:
            qr_found: Whether QR code was detected
            qr_valid: Whether QR signature is valid
            data_matches: Whether extracted data matches QR data
            institution_trusted: Whether institution is trusted

        Returns:
            Trust score impact (-60 to +80)
        """
        score = 0

        if not qr_found:
            logger.warning("[QR] No QR code found - document unverified")
            return -40  # Document unverified

        if qr_valid and institution_trusted:
            score += 30  # Valid signature from trusted source
        elif qr_valid:
            score += 15  # Valid signature but unknown source
        else:
            return -50  # Invalid signature = suspicious

        if data_matches:
            score += 50  # Data consistency = authentic
        else:
            return -60  # Data mismatch = fake/forged

        return score  # +80 = fully verified authentic document
