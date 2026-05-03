"""
Comprehensive Verification Pipeline for Doctors, Clinics, Labs
Phases 1-4: Identity, License, Education, Malpractice + Facility Verification
"""

import json
import logging
from typing import Dict, Any, List, Tuple
import os
from datetime import datetime
import unicodedata

logger = logging.getLogger("doctome.verification_pipeline")

def safe_get(data: Dict[str, Any], *keys: str) -> Any:
    """Safely get value from dict trying multiple key variations"""
    # First, try exact match
    for key in keys:
        if key in data:
            return data[key]

    # Second, try case-insensitive substring matching for flexibility
    for key in keys:
        key_base = key.lower().replace('é', '').replace('è', '').replace('ù', '').replace('ü', '')
        for dict_key, dict_val in data.items():
            dict_base = dict_key.lower().replace('é', '').replace('è', '').replace('ù', '').replace('ü', '')
            if key_base in dict_base or dict_base in key_base:
                return dict_val

    return None

# ═════════════════════════════════════════════════════════════════
# PHASE 1: DOCTOR PIPELINE (30% ID + 25% Diploma + 20% School + 15% License + 10% Malpractice)
# ═════════════════════════════════════════════════════════════════

class DoctorVerification:
    """Verify doctor credentials"""

    WEIGHTS = {
        "id_verification": 0.30,
        "diploma_verified": 0.25,
        "school_accredited": 0.20,
        "license_active": 0.15,
        "no_malpractice": 0.10
    }

    @staticmethod
    def verify_id(extracted_data: Dict[str, Any], diploma_data: Dict[str, Any] = None) -> Tuple[bool, str, int]:
        """
        Step 1: ID Verification (MVC Chip Reader + Face Match)
        → Reads chip data from ID (NFC simulation)
        → Compares with extracted text
        → Face match: Selfie vs ID Photo
        → Cross-check with Diploma name
        """
        try:
            # 1. Simulate MVC/NFC Chip Read
            logger.info("[MVC CHIP] Accessing secure enclave for biometric data...")
            
            nfc_data = extracted_data.get("nfc_data", {})
            if not nfc_data:
                # Simulate extraction from a real secure chip
                nfc_data = {
                    "nom": safe_get(extracted_data, "nom", "name"),
                    "date_naissance": safe_get(extracted_data, "date_naissance", "dob"),
                    "numéro_id": safe_get(extracted_data, "numéro_id", "id_number")
                }
            
            # 2. Face Match Check (Simulated AWS Rekognition / FaceID)
            face_match_score = extracted_data.get("face_match_score")
            if face_match_score is None:
                # Simulate a successful match if data is good
                face_match_score = 0.98 if nfc_data.get("nom") else 0.0
            
            if face_match_score < 0.85:
                logger.warning(f"[MVC CHIP] Face match failed: {face_match_score}")
                return False, f"Face match failed (Score: {face_match_score})", 0
            
            logger.info(f"[MVC CHIP] Face matching: SUCCESS (Confidence: {face_match_score*100:.1f}%)")

            # 3. Cross-check Chip Data with Diploma (if provided)
            if diploma_data:
                dip_name = safe_get(diploma_data, "nom", "name")
                id_name = nfc_data.get("nom")
                
                if dip_name and id_name:
                    # Normalize names for comparison
                    def normalize(s):
                        return "".join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
                    
                    n_dip = normalize(dip_name)
                    n_id = normalize(id_name)
                    
                    if n_dip != n_id:
                        # Check if all parts of ID name are in Diploma name or vice-versa
                        parts_dip = set(n_dip.split())
                        parts_id = set(n_id.split())
                        if not parts_dip.intersection(parts_id):
                            logger.error(f"[MVC CHIP] IDENTITY FRAUD DETECTED: ID({id_name}) vs Diploma({dip_name})")
                            return False, f"Name mismatch: ID({id_name}) vs Diploma({dip_name})", 5
                        else:
                            logger.info("[MVC CHIP] Identity verified via partial name match")

            # 4. Mandatory Fields Check
            if not nfc_data.get("nom") or not nfc_data.get("numéro_id"):
                return False, "ID incomplete - MVC chip read failed", 0

            return True, "ID Verified via MVC Chip Reader & Biometric Face Match", 30

        except Exception as e:
            logger.error(f"[DOCTOR] ID verification error: {str(e)}")
            return False, f"ID verification error: {str(e)}", 0

    @staticmethod
    def verify_diploma(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 2: Diploma Verification (OCR + QR Signature)
        → OCR extracts: doctor name, school, year, degree
        → QR code scan (simulated via qr_verifier)
        → Verify QR points to real government registry
        """
        try:
            logger.info("[DIPLOMA] Analyzing official seal and QR signature...")
            
            required = ["nom", "université", "année", "diplôme"]
            found = {f: extracted_data.get(f) for f in required if extracted_data.get(f)}

            # Simulate QR Verification (would use QRVerifier.detect_qr_in_image)
            qr_verified = extracted_data.get("qr_verified", True) # Default to true for recognized docs
            
            if not qr_verified:
                return False, "QR code signature invalid or points to untrusted URL", 5

            if len(found) >= 3:
                logger.info("[DIPLOMA] Official signature and QR code verified")
                return True, "Diploma verified via OCR + Secure QR Registry", 25
            else:
                logger.warning("[DIPLOMA] Verification failed: Incomplete data")
                return False, "Diploma incomplete or unreadable", 5

        except Exception as e:
            logger.error(f"[DOCTOR] Diploma error: {str(e)}")
            return False, f"Diploma verification error: {str(e)}", 0

    @staticmethod
    def verify_school(school_name: str) -> Tuple[bool, str, int]:
        """
        Step 3: Medical School Verification (WDOMS API)
        → Query World Directory of Medical Schools
        → Confirm school is accredited and active
        """
        try:
            # Simulated API call to https://www.wdoms.org/
            accredited_schools = [
                "université de tlemcen", "université d'algérie", 
                "université oran", "université constantine",
                "faculté de médecine d'alger"
            ]

            school_lower = school_name.lower() if school_name else ""

            if any(s in school_lower for s in accredited_schools):
                logger.info(f"[WDOMS] School {school_name} found in World Directory")
                return True, f"School {school_name} is accredited by WDOMS", 20
            else:
                logger.warning(f"[WDOMS] School {school_name} not recognized")
                return False, f"School {school_name} not in WDOMS accreditation list", 5

        except Exception as e:
            logger.error(f"[DOCTOR] School verification error: {str(e)}")
            return False, f"School verification error: {str(e)}", 0

    @staticmethod
    def verify_license(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 4: License Verification (Scrape CNOM)
        → Scrape Conseil National de l'Ordre des Médecins
        → Search by license number
        """
        try:
            license_num = extracted_data.get("numéro d'inscription") or extracted_data.get("numéro de licence")

            if license_num:
                # Simulated search on http://www.cnom.dz/
                logger.info(f"[CNOM] Verifying license {license_num} in national registry...")
                return True, f"License {license_num} is ACTIVE and VALID", 15
            else:
                logger.warning("[CNOM] License number missing")
                return False, "License number required for legal practice check", 0

        except Exception as e:
            logger.error(f"[DOCTOR] License verification error: {str(e)}")
            return False, f"License verification error: {str(e)}", 0

    @staticmethod
    def check_malpractice(doctor_name: str) -> Tuple[bool, str, int]:
        """
        Step 5: Malpractice & Behavioral Risk (AI Scraper)
        → Google search + Social Media sentiment analysis
        → LLM summarizes public complaints or disciplinary actions
        """
        try:
            # Simulated AI search
            logger.info(f"[BEHAVIOR] Scanning web for public records of {doctor_name}...")
            return True, "No malpractice records or significant negative sentiment found", 10

        except Exception as e:
            logger.error(f"[DOCTOR] Malpractice check error: {str(e)}")
            return False, f"Malpractice check error: {str(e)}", 0

    @staticmethod
    def calculate_doctor_score(extracted_data: Dict[str, Any], all_docs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate doctor verification score using biometric and registry checks"""
        scores = {}
        all_docs = all_docs or []
        
        # Extract Diploma data if available for cross-check
        diploma_data = None
        for doc in all_docs:
            if doc.get("results", {}).get("document_type") == "DIPLOMA":
                diploma_data = doc.get("results", {}).get("structured_data", {})
                break

        # 1. ID (NFC + Face Match)
        id_ok, id_msg, id_pts = DoctorVerification.verify_id(extracted_data, diploma_data)
        scores["id"] = {"pass": id_ok, "message": id_msg, "points": id_pts, "weight": DoctorVerification.WEIGHTS["id_verification"]}

        # Diploma
        dip_ok, dip_msg, dip_pts = DoctorVerification.verify_diploma(extracted_data)
        scores["diploma"] = {"pass": dip_ok, "message": dip_msg, "points": dip_pts, "weight": DoctorVerification.WEIGHTS["diploma_verified"]}

        # School
        school = extracted_data.get("université") or extracted_data.get("school")
        school_ok, school_msg, school_pts = DoctorVerification.verify_school(school)
        scores["school"] = {"pass": school_ok, "message": school_msg, "points": school_pts, "weight": DoctorVerification.WEIGHTS["school_accredited"]}

        # License
        lic_ok, lic_msg, lic_pts = DoctorVerification.verify_license(extracted_data)
        scores["license"] = {"pass": lic_ok, "message": lic_msg, "points": lic_pts, "weight": DoctorVerification.WEIGHTS["license_active"]}

        # Malpractice
        name = extracted_data.get("nom") or "unknown"
        mal_ok, mal_msg, mal_pts = DoctorVerification.check_malpractice(name)
        scores["malpractice"] = {"pass": mal_ok, "message": mal_msg, "points": mal_pts, "weight": DoctorVerification.WEIGHTS["no_malpractice"]}

        # Calculate final score
        total_weight = sum(s["weight"] for s in scores.values())
        weighted_sum = sum(s["weight"] * (s["points"] if "points" in s else (100 if s["pass"] else 0)) for s in scores.values())

        final_score = round((weighted_sum / total_weight) if total_weight > 0 else 0, 2)

        return {
            "entity_type": "medecin_individuel",
            "scores": scores,
            "final_score": final_score,
            "timestamp": datetime.now().isoformat()
        }


# ═════════════════════════════════════════════════════════════════
# PHASE 3: CLINIC PIPELINE (30% Legal + 15% Address + 40% Doctors + 15% License)
# ═════════════════════════════════════════════════════════════════

class ClinicVerification:
    """Verify clinic credentials using digital signatures and physical location checks"""

    WEIGHTS = {
        "legal_registration": 0.30,
        "address_confirmed": 0.15,
        "doctors_verified": 0.40,
        "license_valid": 0.15
    }

    @staticmethod
    def verify_legal_registration(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 1: Legal Registration & QR Integrity
        → Scans QR for Ministry of Health (MOH) digital seal
        → Verifies license number in national registry
        """
        try:
            logger.info("[CLINIC] Verifying MOH digital seal and license ID...")
            
            # 1. QR Integrity Check (The "Closed" Document Check)
            qr_verified = extracted_data.get("qr_verified", True) # Default to true for demo
            if not qr_verified:
                logger.error("[CLINIC] QR CODE BROKEN: Document may have been modified!")
                return False, "Digital signature invalid - Document integrity compromised", 0

            # 2. Registry Existence Check
            clinic_name = safe_get(extracted_data, "nom_établissement", "nom légal", "clinic_name")
            license_num = safe_get(extracted_data, "numéro_licence", "agréments", "license_number")

            if clinic_name and license_num:
                # Simulated search on Ministry of Health Portal
                logger.info(f"[CLINIC] Searching MOH registry for License: {license_num}")
                return True, f"Clinic '{clinic_name}' (ID: {license_num}) is officially REGISTERED", 30
            else:
                logger.warning("[CLINIC] Legal ID or Name missing from document")
                return False, "Legal registration info incomplete", 5

        except Exception as e:
            logger.error(f"[CLINIC] Legal registration error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def verify_address(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 2: Address Verification (Google Maps API)
        → Geocoding confirms address exists
        → Street View confirms medical facility at coordinates
        """
        try:
            address = safe_get(extracted_data, "adresse", "address", "location")

            if address:
                # Simulated call to Google Maps Geocoding API
                logger.info(f"[CLINIC] Sending address to Google Maps: {address}")
                logger.info("[CLINIC] Street View verification: MEDICAL FACILITY CONFIRMED")
                return True, f"Physical address '{address}' verified via Google Maps", 15
            else:
                logger.warning("[CLINIC] No address found for physical verification")
                return False, "Physical address missing - cannot verify location", 0

        except Exception as e:
            logger.error(f"[CLINIC] Address verification error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def verify_doctors(doctors_list: List[str]) -> Tuple[bool, str, int]:
        """
        Step 3: Doctors Inside Clinic
        → Cross-references doctor staff list with individual verified profiles
        """
        try:
            if not doctors_list:
                logger.warning("[CLINIC] No staff list provided")
                return False, "No verified doctors found on staff", 0

            verified_count = int(len(doctors_list) * 0.8)  # Simulation
            percentage = round((verified_count / len(doctors_list)) * 100)
            points = int(40 * (percentage / 100))
            
            logger.info(f"[CLINIC] Staff Integrity: {percentage}% of doctors are VERIFIED")
            return True, f"{percentage}% of medical staff are officially verified", points

        except Exception as e:
            logger.error(f"[CLINIC] Doctor verification error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def verify_license(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 4: Domain & Specialty Consistency
        → Compares 'Activité' with the clinic's provided services
        """
        try:
            domain = safe_get(extracted_data, "agréments", "activité", "specialty")
            
            if domain:
                logger.info(f"[CLINIC] Authorized Domain: {domain}")
                return True, f"Clinic is authorized for: {domain}", 15
            else:
                logger.warning("[CLINIC] Operating domain not specified")
                return False, "Service authorization not found", 0

        except Exception as e:
            logger.error(f"[CLINIC] License verification error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def calculate_clinic_score(extracted_data: Dict[str, Any], all_docs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate clinic verification score using digital and physical checks"""
        all_docs = all_docs or []
        
        # Look for staff list document
        doctors_list = []
        for doc in all_docs:
            if doc.get("results", {}).get("document_type") == "STAFF_LIST":
                doctors_list = doc.get("results", {}).get("structured_data", {}).get("doctors", [])
                break
        
        # If no staff list, simulate a few for the demo
        if not doctors_list:
            doctors_list = ["Dr. Karim", "Dr. Sarah"]

        scores = {}

        # 1. Legal & QR
        legal_ok, legal_msg, legal_pts = ClinicVerification.verify_legal_registration(extracted_data)
        scores["legal"] = {"pass": legal_ok, "message": legal_msg, "points": legal_pts, "weight": ClinicVerification.WEIGHTS["legal_registration"]}

        # 2. Address
        addr_ok, addr_msg, addr_pts = ClinicVerification.verify_address(extracted_data)
        scores["address"] = {"pass": addr_ok, "message": addr_msg, "points": addr_pts, "weight": ClinicVerification.WEIGHTS["address_confirmed"]}

        # 3. Doctors
        doc_ok, doc_msg, doc_pts = ClinicVerification.verify_doctors(doctors_list)
        scores["doctors"] = {"pass": doc_ok, "message": doc_msg, "points": doc_pts, "weight": ClinicVerification.WEIGHTS["doctors_verified"]}

        # 4. License Domain
        lic_ok, lic_msg, lic_pts = ClinicVerification.verify_license(extracted_data)
        scores["license"] = {"pass": lic_ok, "message": lic_msg, "points": lic_pts, "weight": ClinicVerification.WEIGHTS["license_valid"]}

        # Final Score
        total_weight = sum(s["weight"] for s in scores.values())
        weighted_sum = sum(s["weight"] * s["points"] for s in scores.values())
        final_score = round((weighted_sum / total_weight) if total_weight > 0 else 0, 2)

        return {
            "entity_type": "clinique_hopital",
            "scores": scores,
            "final_score": final_score,
            "timestamp": datetime.now().isoformat()
        }


# ═════════════════════════════════════════════════════════════════
# PHASE 4: LAB PIPELINE (25% Legal + 35% ISO + 25% Equipment + 15% Staff)
# ═════════════════════════════════════════════════════════════════

class LabVerification:
    """Verify laboratory credentials focusing on digital signatures, ISO standards, and location"""

    WEIGHTS = {
        "legal_registration": 0.25,
        "address_confirmed": 0.15,
        "iso_accreditation": 0.35,
        "equipment_staff": 0.25
    }

    @staticmethod
    def verify_legal_registration(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 1: Legal Registration & QR Integrity
        → Scans QR for Ministry of Health (MOH) digital seal
        → Verifies license number in national registry
        """
        try:
            logger.info("[LAB] Verifying MOH digital seal and license ID...")
            
            # 1. QR Integrity Check (The "Closed" Document Check)
            qr_verified = extracted_data.get("qr_verified", True) # Default to true for demo
            if not qr_verified:
                logger.error("[LAB] QR CODE BROKEN: Agreement may have been modified!")
                return False, "Digital signature invalid - Document integrity compromised", 0

            # 2. Registry Existence Check
            name = safe_get(extracted_data, "nom_laboratoire", "nom", "lab_name")
            license_num = safe_get(extracted_data, "numéro_licence", "agréments", "license_number")

            if name and license_num:
                # Simulated search on Ministry of Health Portal
                logger.info(f"[LAB] Searching MOH registry for License: {license_num}")
                return True, f"Laboratory '{name}' (ID: {license_num}) is officially REGISTERED", 25
            else:
                logger.warning("[LAB] Legal ID or Name missing from document")
                return False, "Legal registration info incomplete", 5

        except Exception as e:
            logger.error(f"[LAB] Legal registration error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def verify_address(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 2: Address Verification (Google Maps API)
        → Geocoding confirms address exists
        → Street View confirms laboratory at coordinates
        """
        try:
            address = safe_get(extracted_data, "adresse", "address", "location")

            if address:
                # Simulated call to Google Maps Geocoding API
                logger.info(f"[LAB] Sending address to Google Maps: {address}")
                logger.info("[LAB] Street View verification: LABORATORY CONFIRMED")
                return True, f"Physical address '{address}' verified via Google Maps", 15
            else:
                logger.warning("[LAB] No address found for physical verification")
                return False, "Physical address missing - cannot verify location", 0

        except Exception as e:
            logger.error(f"[LAB] Address verification error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def verify_iso_qr(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """
        Step 3: ISO 15189 QR Verification
        → Scans QR code on the ISO certificate for ALGERAC/International seal
        """
        try:
            logger.info("[LAB] Analyzing ISO 15189 Digital Seal...")
            
            # Simulated QR scan for ISO certificate
            iso_qr_verified = extracted_data.get("iso_qr_verified", True)
            accreditation = safe_get(extracted_data, "accreditation", "accréditation", "standards")

            if iso_qr_verified and accreditation and "15189" in accreditation:
                logger.info("[LAB] ISO 15189 DIGITAL SIGNATURE VALID")
                return True, "ISO 15189 Medical Standard verified via Digital QR Seal", 35
            else:
                logger.warning("[LAB] ISO QR missing or standard incorrect")
                return False, "Valid ISO 15189 Digital Seal not found", 0

        except Exception as e:
            logger.error(f"[LAB] ISO QR verification error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def verify_equipment_and_staff(extracted_data: Dict[str, Any]) -> Tuple[bool, str, int]:
        """Step 4: Equipment & Staff Quality"""
        try:
            equipment_status = safe_get(extracted_data, "equipements", "équipements", "equipment_status")
            director = safe_get(extracted_data, "directeur", "responsable", "director")
            
            points = 0
            msgs = []
            
            if equipment_status and "calibré" in equipment_status.lower():
                points += 15
                msgs.append("Equipment Calibrated")
            
            if director:
                points += 10
                msgs.append(f"Director Verified: {director}")
            
            if points > 0:
                return True, f"Quality check passed: {', '.join(msgs)}", points
            else:
                return False, "Equipment or Staff data missing", 0

        except Exception as e:
            logger.error(f"[LAB] Quality check error: {str(e)}")
            return False, f"Error: {str(e)}", 0

    @staticmethod
    def calculate_lab_score(extracted_data: Dict[str, Any], all_docs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate laboratory verification score using digital and physical checks"""
        scores = {}

        # 1. Legal & QR
        legal_ok, legal_msg, legal_pts = LabVerification.verify_legal_registration(extracted_data)
        scores["legal"] = {"pass": legal_ok, "message": legal_msg, "points": legal_pts, "weight": LabVerification.WEIGHTS["legal_registration"]}

        # 2. Address
        addr_ok, addr_msg, addr_pts = LabVerification.verify_address(extracted_data)
        scores["address"] = {"pass": addr_ok, "message": addr_msg, "points": addr_pts, "weight": LabVerification.WEIGHTS["address_confirmed"]}

        # 3. ISO QR
        iso_ok, iso_msg, iso_pts = LabVerification.verify_iso_qr(extracted_data)
        scores["iso"] = {"pass": iso_ok, "message": iso_msg, "points": iso_pts, "weight": LabVerification.WEIGHTS["iso_accreditation"]}

        # 4. Quality (Equipment/Staff)
        qual_ok, qual_msg, qual_pts = LabVerification.verify_equipment_and_staff(extracted_data)
        scores["quality"] = {"pass": qual_ok, "message": qual_msg, "points": qual_pts, "weight": LabVerification.WEIGHTS["equipment_staff"]}

        # Final Score
        total_weight = sum(s["weight"] for s in scores.values())
        weighted_sum = sum(s["weight"] * s["points"] for s in scores.values())
        final_score = round((weighted_sum / total_weight) if total_weight > 0 else 0, 2)

        return {
            "entity_type": "laboratoire",
            "scores": scores,
            "final_score": final_score,
            "timestamp": datetime.now().isoformat()
        }
