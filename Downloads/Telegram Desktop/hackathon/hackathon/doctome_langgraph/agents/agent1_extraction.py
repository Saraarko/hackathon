"""
Agent 1: Document Extraction Agent
Extracts text from medical documents, structures with LLM, and assesses quality
"""

import logging
import pdfplumber
import json
import os
from typing import Dict, Any, List
from .state import PractitionerState
from datetime import datetime
from pathlib import Path
from .prompts import get_prompt
from dotenv import load_dotenv

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

# Try to import OCR libraries
PYTESSERACT_AVAILABLE = False
EASYOCR_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    pass

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    pass

logger = logging.getLogger("doctome.extraction")

# ─────────────────────────────────────────────
# GROQ LLM SETUP
# ─────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Create output folder (absolute path to doctome_langgraph/output)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output")
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)
    logger.info(f"Created output folder: {OUTPUT_FOLDER}")

# ─────────────────────────────────────────────
# LLM DATA STRUCTURING
# ─────────────────────────────────────────────

def structure_with_llm(extracted_text: str, entity_type: str) -> Dict[str, Any]:
    """
    Use Groq LLM to structure extracted text into JSON format.

    Args:
        extracted_text: Raw text from PDF
        entity_type: Type of document (medecin_individuel, clinique_hopital, laboratoire)

    Returns:
        Structured JSON dict matching agent2 schema
    """
    if not GROQ_AVAILABLE or not GROQ_API_KEY:
        logger.warning("[AGENT 1] Groq not available, returning raw extraction")
        return {"status": "raw_extraction", "text": extracted_text}

    try:
        client = Groq(api_key=GROQ_API_KEY)

        # Get prompt for this entity type
        prompt_template = get_prompt(entity_type)
        prompt = prompt_template.format(text=extracted_text)

        logger.info(f"[AGENT 1] Structuring {entity_type} document with Groq LLM...")

        message = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0] if len(response_text.split("```")) > 2 else response_text

        # Clean up response
        response_text = response_text.strip()

        # Extract JSON from response - find first { and last }
        if '{' in response_text and '}' in response_text:
            json_start = response_text.index('{')
            json_end = response_text.rindex('}') + 1
            response_text = response_text[json_start:json_end]

        logger.debug(f"[AGENT 1] Parsing JSON for {entity_type}: {response_text[:100]}...")
        structured_data = json.loads(response_text)
        logger.info(f"[AGENT 1] Successfully structured data for {entity_type}")
        return structured_data

    except json.JSONDecodeError as e:
        logger.error(f"[AGENT 1] JSON decode error for {entity_type}: {str(e)}")
        logger.error(f"[AGENT 1] Response was: {response_text[:200] if 'response_text' in locals() else 'N/A'}")
        return {"status": "parse_error", "entity_type": entity_type, "error": str(e)}
    except Exception as e:
        logger.error(f"[AGENT 1] LLM structuring error for {entity_type}: {str(e)}")
        return {"status": "llm_error", "entity_type": entity_type, "error": str(e)}


