from fastapi import FastAPI, Request
import uvicorn
import re
import spacy

app = FastAPI(title="Medical De-identification Proxy", version="1.0.0")
nlp = spacy.load("en_core_web_sm")

MEDICAL_EPONYMS = {"parkinson's", "alzheimer's", "hodgkin's", "cesarean", "asperger's"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "de-id proxy active"}

@app.post("/proxy/process")
async def proxy_process(request: Request):
    payload = await request.json()
    text = payload.get("text", "")
    
    # 1. Regex masking (Emails & Phone Numbers)
    masked_text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL_REDACTED]', text)
    masked_text = re.sub(r'\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b', '[PHONE_REDACTED]', masked_text)
    
    # 2. NLP entity filtering (Protecting medical eponyms)
    doc = nlp(masked_text)
    final_text = masked_text
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if ent.text.lower() in MEDICAL_EPONYMS:
                continue
            final_text = final_text.replace(ent.text, "[PATIENT_NAME]")
            
    return {"status": "success", "processed_text": final_text}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)