from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from app.Services.redaction import process_clinical_note

app = FastAPI(title="Medical De-identification Proxy", version="2.2.0")

class ClinicalNoteRequest(BaseModel):
    text: str

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "de-id proxy active"}

@app.post("/proxy/process")
async def proxy_process(payload: ClinicalNoteRequest):
    processed_text = process_clinical_note(payload.text)
    return {
        "status": "success", 
        "processed_text": processed_text
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
