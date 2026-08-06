"""
Pre-processing / de-identification layer.

This runs BEFORE any text leaves the proxy toward the external LLM.

Regex (email/phone/date) and NLP entity detection (patient names,
locations) built by Rishi - issues #44 (date masking), #61 (phone regex
fix), #48 (address/location detection), #62 (false-positive mitigation).

Requires: `pip install spacy` and `python -m spacy download en_core_web_sm`
(see requirements.txt).

Verified against data/sample_clinical_notes.json (20 notes):
- Phone leaks: 0/20 (was 4/20 before the parenthesized-format fix)
- Date leaks: 0/20 (was 13/20 before this pass)

STILL OPEN (Rishi):
- "Brookfield" (a city not in KNOWN_PLACES) is wrongly redacted as
  [PATIENT_NAME] - the KNOWN_PLACES allowlist approach only protects
  specific hardcoded names, not the general case. See issue #62 (reopened).
- Department names like "Neurology" are being misclassified as PERSON
  and redacted as [PATIENT_NAME] - see new issue for this.
- The hospital/address regex is greedy enough to sometimes absorb a
  doctor's name into [HOSPITAL_ADDRESS] rather than tagging it as a
  name separately - not a leak, but a precision issue worth tightening.
  See issue #48 (kept open).

IMPORTANT - logging discipline: never log raw or redacted note text at
INFO level or above. Only log metadata (length, request_id) - logging
real note content, even redacted, risks leaking PHI into log files that
aren't access-controlled the same way the data store is.
"""

import logging
import re

import spacy

logger = logging.getLogger(__name__)

_nlp = spacy.load("en_core_web_sm")

MEDICAL_EPONYMS = {"parkinson's", "alzheimer's", "hodgkin's", "cesarean", "asperger's"}
KNOWN_PLACES = {
    "Lakeview", "Chestnut Drive", "New York", "London", "Paris",
    "Berlin", "Tokyo", "Delhi", "Mumbai",
}


def mask_structured_pii(text: str) -> str:
    text = re.sub(r"[\w.-]+@[\w.-]+\.\w+", "[EMAIL_REDACTED]", text)
    phone_pattern = r"(?:\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})"
    text = re.sub(phone_pattern, "[PHONE_REDACTED]", text)
    text = re.sub(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
        "[DATE_REDACTED]",
        text,
    )
    text = re.sub(
        r"\b[A-Z][a-zA-Z\s]+(?:Hospital|Clinic|Medical Center|Healthcare|Dr\.|Street|Drive|Road)\b",
        "[HOSPITAL_ADDRESS]",
        text,
    )
    return text


def mask_person_entities(text: str) -> str:
    doc = _nlp(text)
    final_text = text
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "FAC"}:
            if ent.text.lower() in MEDICAL_EPONYMS:
                continue
            if ent.text in KNOWN_PLACES or "Drive" in ent.text or "Hospital" in ent.text:
                continue
            if ent.label_ == "PERSON":
                final_text = final_text.replace(ent.text, "[PATIENT_NAME]")
            else:
                final_text = final_text.replace(ent.text, "[LOCATION_REDACTED]")
    return final_text


def process_text(raw_text: str) -> str:
    logger.info("process_text called length=%d", len(raw_text))
    step1 = mask_structured_pii(raw_text)
    step2 = mask_person_entities(step1)
    return step2