class DocumentExtractor:
    """Handles document extraction and analysis."""
    SYSTEM_PROMPTS = {
    "medecin_individuel": """You are an expert medical credential extractor for Algeria. 
    Extract the following from the OCR text into JSON:
    - nom (Full Name)
    - diplôme (Degree type)
    - université (Medical School)
    - année (Graduation Year)
    - numéro d'inscription (License/CNOM number)
    - qr_verified (boolean: set to true ONLY if you see evidence of a digital signature or official QR code)
    - nfc_data (Extract any biometric/chip reference if present)""",

    "clinique_hopital": """You are an expert healthcare facility auditor.
    Extract the following from the clinic's operating license or agreement:
    - nom_établissement (Legal Name)
    - adresse (Full physical address for Google Maps verification)
    - numéro_licence (Ministry of Health license/agrément number)
    - capacité (Bed count or patient capacity)
    - activité (Authorized medical domain/specialty)
    - qr_verified (boolean: set to true if the document contains a Ministry of Health QR seal)""",

    "laboratoire": """You are an expert laboratory accreditation specialist.
    Extract the following from the lab's certificate or ISO document:
    - nom_laboratoire (Legal Name)
    - adresse (Physical address for Google Maps verification)
    - numéro_licence (MOH Registration number)
    - accreditation (Specifically look for 'ISO 15189' or other standards)
    - equipements (Look for mentions of 'calibré', 'certifié', or equipment list)
    - directeur (Name of Technical Director/Responsable)
    - iso_qr_verified (boolean: set to true if the ISO certificate has an official QR seal)"""
    }

    # Entity type requirements
    ENTITY_REQUIREMENTS = {
        "medecin_individuel": {
            "name": "Médecin individuel",
            "required_documents": ["diploma", "id_card", "license"],
            "required_keywords": ["diplôme", "médecin", "spécialité", "inscription"],
            "required_fields": ["nom", "spécialité", "numéro d'inscription"],
            "keywords": ["médecin", "doctor", "practitioner", "diplôme", "diploma", "degree", "licence", "license", "specialty", "spécialité", "graduation"]
        },
        "clinique_hopital": {
            "name": "Clinique / Hôpital",
            "required_documents": ["license", "approval", "certification"],
            "required_keywords": ["licence", "hôpital", "clinique", "agrément"],
            "required_fields": ["nom légal", "adresse", "capacité lits", "agréments"],
            "keywords": ["hôpital", "hospital", "clinique", "clinic", "licence", "license", "healthcare facility", "agréments", "beds", "capacity"]
        },
        "laboratoire": {
            "name": "Laboratoire d'analyses",
            "required_documents": ["authorization", "accreditation", "approval"],
            "required_keywords": ["laboratoire", "analyse", "iso 15189", "accréditation"],
            "required_fields": ["directeur", "types d'analyses", "équipements"],
            "keywords": ["laboratoire", "laboratory", "analyse", "analysis", "accréditation", "accreditation", "iso 15189", "testing", "equipment"]
        }
    }

    @staticmethod
    def detect_entity_type(text: str) -> str:
        """
        Detect entity type from document text.

        Returns:
            Entity type: medecin_individuel, clinique_hopital, laboratoire, or UNKNOWN
        """
        text_lower = text.lower()

        for entity_type, config in DocumentExtractor.ENTITY_REQUIREMENTS.items():
            keyword_count = sum(1 for kw in config["keywords"] if kw in text_lower)
            if keyword_count >= 2:
                return entity_type

        return "UNKNOWN"

    @staticmethod
    def validate_required_fields(text: str, entity_type: str) -> List[str]:
        """
        Validate required fields based on entity type.

        Returns:
            List of missing fields
        """
        if entity_type not in DocumentExtractor.ENTITY_REQUIREMENTS:
            return []

        required_fields = DocumentExtractor.ENTITY_REQUIREMENTS[entity_type]["required_fields"]
        text_lower = text.lower()
        missing_fields = []

        for field in required_fields:
            if field.lower() not in text_lower:
                missing_fields.append(field)

        return missing_fields

    @staticmethod
    def extract_text_from_image(file_path: str) -> str:
        """
        Extract text from image file using OCR.

        Supports: PNG, JPG, JPEG, BMP, TIFF, GIF, WEBP

        Args:
            file_path: Path to image file

        Returns:
            Extracted text string
        """
        try:
            logger.info(f"Extracting text from image: {file_path}")

            # Try pytesseract first (faster if available)
            if PYTESSERACT_AVAILABLE:
                try:
                    image = Image.open(file_path)
                    text = pytesseract.image_to_string(image)
                    logger.info(f"[OCR-Tesseract] Extracted {len(text)} characters from {file_path}")
                    return text
                except Exception as e:
                    logger.warning(f"Pytesseract failed: {str(e)}, trying EasyOCR...")

            # Fallback to EasyOCR (English + French only, no Arabic detection)
            if EASYOCR_AVAILABLE:
                try:
                    import sys
                    from io import StringIO

                    # Suppress EasyOCR's verbose output
                    old_stderr = sys.stderr
                    sys.stderr = StringIO()

                    # Use English + French for multilingual support
                    reader = easyocr.Reader(['en', 'fr'], gpu=False, verbose=False)
                    result = reader.readtext(file_path)

                    sys.stderr = old_stderr

                    text = "\n".join([item[1] for item in result])
                    logger.info(f"[OCR-EasyOCR] Extracted {len(text)} characters from {file_path}")
                    return text
                except Exception as e:
                    sys.stderr = old_stderr
                    logger.warning(f"EasyOCR failed: {str(e)}")

            # If no OCR library available, return error message
            if not PYTESSERACT_AVAILABLE and not EASYOCR_AVAILABLE:
                logger.warning("No OCR library available. Install: pip install pytesseract pillow OR pip install easyocr")
                return "[OCR_NOT_AVAILABLE] No OCR library installed. Please install pytesseract or easyocr."

            raise Exception("All OCR methods failed")

        except Exception as e:
            logger.error(f"Failed to extract from image {file_path}: {str(e)}")
            raise

    @staticmethod
    def extract_text_from_pdf(file_path: str) -> str:
        """
        Extract text from PDF document using pdfplumber.

        Args:
            file_path: Path to PDF file

        Returns:
            Extracted text string
        """
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            text = ""

            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text += f"\n--- PAGE {page_num + 1} ---\n"
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text

            logger.info(f"Extracted {len(text)} characters from {file_path}")
            return text

        except Exception as e:
            logger.error(f"Failed to extract from PDF {file_path}: {str(e)}")
            raise

    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from any supported file type (PDF or Image).

        Supports: PDF, PNG, JPG, JPEG, BMP, TIFF, GIF, WEBP

        Args:
            file_path: Path to file

        Returns:
            Extracted text string
        """
        file_ext = Path(file_path).suffix.lower()

        if file_ext == ".pdf":
            return DocumentExtractor.extract_text_from_pdf(file_path)
        elif file_ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".gif", ".webp"]:
            return DocumentExtractor.extract_text_from_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")


    @staticmethod
    def assess_document_quality(text: str, file_path: str) -> float:
        """
        Assess quality of extracted document (0.0-1.0).

        Factors considered:
        - Text length (longer = better)
        - Word count (more words = better)
        - Medical keywords presence
        - Coherence

        Args:
            text: Extracted text
            file_path: Original file path (for context)

        Returns:
            Quality score 0.0-1.0
        """
        quality = 0.3  # Baseline

        # Text length (most important)
        text_length = len(text)
        if text_length > 2000:
            quality += 0.25
        elif text_length > 1000:
            quality += 0.15
        elif text_length > 500:
            quality += 0.08

        # Word count
        words = text.split()
        word_count = len(words)
        if word_count > 200:
            quality += 0.15
        elif word_count > 100:
            quality += 0.08

        # Medical keywords (strong indicator of legitimate document)
        medical_keywords = [
            "médecin", "doctor", "medical", "diplôme", "diploma",
            "licence", "license", "spécialité", "specialty",
            "université", "university", "école", "school",
            "année", "year", "étudiant", "student", "certificat", "certificate"
        ]
        keyword_count = sum(1 for kw in medical_keywords if kw in text.lower())
        if keyword_count >= 5:
            quality += 0.2
        elif keyword_count >= 3:
            quality += 0.1

        # Date presence (good indicator)
        import re
        if re.search(r"\d{4}", text):
            quality += 0.05

        return min(1.0, quality)

    @staticmethod
    def classify_document_type(text: str, hint: str = "") -> str:
        """
        Classify document type based on content.

        Args:
            text: Extracted text
            hint: Expected type as hint

        Returns:
            Document type (DIPLOMA, LICENSE, ID_CARD, INSURANCE, UNKNOWN)
        """
        text_lower = text.lower()

        # Diploma indicators
        diploma_keywords = ["diplôme", "diploma", "degree", "graduated", "graduation"]
        if any(kw in text_lower for kw in diploma_keywords):
            return "DIPLOMA"

        # License indicators
        license_keywords = ["licence", "license", "registration", "enregistrement"]
        if any(kw in text_lower for kw in license_keywords):
            return "LICENSE"

        # ID Card indicators
        id_keywords = ["carte nationale", "national id", "passport", "passeport"]
        if any(kw in text_lower for kw in id_keywords):
            return "ID_CARD"

        # Insurance indicators
        insurance_keywords = ["assurance", "insurance", "liability", "responsabilité"]
        if any(kw in text_lower for kw in insurance_keywords):
            return "INSURANCE"

        # Use hint if provided
        return hint or "UNKNOWN"

    @staticmethod
    def detect_anomalies(text: str, full_name: str, doc_type: str, entity_type: str = None) -> List[str]:
        """
        Detect anomalies in document text.

        Anomalies indicate potential issues:
        - Missing name
        - Suspicious patterns
        - Poor quality indicators
        - Missing key information
        - Entity-specific field validation

        Args:
            text: Extracted text
            full_name: Expected practitioner name
            doc_type: Document type
            entity_type: Entity type (medecin_individuel, clinique_hopital, laboratoire)

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Name check
        if full_name and full_name.lower() not in text.lower():
            # Check individual name parts
            name_parts = full_name.split()
            parts_found = sum(1 for part in name_parts if part.lower() in text.lower())
            if parts_found < len(name_parts) / 2:
                anomalies.append("name_not_found_in_document")

        # Text length (too short = suspicious)
        if len(text) < 200:
            anomalies.append("document_text_too_short")

        # Suspicious patterns (common in fake documents)
        suspicious_patterns = ["photocopy", "copy", "scan", "draft", "sample", "test"]
        for pattern in suspicious_patterns:
            if pattern in text.lower():
                anomalies.append(f"suspicious_pattern: {pattern}")

        # For diplomas/licenses, check for graduation date
        if doc_type in ["DIPLOMA", "LICENSE"]:
            import re
            if not re.search(r"\b\d{4}\b", text):
                anomalies.append("no_year_found")

        # Check for excessive special characters (OCR quality indicator)
        special_chars = sum(1 for c in text if not c.isalnum() and c not in " .,;:-'()!\n\t")
        if special_chars > len(text) * 0.3:
            anomalies.append("excessive_special_characters")

        # Text coherence (high ratio of unique words is good)
        words = text.lower().split()
        if words:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:  # Too much repetition
                anomalies.append("excessive_text_repetition")

        # Entity-specific field validation
        if entity_type and entity_type in DocumentExtractor.ENTITY_REQUIREMENTS:
            missing_fields = DocumentExtractor.validate_required_fields(text, entity_type)
            for field in missing_fields:
                anomalies.append(f"missing_field: {field}")

        return anomalies


