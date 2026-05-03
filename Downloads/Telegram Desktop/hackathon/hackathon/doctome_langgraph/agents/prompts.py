"""
Prompt Library for Document Structuring
Each entity type has a prompt that instructs the LLM to extract and structure data
matching the JSON schema in agent2's library
"""

PROMPTS = {
    "medecin_individuel": """You are a medical document parser. Extract and structure doctor credential information from the text below.

Return ONLY valid JSON matching this exact structure:
{{
  "nom": "<full name>",
  "spécialité": "<medical specialty>",
  "numéro d'inscription": "<registration number>",
  "date de validité": "<validity date in YYYY-MM-DD or DD/MM/YYYY format>",
  "titre": "<title/position if any>",
  "lieu_exercice": "<place of practice if any>"
}}

If a field is not found, use "NOT_FOUND". Extract ONLY from the provided text.

Document Text:
{text}""",

    "clinique_hopital": """You are a medical facility document parser. Extract and structure hospital/clinic information from the text below.

Return ONLY valid JSON matching this exact structure:
{{
  "nom légal": "<legal facility name>",
  "adresse": "<complete address>",
  "capacité lits": "<number of beds>",
  "agréments": "<accreditations/licenses>",
  "numéro de licence": "<license number>",
  "directeur": "<director/administrator name if any>",
  "type_établissement": "<hospital/clinic/center>"
}}

If a field is not found, use "NOT_FOUND". Extract ONLY from the provided text.

Document Text:
{text}""",

    "laboratoire": """You are a laboratory accreditation document parser. Extract and structure laboratory certification data.

CRITICAL: Extract ALL numeric IDs, dates, and official information. Look for:
- Lab name (any variation: "Laboratoire", "Laboratory", "Lab")
- Director/Head name (look for "Dr", "Directeur", "Director", "Head")
- ISO standard (ISO 9001, ISO 15189, CAP, etc.)
- Certificate/Registration number (alphanumeric codes like "12345678")
- Validity dates (start and end dates)
- Location/Address
- Types of analysis offered

Return ONLY valid JSON matching this exact structure:
{{
  "nom_laboratoire": "<full laboratory name>",
  "directeur": "<laboratory director full name>",
  "adresse": "<complete address>",
  "types_analyses": "<types of medical analysis>",
  "equipements": "<equipment and instruments used>",
  "accréditation": "<accreditation standard name (e.g. ISO 9001, ISO 15189)>",
  "numéro_accréditation": "<certificate or registration number>",
  "date_validité_début": "<accreditation start date YYYY-MM-DD>",
  "date_validité_fin": "<accreditation end date YYYY-MM-DD>",
  "certifications": "<other certifications if any>",
  "organisme_certification": "<certifying body/organization>"
}}

EXTRACTION RULES:
1. Look for certificate numbers: Usually after "N°" or "N° de" or "Registration"
2. Look for dates: Usually near "Valid", "Valable", "Expiry", "Jusqu'au"
3. Look for lab name: Usually at top or in official header
4. Look for director: Usually has "Dr" or "Directeur" prefix
5. If a field not found, use "NOT_FOUND" - DO NOT GUESS

Return ONLY the JSON object, no other text.

Document Text:
{text}"""
}

def get_prompt(entity_type: str) -> str:
    """Get the appropriate prompt for the entity type."""
    return PROMPTS.get(entity_type, PROMPTS["medecin_individuel"])
