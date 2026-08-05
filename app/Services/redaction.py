import re
import spacy

nlp = spacy.load("en_core_web_sm")

MEDICAL_EPONYMS = {"parkinson's", "alzheimer's", "hodgkin's", "cesarean", "asperger's"}
KNOWN_PLACES = {"Lakeview", "Chestnut Drive", "New York", "London", "Paris", "Berlin", "Tokyo", "Delhi", "Mumbai"}

def mask_structured_pii(text: str) -> str:
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    phone_pattern = r'(?:\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b|\(\d{3}\)\s*\d{3}[-.\s]?\d{4})'
    text = re.sub(phone_pattern, '[PHONE_REDACTED]', text)
    text = re.sub(r'\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})|(?:\d{4}[-/]\d{1,2}[-/]\d{1,2})\b', '[DATE_REDACTED]', text)
    text = re.sub(r'\b[A-Z][a-zA-Z\s]+(?:Hospital|Clinic|Medical Center|Healthcare|Dr\.|Street|Drive|Road)\b', '[HOSPITAL_ADDRESS]', text)
    return text

def mask_person_entities(text: str) -> str:
    doc = nlp(text)
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

def process_clinical_note(text: str) -> str:
    step1 = mask_structured_pii(text)
    step2 = mask_person_entities(step1)
    return step2