def _normalize_dict_keys(d: dict) -> dict:
    """
    Normalize dict keys by removing accents and converting to ASCII.
    Recursively normalizes nested dicts.
    """
    if not isinstance(d, dict):
        return d

    def remove_accents(s: str) -> str:
        """Remove accents from a string."""
        import unicodedata
        if not isinstance(s, str):
            return s
        # Decompose accented characters and filter out combining marks
        nfd = unicodedata.normalize('NFD', s)
        return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')

    normalized = {}
    for key, value in d.items():
        # Normalize the key
        new_key = remove_accents(key) if isinstance(key, str) else key
        # Recursively normalize nested dicts
        new_value = _normalize_dict_keys(value) if isinstance(value, dict) else value
        normalized[new_key] = new_value

    return normalized


def _save_document_json(doc_json: dict, file_path: str) -> str:
    """
    Save document JSON to output folder.
    Normalizes keys to remove accents for compatibility with all systems.

    Args:
        doc_json: Document JSON dict
        file_path: Original PDF file path

    Returns:
        Path to saved JSON file
    """
    try:
        # Extract filename without extension
        base_name = os.path.splitext(os.path.basename(file_path))[0]

        # Create output filename
        output_file = os.path.join(OUTPUT_FOLDER, f"{base_name}_extraction.json")

        # Normalize keys to remove accents
        normalized_json = _normalize_dict_keys(doc_json)

        # Save JSON to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(normalized_json, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved JSON to: {output_file}")
        return output_file

    except Exception as e:
        logger.error(f"Failed to save JSON: {str(e)}")
        return None


