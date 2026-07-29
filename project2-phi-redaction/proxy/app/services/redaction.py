"""
Pre-processing / de-identification layer.

This runs BEFORE any text leaves the proxy toward the external LLM.

Regex email/phone masking and spaCy PERSON-entity detection (with medical
eponym protection) were built by Rishi (issues #46/#47) and are merged in
here from the standalone prototype at the repo root.

Requires: `pip install spacy` and `python -m spacy download en_core_web_sm`
(see requirements.txt).

STILL OPEN (Jagadesh - issue #44): date format masking. Phone numbers and
emails are handled below, but standard date formats (DOB, visit dates -
e.g. 1985-03-14, 03/14/1985) are not yet caught. Add a regex pass for
dates in mask_structured_pii() below, replacing matches with "[DATE]".

Address detection (issue #48, Rishi) still needs to be added as its own
entity pass - spaCy's default GPE/FAC/LOC labels are a starting point but
need tuning against the synthetic dataset.

IMPORTANT - logging discipline: never log raw or redacted note text at
INFO level or above. Only log metadata (length, request_id, counts of
matches found) - logging real note content, even redacted, risks leaking
PHI into log files that aren't access-controlled the same way the data
store is.
"""

import logging
import re

import spacy

logger = logging.getLogger(__name__)

# Loaded once at import time - reused across requests.
_nlp = spacy.load("en_core_web_sm")

# Conditions/eponyms that must NOT be redacted even though they look like
# person names to a NER model.
MEDICAL_EPONYMS = {
    "parkinson's",
    "alzheimer's",
    "hodgkin's",
    "cesarean",
    "asperger's",
    "crohn's",
    "huntington's",
    "tourette",
}

_EMAIL_RE = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")
_PHONE_RE = re.compile(r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b")


def mask_structured_pii(text: str) -> str:
    """
    Regex pass: emails and phone numbers.

    TODO (Jagadesh - #44): add a date-format regex pass here for DOB /
    visit dates, replacing matches with "[DATE]".
    """
    masked = _EMAIL_RE.sub("[EMAIL_REDACTED]", text)
    masked = _PHONE_RE.sub("[PHONE_REDACTED]", masked)
    return masked


def mask_person_entities(text: str) -> str:
    """
    NLP pass: detects PERSON entities via spaCy and masks them, while
    protecting medical eponyms that look like names (e.g. Parkinson's).
    """
    doc = _nlp(text)
    final_text = text
    for ent in doc.ents:
        if ent.label_ != "PERSON":
            continue
        if ent.text.lower() in MEDICAL_EPONYMS:
            continue
        final_text = final_text.replace(ent.text, "[PATIENT_NAME]")
    return final_text


def process_text(raw_text: str) -> str:
    logger.info("process_text called length=%d", len(raw_text))

    masked = mask_structured_pii(raw_text)
    cleaned_text = mask_person_entities(masked)

    return cleaned_text
