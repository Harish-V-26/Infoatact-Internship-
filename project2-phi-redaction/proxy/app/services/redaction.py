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

from vault import create_or_get_token

logger = logging.getLogger(__name__)

_nlp = spacy.load("en_core_web_sm")

MEDICAL_EPONYMS = {"parkinson's", "alzheimer's", "hodgkin's", "cesarean", "asperger's"}
KNOWN_PLACES = {
    "Lakeview", "Chestnut Drive", "New York", "London", "Paris",
    "Berlin", "Tokyo", "Delhi", "Mumbai",
}

# Matches vault tokens like EMAIL_0001, PERSON_0002, HOSPITAL_ADDRESS_0001.
# Used to stop the NLP pass from re-tokenizing text the regex pass already
# tokenized (see issue #72 - a generated token can look like a proper noun
# to spaCy and get wrapped again, corrupting reverse mapping).
_VAULT_TOKEN_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*_\d{4}$")


def mask_structured_pii(text: str) -> str:
    text = re.sub(
        r"[\w.-]+@[\w.-]+\.\w+",
        lambda match: create_or_get_token("EMAIL", match.group(0)),
        text,
    )
    phone_pattern = r"(?:\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})"
    text = re.sub(
        phone_pattern,
        lambda match: create_or_get_token("PHONE", match.group(0)),
        text,
    )
    text = re.sub(
        r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
        lambda match: create_or_get_token("DATE", match.group(0)),
        text,
    )
    text = re.sub(
        r"\b[A-Z][a-zA-Z\s]+(?:Hospital|Clinic|Medical Center|Healthcare|Dr\.|Street|Drive|Road)\b",
        lambda match: create_or_get_token("HOSPITAL_ADDRESS", match.group(0)),
        text,
    )
    return text


def mask_person_entities(text: str) -> str:
    doc = _nlp(text)
    final_text = text
    for ent in doc.ents:
        if ent.label_ in {"PERSON", "GPE", "LOC", "FAC"}:
            if _VAULT_TOKEN_PATTERN.match(ent.text):
                # Already a vault token from the regex pass - don't
                # re-tokenize it, or reverse mapping breaks (#72).
                continue
            if ent.text.lower() in MEDICAL_EPONYMS:
                continue
            if ent.text in KNOWN_PLACES or "Drive" in ent.text or "Hospital" in ent.text:
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
