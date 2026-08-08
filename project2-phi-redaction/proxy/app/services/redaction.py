"""
Pre-processing / de-identification layer.

This runs BEFORE any text leaves the proxy toward the external LLM.

Regex (email/phone/date) and NLP entity detection (patient names,
locations) built by Rishi - issues #44 (date masking), #61 (phone regex
fix), #48 (address/location detection), #62 (false-positive mitigation),
#68 (department name misclassifications).

Requires: `pip install spacy` and `python -m spacy download en_core_web_sm`
(see requirements.txt).
"""

import logging
import re
import spacy
from vault import create_or_get_token

logger = logging.getLogger(__name__)

_nlp = spacy.load("en_core_web_sm")

MEDICAL_EPONYMS = {"parkinson's", "alzheimer's", "hodgkin's", "cesarean", "asperger's"}

MEDICAL_DEPARTMENTS = {
    "Neurology", "Cardiology", "Pediatrics", "Radiology", 
    "Orthopedics", "Oncology", "Dermatology", "Psychiatry",
    "Gastroenterology", "Endocrinology", "Urology", "Hematology"
}

KNOWN_PLACES = {
    "Lakeview", "Chestnut Drive", "New York", "London", "Paris",
    "Berlin", "Tokyo", "Delhi", "Mumbai", "Brookfield"
}

def mask_structured_pii(text: str) -> str:
    # Fixed Email Masking
    text = re.sub(
        r"[\w.-]+@[\w.-]+\.\w+",
        lambda match: create_or_get_token("EMAIL", match.group(0)),
        text,
    )
    
    # Fixed Phone Pattern Masking (removed erroneous leading v\b)
    phone_pattern = r"(?:\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})"
    text = re.sub(
        phone_pattern,
        lambda match: create_or_get_token("PHONE", match.group(0)),
        text,
    )
    
    # Date Pattern Masking
    text = re.sub(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
        lambda match: create_or_get_token("DATE", match.group(0)),
        text,
    )
    
    # Tightened Hospital/Address Pattern (Uses strict word constraints to prevent swallowing doctor names)
    hospital_address_pattern = r"\b\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|Drive|Road|Avenue|Boulevard|Hospital|Clinic|Medical Center|Healthcare)\b"
    text = re.sub(
        hospital_address_pattern,
        lambda match: create_or_get_token("HOSPITAL_ADDRESS", match.group(0)),
        text,
    )
    
    return text


def mask_person_entities(text: str) -> str:
    doc = _nlp(text)
    final_text = text
    
    # Sort entities by length descending to prevent substring replacement bugs
    sorted_ents = sorted(doc.ents, key=lambda e: len(e.text), reverse=True)
    
    for ent in sorted_ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "FAC"}:
            # Skip medical eponyms
            if ent.text.lower() in MEDICAL_EPONYMS:
                continue
            
            # Skip medical departments to fix issue #68
            if ent.text in MEDICAL_DEPARTMENTS:
                continue
                
            # Generalized check for Issue #62: detect location context from preceding prepositions
            is_location_context = False
            if ent.start > 0:
                prev_token = doc[ent.start - 1].text.lower()
                if prev_token in {"at", "in", "near", "from", "to", "visiting"}:
                    is_location_context = True
                
            if (
                ent.text in KNOWN_PLACES 
                or "Drive" in ent.text 
                or "Hospital" in ent.text 
                or "Clinic" in ent.text
                or ent.label_ in {"GPE", "LOC", "FAC"}
                or is_location_context
            ):
                token = create_or_get_token("LOCATION", ent.text)
                final_text = final_text.replace(ent.text, token)
                continue
                
            if ent.label_ == "PERSON":
                token = create_or_get_token("PERSON", ent.text)
            else:
                token = create_or_get_token("LOCATION", ent.text)
                
            final_text = final_text.replace(ent.text, token)
            
    return final_text


def process_text(raw_text: str) -> str:
    logger.info("process_text called length=%d", len(raw_text))
    step1 = mask_structured_pii(raw_text)
    step2 = mask_person_entities(step1)
    return step2