def _document_to_json(
    file_path: str,
    doc_type: str,
    extracted_text: str,
    quality_score: float,
    anomalies: list,
    entity_type: str = None,
    error_message: str = None,
    structured_data: dict = None
) -> dict:
    """
    Convert single document extraction to JSON format.

    Returns:
        JSON dict with extraction results for one document
    """
    return {
        "status": "failed" if error_message else "success",
        "agent": "extraction",
        "document": {
            "file_path": file_path,
            "document_type": doc_type,
            "entity_type": entity_type or "UNKNOWN"
        },
        "timestamp": datetime.now().isoformat(),
        "results": {
            "extracted_text": extracted_text,
            "structured_data": structured_data or {},  # LLM-structured JSON matching agent2 schema
            "document_quality": round(quality_score, 2),
            "doc_anomalies": anomalies,
            "anomalies_count": len(anomalies)
        },
        "metadata": {
            "text_length": len(extracted_text),
            "quality_score": round(quality_score, 2),
            "entity_type": entity_type or "UNKNOWN"
        },
        "errors": [error_message] if error_message else []
    }


def _extraction_summary_to_json(
    quality_scores: list,
    anomalies_all: list,
    extracted_texts: list,
    documents_json: list,
    error_messages: list = None
) -> dict:
    """
    Convert extraction summary (all documents) to JSON format.

    Returns:
        JSON dict with summary of all extraction results
    """
    avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

    return {
        "status": "success" if not error_messages else "partial",
        "agent": "extraction",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_documents": len(extracted_texts),
            "average_quality": round(avg_quality, 2),
            "total_anomalies": len(anomalies_all),
            "quality_scores": [round(q, 2) for q in quality_scores]
        },
        "documents": documents_json,
        "metadata": {
            "total_text_length": sum(len(text) for text in extracted_texts),
            "documents_processed": len(extracted_texts)
        },
        "errors": error_messages or []
    }


