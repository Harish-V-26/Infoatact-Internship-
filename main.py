from fastapi import FastAPI, Request
import uvicorn
from app.Services.redaction import process_clinical_note

app = FastAPI(title="Medical De-identification Proxy", version="2.2.0")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "de-id proxy active"}

@app.post("/proxy/process")
async def proxy_process(request: Request):
    payload = await request.json()
    text = payload.get("text", "")
    processed_text = process_clinical_note(text)
    
    return {
        "status": "success", 
        "processed_text": processed_text
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)