async def main_test():
    """Test extraction agent directly."""
    from datetime import datetime

    # Get absolute paths for data files
    data_dir = os.path.join(BASE_DIR, "data")

    state = PractitionerState(
        practitioner_id="test_multi_format_001",
        full_name="Dr. Karim Belhadj",
        specialty="Médecine générale",
        country="Algeria",
        registration_number="D-2023-5678",
        documents=[
            # PDF files
            {"path": os.path.join(data_dir, "DOCTOR_DIPLOMA_FR.pdf"), "type": "diploma"},
            {"path": os.path.join(data_dir, "ALGERIAN_MEDICAL_LICENSE.pdf"), "type": "license"},
            # Image file with OCR (JPG)
            {"path": os.path.join(data_dir, "certificat_iso.jpg"), "type": "certificate"},
        ],
        submission_time=datetime.now().isoformat(),
        error_messages=[],
        processing_log=[]
    )

    result = await extraction_agent(state)
    return result


async def extraction_agent(state: PractitionerState) -> dict:
    """
    Agent 1: Extract and analyze documents.

    This is the first agent in the workflow.
    Responsible for:
    1. Extracting text from documents
    2. Assessing quality
    3. Classifying document types
    4. Detecting anomalies

    Input from state:
    - documents: list of file paths
    - full_name: expected name

    Output: JSON dict with extraction results

    JSON Output Format:
    {
        "status": "success",
        "agent": "extraction",
        "timestamp": "2026-05-02T14:32:05...",
        "results": {
            "extracted_text": "...",
            "document_quality": 0.87,
            "doc_anomalies": [...],
            "document_count": 3,
            "quality_scores": [0.85, 0.87, 0.89]
        },
        "metadata": {
            "total_text_length": 5234,
            "average_quality": 0.87,
            "documents_processed": 3
        },
        "errors": []
    }

    Also updates state for LangGraph workflow.

    Args:
        state: Current state from workflow

    Returns:
        JSON dict with extraction results + updated state
    """
    logger.info(f"[AGENT 1] Starting extraction for {state.get('practitioner_id', 'unknown')}")

    try:
        documents = state.get("documents", [])
        full_name = state.get("full_name", "")

        if not documents:
            raise ValueError("No documents provided")

        logger.info(f"[AGENT 1] Processing {len(documents)} documents")

        # Extract texts from all documents
        extracted_texts = []
        quality_scores = []
        anomalies_all = []
        doc_types = []
        entity_types = []
        documents_json = []
        error_messages = []

        for idx, doc in enumerate(documents, 1):
            try:
                file_path = doc.get("path")
                doc_type_hint = doc.get("type", "UNKNOWN")

                logger.info(f"[AGENT 1] Processing document {idx}/{len(documents)}: {file_path}")

                # Extract text (supports PDF and images)
                text = DocumentExtractor.extract_text(file_path)
                extracted_texts.append(text)

                # Classify document type
                classified_type = DocumentExtractor.classify_document_type(text, doc_type_hint)
                doc_types.append(classified_type)
                logger.info(f"[AGENT 1] Document classified as: {classified_type}")

                # Detect entity type
                entity_type = DocumentExtractor.detect_entity_type(text)
                entity_types.append(entity_type)
                logger.info(f"[AGENT 1] Entity type detected: {entity_type}")

                # Structure data with LLM (Groq)
                structured_data = structure_with_llm(text, entity_type)
                logger.info(f"[AGENT 1] LLM structured data for {entity_type}")

                # Assess quality
                quality = DocumentExtractor.assess_document_quality(text, file_path)
                quality_scores.append(quality)
                logger.info(f"[AGENT 1] Quality score: {quality:.2f}")

                # Detect anomalies (including entity-specific validation)
                anomalies = DocumentExtractor.detect_anomalies(text, full_name, classified_type, entity_type)
                if anomalies:
                    anomalies_all.extend(anomalies)
                    logger.warning(f"[AGENT 1] Anomalies detected: {anomalies}")

                # Create JSON for this document
                doc_json = _document_to_json(
                    file_path,
                    classified_type,
                    text,
                    quality,
                    anomalies,
                    entity_type,
                    structured_data=structured_data
                )
                documents_json.append(doc_json)

                # Save JSON to output folder
                output_file = _save_document_json(doc_json, file_path)
                logger.info(f"[AGENT 1] JSON created and saved for document {idx}: {output_file}")

            except Exception as e:
                error_msg = f"Failed to process document {idx}: {str(e)}"
                logger.error(f"[AGENT 1] {error_msg}")
                error_messages.append(error_msg)

                # Create error JSON for this document
                doc_json = _document_to_json(
                    documents[idx-1].get("path", f"document_{idx}"),
                    documents[idx-1].get("type", "UNKNOWN"),
                    "",
                    0.0,
                    ["extraction_failed"],
                    entity_type="UNKNOWN",
                    error_message=str(e)
                )
                documents_json.append(doc_json)
                entity_types.append("UNKNOWN")

        # Calculate aggregated metrics
        combined_text = "\n".join(extracted_texts)
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0

        logger.info(
            f"[AGENT 1] Extraction complete: "
            f"quality={avg_quality:.2f}, "
            f"anomalies={len(anomalies_all)}, "
            f"documents={len(extracted_texts)}"
        )

        # Generate JSON output - Summary of all documents
        json_summary = _extraction_summary_to_json(
            quality_scores,
            anomalies_all,
            extracted_texts,
            documents_json,
            error_messages
        )

        # Save summary JSON to output folder
        try:
            summary_file = os.path.join(OUTPUT_FOLDER, "extraction_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(json_summary, f, indent=2, ensure_ascii=False)
            logger.info(f"[AGENT 1] Summary JSON saved to: {summary_file}")
        except Exception as e:
            logger.error(f"[AGENT 1] Failed to save summary JSON: {str(e)}")

        # Update state for LangGraph workflow
        state["extracted_text"] = combined_text
        state["document_quality"] = round(avg_quality, 2)
        state["doc_anomalies"] = list(set(anomalies_all))
        state["document_count"] = len(extracted_texts)
        state["extraction_json_output"] = json_summary
        state["extraction_documents_json"] = documents_json  # Individual JSONs for each document

        if "processing_log" not in state or state["processing_log"] is None:
            state["processing_log"] = []
        state["processing_log"].append(
            f"[{datetime.now().isoformat()}] Agent 1 (Extraction) completed: "
            f"{len(extracted_texts)} docs, quality={avg_quality:.2f}"
        )

        logger.info(f"[AGENT 1] JSON output generated ({len(documents_json)} individual documents)")
        return state

    except Exception as e:
        logger.error(f"[AGENT 1] Critical error: {str(e)}")

        # Create error JSON
        json_summary = {
            "status": "failed",
            "agent": "extraction",
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_documents": 0,
                "average_quality": 0.0,
                "total_anomalies": 0,
                "quality_scores": []
            },
            "documents": [],
            "metadata": {
                "total_text_length": 0,
                "documents_processed": 0
            },
            "errors": [str(e)]
        }

        # Update state with safe defaults
        state["extracted_text"] = ""
        state["document_quality"] = 0.0
        state["doc_anomalies"] = ["extraction_failed"]
        state["document_count"] = 0
        state["extraction_json_output"] = json_summary
        state["extraction_documents_json"] = []

        if "error_messages" not in state or state["error_messages"] is None:
            state["error_messages"] = []
        state["error_messages"].append(f"Agent 1 failed: {str(e)}")

        return state


async def test_image_only():
    """Test extraction on image file only."""
    from datetime import datetime

    # Get absolute paths for data files
    data_dir = os.path.join(BASE_DIR, "data")

    state = PractitionerState(
        practitioner_id="test_image_only",
        full_name="Dr. Test",
        specialty="Medicine",
        country="Algeria",
        registration_number="IMG-2024-001",
        documents=[
            # Only image file
            {"path": os.path.join(data_dir, "certificat_iso.jpg"), "type": "certificate"},
        ],
        submission_time=datetime.now().isoformat(),
        error_messages=[],
        processing_log=[]
    )

    result = await extraction_agent(state)
    return result


if __name__ == "__main__":
    """Run Agent 1 directly."""
    import asyncio
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='[%(name)s] %(levelname)s: %(message)s'
    )

    print("\n" + "="*70)
    print("AGENT 1: IMAGE OCR TEST")
    print("Testing: certificat_iso.jpg")
    print("="*70 + "\n")

    try:
        # Run image-only test
        result = asyncio.run(test_image_only())

        print("\n" + "="*70)
        print("IMAGE EXTRACTION COMPLETE")
        print("="*70)
        print(f"\nStatus: {result.get('extraction_json_output', {}).get('status')}")
        print(f"Documents: {result.get('document_count')}")
        print(f"Quality: {result.get('document_quality')}")
        print(f"Anomalies: {result.get('doc_anomalies')}")

        print("\n[INFO] JSON files saved to: output/")
        print(f"  - certificat_iso_extraction.json")
        print(f"  - extraction_summary.json")

        # Show extracted text
        if result.get('extracted_text'):
            print("\n" + "="*70)
            print("EXTRACTED TEXT (first 500 chars):")
            print("="*70)
            extracted = result.get('extracted_text', '')
            if len(extracted) > 500:
                print("[Text contains multilingual content - see JSON for full text]")
            else:
                try:
                    print(extracted)
                except UnicodeEncodeError:
                    print("[Text contains non-ASCII characters - see JSON for full text]")

        print("\n" + "="*70 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Agent 1 failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
